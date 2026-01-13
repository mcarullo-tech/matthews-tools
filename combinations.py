import math
import tkinter as tk
from tkinter import messagebox

# Function to calculate combinations
def combinations(n, r):
    return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

# Function to handle button click
def calculate():
    try:
        n = int(entry_n.get())
        r = int(entry_r.get())
        if r > n or n < 0 or r < 0:
            messagebox.showerror("Oops!", "❌ r cannot be greater than n and both must be non-negative.")
            return
        result = combinations(n, r)
        result_label.config(text=f"🎉 Result: {result}", fg="#4CAF50", font=("Arial", 18, "bold"))
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integers for n and r.")

# Create main window
root = tk.Tk()
root.title("🎲 Fun Combinations Calculator")

# Make window taller
root.geometry("300x400")
root.configure(bg="#ffe4b5")  # Light orange background

# Center the window on screen
root.eval('tk::PlaceWindow . center')

# Title label with emoji
title_label = tk.Label(root, text="📚 C(n, r) Calculator", font=("Comic Sans MS", 20, "bold"), bg="#ffe4b5", fg="#333")
title_label.pack(pady=20)

# Input fields frame
frame = tk.Frame(root, bg="#ffe4b5")
frame.pack(pady=10)

tk.Label(frame, text="Enter n:", font=("Arial", 14), bg="#ffe4b5").grid(row=0, column=0, padx=10, pady=5)
entry_n = tk.Entry(frame, width=12, font=("Arial", 14))
entry_n.grid(row=0, column=1, padx=10, pady=5)

tk.Label(frame, text="Enter r:", font=("Arial", 14), bg="#ffe4b5").grid(row=1, column=0, padx=10, pady=5)
entry_r = tk.Entry(frame, width=12, font=("Arial", 14))
entry_r.grid(row=1, column=1, padx=10, pady=5)

# Calculate button with fun colors
calc_button = tk.Button(root, text="✨ Calculate ✨", font=("Arial", 14, "bold"), bg="#ff69b4", fg="white", command=calculate)
calc_button.pack(pady=20)

# Result label
result_label = tk.Label(root, text="Result will appear here!", font=("Arial", 16), bg="#ffe4b5", fg="#333")
result_label.pack(pady=30)

# Run the application
root.mainloop()

