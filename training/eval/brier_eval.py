"""
P.R.I.S.M. Brier Score Evaluation
Measures the mean squared difference between predicted probabilities and actual outcomes.
"""
import torch
import torch.nn.functional as F

def brier_score(logits, labels):
    probs = F.softmax(logits, dim=1)
    # One-hot encode labels
    labels_one_hot = F.one_hot(labels, num_classes=logits.size(1)).float()
    
    score = torch.mean(torch.sum((probs - labels_one_hot) ** 2, dim=1))
    return score.item()

if __name__ == "__main__":
    dummy_logits = torch.randn(100, 2)
    dummy_labels = torch.randint(0, 2, (100,))
    print(f"Dummy Brier Score: {brier_score(dummy_logits, dummy_labels):.4f}")
