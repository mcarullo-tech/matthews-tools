#!/usr/bin/env python3
# Skull Rave — Music playback + Music-Reactive (mic or Windows loopback)
# Deps: numpy, sounddevice (reactivity), pygame (only if using --music)

import os
import sys
import time
import math
import random
import argparse
import shutil

RESET = "\033[0m"
BOLD = "\033[1m"
INVERT = "\033[7m"
FG = [f"\033[{c}m" for c in range(90, 98)]
BG = [f"\033[{c}m" for c in range(100, 107)]

# Enable ANSI colors on Windows terminals
if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass

def clear():
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()

def get_size():
    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    return cols, rows

BIG_SKULL = [
    r"           .-''''''-.",
    r"         .'  _  _    '.",
    r"        /   (o)(o)     \ ",
    r"       |      __        |",
    r"       |     (__)       |",
    r"       |   .-`__`-.     |",
    r"       |  /  /  \  \    |",
    r"       |  |  \__/ |     |",
    r"       |  \_.____/      |",
    r"        \              /",
    r"         '.__________.'",
]

def colorize(s, fg=None, bg=None, bold=False, invert=False):
    parts = []
    if fg: parts.append(fg)
    if bg: parts.append(bg)
    if bold: parts.append(BOLD)
    if invert: parts.append(INVERT)
    return "".join(parts) + s + RESET

def draw_centered(lines, fg=None, bg=None, bold=False, invert=False, y_offset=0):
    cols, rows = get_size()
    # vertical offset (bob)
    if y_offset > 0:
        print("\n" * min(y_offset, max(0, rows - 1)), end="")
    for line in lines:
        if len(line) > cols:
            line = line[:max(0, cols)]
        else:
            pad = max(0, (cols - len(line)) // 2)
            line = " " * pad + line
        print(colorize(line, fg=fg, bg=bg, bold=bold, invert=invert))

def wall_of_skulls(char="💀", density=0.6, fg=None, bg=None, bold=False, invert=False):
    cols, rows = get_size()
    usable_rows = max(1, rows - 1)
    line_chars = max(1, cols)
    for _ in range(usable_rows):
        row = []
        for _ in range(line_chars):
            row.append(char if random.random() < density else " ")
        print(colorize("".join(row), fg=fg, bg=bg, bold=bold, invert=invert))

def wave_of_skulls(char="☠", amplitude=6, wavelength=12, fg=None, bg=None, bold=False, invert=False, t=0.0):
    cols, rows = get_size()
    usable_rows = max(1, rows - 1)
    base = usable_rows // 2
    canvas = [[" "]*cols for _ in range(usable_rows)]
    for x in range(cols):
        y = int(base + amplitude * math.sin((x / max(1, wavelength)) + t))
        if 0 <= y < usable_rows:
            canvas[y][x] = char
    for r in canvas:
        print(colorize("".join(r), fg=fg, bg=bg, bold=bold, invert=invert))

def banner(text, fg=None, bg=None, bold=True, invert=False):
    cols, _ = get_size()
    pad = max(0, (cols - len(text)) // 2)
    print(colorize(" " * pad + text, fg=fg, bg=bg, bold=bold, invert=invert))

# --- Optional audio playback via pygame ---
def try_start_music(path, volume=0.8):
    if not path:
        return None
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)
        print("[Music] Started OK", file=sys.stderr, flush=True)
        def cleanup():
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception:
                pass
        return cleanup
    except Exception as e:
        print(f"\n[Music] Could not start music ({e}). Install pygame:\n"
              f"    pip install pygame\n"
              f"MP3 can be flaky; WAV/OGG are most reliable.\n", file=sys.stderr, flush=True)
        return None

# --- Music reactivity (mic or Windows loopback) ---
class AudioReactive:
    """
    Captures audio and computes normalized levels (0..1), with bass emphasis (20-200 Hz).
    mode='mic' uses input device (microphone or Stereo Mix).
    mode='loopback' (Windows WASAPI) captures system output even on headphones.
    Adds bass-hit beat detection via spectral flux with adaptive threshold.
    """
    def __init__(self,
                 mode="mic",
                 input_device=None,
                 output_device=None,
                 samplerate=None,
                 blocksize=1024,
                 sensitivity=1.0,
                 # Beat tuning:
                 beat_sensitivity=0.55,   # ratio of flux peak; lower=more sensitive (0.45..0.70 typical)
                 beat_hold_ms=120,        # refractory period to avoid double triggers
                 bass_low=20,             # Hz
                 bass_high=200,           # Hz
                 bass_weight=0.7):        # weight for bass in combined level (0..1)

        self.mode = mode
        self.input_device = input_device
        self.output_device = output_device
        self.blocksize = blocksize
        self.samplerate = samplerate
        self.sensitivity = max(0.1, min(5.0, sensitivity))

        # clamp and store beat/band params
        self._flux_thresh_ratio = float(max(0.2, min(0.9, beat_sensitivity)))
        self._beat_hold = float(max(0.04, min(0.5, beat_hold_ms / 1000.0)))
        l = float(max(10.0, min(200.0, bass_low)))
        h = float(max(l + 10.0, min(400.0, bass_high)))
        self._bass_low = l
        self._bass_high = h
        self._bass_weight = float(max(0.0, min(1.0, bass_weight)))

        self.level = 0.0
        self.bass_level = 0.0
        self.beat = False

        # smooth envs
        self._env = 0.0
        self._peak = 1e-6
        self._bass_env = 0.0
        self._bass_peak = 1e-6

        # beat detection state
        self._prev_bass_mag = None
        self._flux_env = 0.0
        self._flux_peak = 1e-6
        self._last_beat_t = 0.0

        self._lock = None
        self._stream = None

    def start(self):
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError:
            print("[Reactive] Missing deps. Install:\n  pip install numpy sounddevice\n", file=sys.stderr, flush=True)
            return False

        self.np = np
        self.sd = sd
        self._lock = __import__('threading').Lock()

        extra = None
        device = None
        channels = 1

        try:
            if self.mode == "loopback":
                if os.name != "nt" or not hasattr(sd, "WasapiSettings"):
                    print("[Reactive] Loopback requires Windows WASAPI (sounddevice with WasapiSettings).", file=sys.stderr, flush=True)
                    return False
                device = self.output_device
                channels = 2
                extra = sd.WasapiSettings(loopback=True)  # type: ignore
                dev_info = sd.query_devices(device, 'output')
                if self.samplerate is None:
                    self.samplerate = int(dev_info['default_samplerate'])
            else:
                device = self.input_device
                channels = 1
                dev_info = sd.query_devices(device, 'input')
                if self.samplerate is None:
                    self.samplerate = int(dev_info['default_samplerate'])
        except Exception as e:
            print(f"[Reactive] Device query failed: {e}\n"
                  f"List devices with: --list-devices\n", file=sys.stderr, flush=True)
            return False

        def callback(indata, frames, time_info, status):
            if status:
                # you could print status here if needed
                pass

            x = indata
            if x.ndim > 1:
                x = x.mean(axis=1)
            x = x.astype('float32', copy=False)

            # Window + FFT
            w = self.np.hanning(len(x))
            X = self.np.fft.rfft(x * w)
            mag = self.np.abs(X)
            freqs = self.np.fft.rfftfreq(len(x), 1.0 / self.samplerate)  # type: ignore

            # Bass band selection
            bass_mask = (freqs >= self._bass_low) & (freqs <= self._bass_high)
            bass_mag = mag[bass_mask]

            # RMS
            rms = float(self.np.sqrt(self.np.mean(x * x) + 1e-12))
            bass_rms = float(self.np.sqrt(self.np.mean(bass_mag * bass_mag) + 1e-12)) if bass_mag.size else 0.0

            # Envelopes (overall and bass)
            a = 0.20
            self._env = (1 - a) * self._env + a * rms
            self._peak = max(self._peak * 0.995, self._env)
            level = (self._env / max(self._peak, 1e-6)) ** 0.5

            ab = 0.20
            self._bass_env = (1 - ab) * self._bass_env + ab * bass_rms
            self._bass_peak = max(self._bass_peak * 0.995, self._bass_env)
            bass_level = (self._bass_env / max(self._bass_peak, 1e-6)) ** 0.5

            # Combine with bass weighting (PHONK likes bass!)
            combined = ((1.0 - self._bass_weight) * level + self._bass_weight * bass_level) * self.sensitivity
            combined = max(0.0, min(1.0, combined))
            bass_level = max(0.0, min(1.0, bass_level * self.sensitivity))

            # --- Spectral Flux in bass (beat detection) ---
            if self._prev_bass_mag is None or self._prev_bass_mag.shape != bass_mag.shape:
                self._prev_bass_mag = bass_mag.copy()

            flux = float(self.np.sum(self.np.clip(bass_mag - self._prev_bass_mag, 0.0, None)))
            self._prev_bass_mag = bass_mag

            # Adaptive normalization via peak tracker
            fa = 0.15
            self._flux_env = (1 - fa) * self._flux_env + fa * flux
            self._flux_peak = max(self._flux_peak * 0.995, self._flux_env)

            t_now = time.perf_counter()
            beat_candidate = (self._flux_env > self._flux_thresh_ratio * max(self._flux_peak, 1e-6))
            refractory_ok = (t_now - self._last_beat_t) > self._beat_hold
            is_beat = bool(beat_candidate and refractory_ok)
            if is_beat:
                self._last_beat_t = t_now

            # Publish state
            with self._lock:  # type: ignore
                self.level = combined
                self.bass_level = bass_level
                self.beat = is_beat

        try:
            self._stream = self.sd.InputStream(
                device=device,
                channels=2 if self.mode == "loopback" else 1,
                dtype='float32',
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                callback=callback,
                extra_settings=extra
            )
            self._stream.start()
            print(f"[Reactive] Stream started ({self.mode}) @ {self.samplerate} Hz | "
                  f"bass {int(self._bass_low)}-{int(self._bass_high)} Hz | "
                  f"beat_sens={self._flux_thresh_ratio:.2f} hold={self._beat_hold*1000:.0f}ms",
                  file=sys.stderr, flush=True)
            return True
        except Exception as e:
            print(f"[Reactive] Could not start audio stream: {e}\n"
                  f"Tips:\n"
                  f"  • Use --react loopback on Windows and pick your OUTPUT device with --output-device\n"
                  f"  • Or enable 'Stereo Mix' and use --react mic (your device 17)\n"
                  f"  • List devices: --list-devices\n", file=sys.stderr, flush=True)
            return False

    def stop(self):
        try:
            if self._stream:
                self._stream.stop(); self._stream.close()
        except Exception:
            pass

    def get_levels(self):
        if not self._lock:
            return 0.0, 0.0
        with self._lock:
            return self.level, self.bass_level

    def get_state(self):
        """Return (level, bass_level, beat_bool)."""
        if not self._lock:
            return 0.0, 0.0, False
        with self._lock:
            return self.level, self.bass_level, self.beat

def list_devices_and_exit():
    try:
        import sounddevice as sd
        print("\n=== Audio Devices ===")
        devs = sd.query_devices()
        hostapis = sd.query_hostapis()
        for i, d in enumerate(devs):
            ha = hostapis[d['hostapi']]['name']
            print(f"{i:>3}: {d['name']} | hostapi: {ha} | ins: {d['max_input_channels']} outs: {d['max_output_channels']}")
        print("\nUse --input-device <index> for mic, --output-device <index> for loopback.\n"
              "On Windows, pick your HEADPHONES/SPEAKERS device (WASAPI) for loopback.")
    except ImportError:
        print("Install sounddevice to list audio devices:\n    pip install sounddevice")
    sys.exit(0)

def skull_rave(mode="auto", bpm=140, fps=30, density=0.6, strobe=True, use_emoji=True,
               music_path=None, volume=0.8, do_beep=False,
               react=None, react_sensitivity=1.0,
               input_device=None, output_device=None,
               # Beat tuning passthrough:
               beat_sensitivity=0.55, beat_hold_ms=120, bass_low=20, bass_high=200, bass_weight=0.7):
    beat = 60.0 / max(1, bpm)
    frame_time = 1.0 / max(5, fps)
    skull_char = "💀" if use_emoji else "☠"

    music_cleanup = try_start_music(music_path, volume=volume) if music_path else None

    audio = None
    if react in ("mic", "loopback"):
        audio = AudioReactive(mode=react,
                              input_device=input_device,
                              output_device=output_device,
                              sensitivity=react_sensitivity,
                              beat_sensitivity=beat_sensitivity,
                              beat_hold_ms=beat_hold_ms,
                              bass_low=bass_low,
                              bass_high=bass_high,
                              bass_weight=bass_weight)
        if not audio.start():
            audio = None

    t0 = time.perf_counter()
    fg = random.choice(FG)

    try:
        while True:
            t = time.perf_counter() - t0
            phase = (t % beat) / beat if beat > 0 else 0.0

            # Read current state
            beat_now = False
            if audio:
                level, bass, beat_now = audio.get_state()
            else:
                level, bass = (0.0, 0.0)

            # Map audio level -> visuals, with beat spikes
            level_clamped = max(0.0, min(1.0, level))
            if audio:
                density_eff = density * (0.45 + 0.9 * level_clamped)
                amp_eff = 6 + int(8 * level_clamped)
                if beat_now:
                    density_eff *= 1.25
                    amp_eff += 2
                density_eff = max(0.05, min(1.0, density_eff))
                amp_eff = min(18, max(4, amp_eff))
            else:
                density_eff = density
                amp_eff = 6

            # Beat-driven visuals: color flip + strobe on hits
            bg = None
            invert = False
            if beat_now:
                fg = random.choice(FG)
                if strobe:
                    invert = True
                    if random.random() < 0.50:
                        bg = random.choice(BG)
                # Optional short beep if desired and no music
                if do_beep and not music_path:
                    if os.name == "nt":
                        try:
                            import winsound
                            winsound.Beep(880, 40)
                        except Exception:
                            pass
                    else:
                        sys.stdout.write("\a"); sys.stdout.flush()
            else:
                invert = strobe and (level_clamped > 0.92)

            clear()
            title = "🔥💀 SKULL RAVE (Reactive) 💀🔥" if audio else "🔥💀 SKULL RAVE MODE + MUSIC 💀🔥"
            banner(title, fg=fg, bold=True, invert=False)

            # Scene selection (auto cycles, but allow beat to occasionally flip it)
            if mode == "auto":
                cycle = t % 3.2
                scene = "wall" if cycle < 1.0 else ("wave" if cycle < 2.0 else "center")
                if beat_now and random.random() < 0.10:
                    scene = random.choice(["wall", "wave", "center"])
            else:
                scene = mode

            # Render
            if scene == "wall":
                wall_of_skulls(char=skull_char, density=density_eff, fg=fg, bg=bg, bold=True, invert=invert)
            elif scene == "wave":
                wave_of_skulls(char=skull_char, amplitude=amp_eff, wavelength=12, fg=fg, bg=bg, bold=True, invert=invert, t=t*3.0)
            else:
                y_bob = int((1 + 3 * level_clamped) * math.sin(phase * 2 * math.pi)) if audio else 0
                do_invert = invert or (strobe and (phase < 0.10 or level_clamped > 0.85))
                draw_centered(BIG_SKULL, fg=fg, bg=bg, bold=True, invert=do_invert, y_offset=max(0, y_bob))

            footer = "Ctrl+C to exit • --react loopback or --react mic • --sensitivity 0.5..2.0 • --music <file>"
            banner(footer, fg=fg, bold=False, invert=False)

            time.sleep(frame_time)

    except KeyboardInterrupt:
        clear()
        print(colorize("Thanks for raging in SKULL RAVE MODE. Stay based. ✨", fg="\033[92m", bold=True))
    finally:
        if music_cleanup:
            music_cleanup()
        if audio:
            audio.stop()

def parse_args():
    p = argparse.ArgumentParser(description="Skull Rave — terminal animation with optional music & reactive modes")
    p.add_argument("--mode", choices=["auto","wall","wave","center"], default="auto", help="Scene (default: auto)")
    p.add_argument("--bpm", type=int, default=140, help="Fallback beat BPM (default: 140)")
    p.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    p.add_argument("--density", type=float, default=0.6, help="Base density in wall mode 0..1")
    p.add_argument("--no-strobe", action="store_true", help="Disable strobe/invert effects")
    p.add_argument("--ascii", action="store_true", help="Use ASCII ☠ instead of emoji 💀")
    p.add_argument("--music", type=str, default=None, help="Audio file to loop (WAV/OGG/MP3) — requires pygame")
    p.add_argument("--volume", type=float, default=0.8, help="Music volume 0..1")
    p.add_argument("--beep", action="store_true", help="Beat beeps if not using --music")

    # Reactive options
    p.add_argument("--react", choices=["mic", "loopback"], default=None,
                   help="Audio-reactive mode: 'mic' (microphone/Stereo Mix) or 'loopback' (Windows system output)")
    p.add_argument("--sensitivity", type=float, default=1.0, help="Reactive sensitivity multiplier (0.5..2.0)")
    p.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    p.add_argument("--input-device", type=int, default=None, help="Input device index for mic")
    p.add_argument("--output-device", type=int, default=None, help="Output device index for loopback")

    # Beat tuning (new)
    p.add_argument("--beat-sensitivity", type=float, default=0.55,
                   help="Beat trigger ratio vs recent flux peak (lower = more triggers). Typical 0.45..0.70")
    p.add_argument("--beat-hold-ms", type=int, default=120,
                   help="Refractory period in ms between beats (prevents double triggers). Typical 100..160")
    p.add_argument("--bass-low", type=int, default=20, help="Bass band low Hz for beat detection (e.g., 30)")
    p.add_argument("--bass-high", type=int, default=200, help="Bass band high Hz for beat detection (e.g., 130)")
    p.add_argument("--bass-weight", type=float, default=0.7, help="Weight for bass in level mix (0..1), higher = more bass influence")
    return p.parse_args()

ARGS = parse_args()

if __name__ == "__main__":
    if ARGS.list_devices:
        list_devices_and_exit()

    skull_rave(
        mode=ARGS.mode,
        bpm=ARGS.bpm,
        fps=ARGS.fps,
        density=max(0.0, min(1.0, ARGS.density)),
        strobe=not ARGS.no_strobe,
        use_emoji=not ARGS.ascii,
        music_path=ARGS.music,
        volume=max(0.0, min(1.0, ARGS.volume)),
        do_beep=ARGS.beep,
        react=ARGS.react,
        react_sensitivity=ARGS.sensitivity,
        input_device=ARGS.input_device,
        output_device=ARGS.output_device,
        beat_sensitivity=ARGS.beat_sensitivity,
        beat_hold_ms=ARGS.beat_hold_ms,
        bass_low=ARGS.bass_low,
        bass_high=ARGS.bass_high,
        bass_weight=ARGS.bass_weight
    )