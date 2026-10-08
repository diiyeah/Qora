import math

def hellinger_fidelity(dist_p: dict[str, int], dist_q: dict[str, int], shots: int) -> float:
    """
    Calculate the Hellinger fidelity between two probability distributions.
    dist_p: The ideal distribution (counts).
    dist_q: The noisy distribution (counts).
    shots: Total number of shots.
    """
    # Convert counts to probabilities
    prob_p = {state: count / shots for state, count in dist_p.items()}
    prob_q = {state: count / shots for state, count in dist_q.items()}
    
    # Get all unique states observed in both distributions
    all_states = set(prob_p.keys()).union(set(prob_q.keys()))
    
    # Calculate Hellinger distance squared
    h_dist_sq = 0.0
    for state in all_states:
        p_i = prob_p.get(state, 0.0)
        q_i = prob_q.get(state, 0.0)
        h_dist_sq += (math.sqrt(p_i) - math.sqrt(q_i)) ** 2
        
    h_dist_sq = (1.0 / math.sqrt(2)) * math.sqrt(h_dist_sq)
    
    # Hellinger Fidelity is (1 - H^2)^2
    fidelity = (1 - h_dist_sq**2)**2
    
    return float(fidelity)

def evaluate_noise_sensitivity(ideal_counts: dict, noisy_counts: dict, shots: int) -> dict:
    """Calculate the noise sensitivity score for the analyzer endpoint."""
    fidelity = hellinger_fidelity(ideal_counts, noisy_counts, shots)
    
    # Lower fidelity means higher sensitivity to noise
    sensitivity_score = 1.0 - fidelity
    
    return {
        "hellinger_fidelity": round(fidelity, 4),
        "noise_sensitivity": round(sensitivity_score, 4),
        "assessment": "High" if sensitivity_score > 0.3 else "Moderate" if sensitivity_score > 0.1 else "Low"
    }
