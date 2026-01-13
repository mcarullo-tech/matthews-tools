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
            messagebox.showerror("Error", "Invalid input: r cannot be greater than n and both must be non-negative.")
            return
        result = combinations(n, r)
        result_label.config(text=f"Result: {result}")
    except ValueError:
        messagebox.showerror("Error", "Please enter valid integers for n and r.")

# Create main window
root = tk.Tk()
root.title("Combinations Calculator")

# ✅ Increased HEIGHT instead of width
root.geometry("300x350")  # Width=300, Height=350
root.configure(bg="#f0f8ff")

# Title label
title_label = tk.Label(root, text="C(n, r) Calculator", font=("Arial", 18, "bold"), bg="#f0f8ff", fg="#333")
title_label.pack(pady=15)

# Input fields
frame = tk.Frame(root, bg="#f0f8ff")
frame.pack(pady=10)

tk.Label(frame, text="n:", font=("Arial", 14), bg="#f0f8ff").grid(row=0, column=0, padx=10, pady=5)
entry_n = tk.Entry(frame, width=12, font=("Arial", 14))
entry_n.grid(row=0, column=1, padx=10, pady=5)

tk.Label(frame, text="r:", font=("Arial", 14), bg="#f0f8ff").grid(row=1, column=0, padx=10, pady=5)
entry_r = tk.Entry(frame, width=12, font=("Arial", 14))
entry_r.grid(row=1, column=1, padx=10, pady=5)

# Calculate button
calc_button = tk.Button(root, text="Calculate", font=("Arial", 14), bg="#4CAF50", fg="white", command=calculate)
calc_button.pack(pady=15)

# Result label
result_label = tk.Label(root, text="Result: ", font=("Arial", 16), bg="#f0f8ff", fg="#333")
result_label.pack(pady=20)

# Run the application
root.mainloop()
