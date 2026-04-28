"""
P.R.I.S.M. Temperature Scaling Layer
Post-hoc logprob calibration - trains a single learned scalar to optimize Brier/ECE metrics.
"""
import torch
import torch.nn as nn
from torch.optim import LBFGS

class TemperatureScaler(nn.Module):
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits):
        return logits / self.temperature

def calibrate(logits, labels):
    """
    Learns the optimal temperature scalar using LBFGS.
    logits: Unscaled logprobs from the model (N, C)
    labels: True class labels (N)
    """
    scaler = TemperatureScaler()
    nll_criterion = nn.CrossEntropyLoss()
    
    optimizer = LBFGS([scaler.temperature], lr=0.01, max_iter=50)

    def eval():
        optimizer.zero_grad()
        loss = nll_criterion(scaler(logits), labels)
        loss.backward()
        return loss

    optimizer.step(eval)
    print(f"Calibrated Temperature: {scaler.temperature.item():.4f}")
    return scaler.temperature.item()

if __name__ == "__main__":
    print("Testing Temperature Scaling with dummy logits...")
    dummy_logits = torch.randn(1000, 2) * 5
    dummy_labels = torch.randint(0, 2, (1000,))
    optimal_t = calibrate(dummy_logits, dummy_labels)
    
    with open("adapters/temperature.txt", "w") as f:
        f.write(str(optimal_t))
    print("Saved optimal temperature scalar to adapters/temperature.txt")
