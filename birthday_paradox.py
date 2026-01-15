import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Vectorized birthday generator
# -----------------------------
def simulate_birthday_paradox_vectorized(n_people=23, trials=5000):
    """
    Vectorized simulation:
    - Generate all birthdays for all trials at once
    - Shape: (trials, n_people)
    """

    # Generate random months for all trials
    month_idx = np.random.randint(0, 12, size=(trials, n_people))

    # Days per month
    days_in_month = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    # Generate days based on month — vectorized
    days = np.random.randint(1, days_in_month[month_idx] + 1)

    # Encode birthdays as integers (month * 100 + day)
    birthdays = month_idx * 100 + days

    # Check duplicates per row (trial)
    # Trick: sort each row → duplicates become adjacent
    sorted_birthdays = np.sort(birthdays, axis=1)

    # Compare adjacent elements
    duplicates = np.any(sorted_birthdays[:, 1:] == sorted_birthdays[:, :-1], axis=1)

    # Running probability estimate
    running_prob = np.cumsum(duplicates) / np.arange(1, trials + 1)

    return running_prob

# -----------------------------
# Visualization
# -----------------------------
def plot_running_probability(n_people=23, trials=5000):
    running_prob = simulate_birthday_paradox_vectorized(n_people, trials)

    # Theoretical probability
    theoretical = 1 - np.prod([(365 - i) / 365 for i in range(n_people)])

    plt.figure(figsize=(10, 6))
    plt.plot(running_prob, label="Estimated Probability", color="royalblue")
    plt.axhline(theoretical, color="red", linestyle="--", label="Theoretical Probability")

    plt.title(f"Birthday Paradox — Running Probability for {n_people} People")
    plt.xlabel("Number of Trials")
    plt.ylabel("Probability of ≥1 Shared Birthday")
    plt.ylim(0, 1)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

# -----------------------------
# Run the visualization
# -----------------------------
plot_running_probability(n_people=23, trials=5000)
