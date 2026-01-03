import numpy as np
import matplotlib.pyplot as plt

# Vectorized Monte Carlo Pi estimator
def estimate_pi_numpy(num_samples):
    # Generate all random points at once
    points = np.random.uniform(-1, 1, size=(num_samples, 2))
    
    # Compute squared distance from origin
    distances_sq = np.sum(points**2, axis=1)
    
    # Count how many points fall inside the unit circle
    inside_circle = np.sum(distances_sq <= 1)
    
    return (inside_circle / num_samples) * 4

# Run simulations with increasing number of samples
def run_simulations(sample_sizes):
    pi_estimates = []
    for size in sample_sizes:
        pi_estimate = estimate_pi_numpy(size)
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
    plt.title('Monte Carlo Estimation of Pi (NumPy Vectorized)')
    plt.legend()
    plt.grid(True)
    plt.show()

# Main execution
sample_sizes = [10, 100, 1000, 10000, 100000, 1000000]
pi_estimates = run_simulations(sample_sizes)
plot_results(sample_sizes, pi_estimates)
