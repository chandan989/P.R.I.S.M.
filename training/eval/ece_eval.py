"""
P.R.I.S.M. Expected Calibration Error (ECE)
Evaluates confidence calibration by dividing predictions into bins and measuring the gap 
between average confidence and accuracy.
"""
import torch
import torch.nn.functional as F

def expected_calibration_error(logits, labels, n_bins=10):
    probs = F.softmax(logits, dim=1)
    confidences, predictions = torch.max(probs, 1)
    accuracies = predictions.eq(labels)
    
    ece = torch.zeros(1, device=logits.device)
    bin_boundaries = torch.linspace(0, 1, n_bins + 1)
    
    for bin_lower, bin_upper in zip(bin_boundaries[:-1], bin_boundaries[1:]):
        in_bin = confidences.gt(bin_lower.item()) * confidences.le(bin_upper.item())
        prop_in_bin = in_bin.float().mean()
        if prop_in_bin.item() > 0:
            accuracy_in_bin = accuracies[in_bin].float().mean()
            avg_confidence_in_bin = confidences[in_bin].mean()
            ece += torch.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
            
    return ece.item()

if __name__ == "__main__":
    dummy_logits = torch.randn(100, 2)
    dummy_labels = torch.randint(0, 2, (100,))
    print(f"Dummy ECE Score: {expected_calibration_error(dummy_logits, dummy_labels, 10):.4f}")
