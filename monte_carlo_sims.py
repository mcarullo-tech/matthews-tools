import numpy as np
import matplotlib.pyplot as plt
import random

# Estimate the value of pi using Monte Carlo simulation
def estimate_pi(num_samples):
    inside_circle = 0
    for _ in range(num_samples):
        x, y = random.uniform(-1, 1), random.uniform(-1, 1)
        if x**2 + y**2 <= 1:
            inside_circle += 1
    return (inside_circle / num_samples) * 4

# Run simulations with increasing number of samples
def run_simulations(sample_sizes):
    pi_estimates = []
    for size in sample_sizes:
        pi_estimate = estimate_pi(size)
        pi_estimates.append(pi_estimate)
        print(f"Samples: {size}, Estimated Pi: {pi_estimate}")
    return pi_estimates

# Plot the results
def plot_results(sample_sizes, pi_estimates):
    plt.figure(figsize=(10, 6))
    plt.plot(sample_sizes, pi_estimates, marker='o', label='Estimated Pi')
    plt.axhline(y=np.pi, color='r', linestyle='--', label='Actual Pi')
    plt.xscale('log')
    plt.xlabel('Number of Samples (log scale)')
    plt.ylabel('Estimated Value of Pi')
    plt.title('Monte Carlo Estimation of Pi')
    plt.legend()
    plt.grid(True)
    plt.show()

# Main execution
sample_sizes = [10, 100, 1000, 10000, 100000, 1000000]
pi_estimates = run_simulations(sample_sizes)
plot_results(sample_sizes, pi_estimates)