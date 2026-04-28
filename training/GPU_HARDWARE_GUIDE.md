# P.R.I.S.M. GPU Hardware Selection Guide

Based on the explicit pricing and architecture available on Google Colab:

| Instance | GPU Architecture | VRAM | Hourly Cost | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **G4** | Blackwell | 96GB | $8.57 | **Primary Choice (Fastest)** |
| **H100** | Hopper | 80GB | $8.57 | Avoid (G4 is the same price but better) |
| **A100** | Ampere | 40GB | $5.57 | **Budget Choice (Safest Baseline)** |

## Analysis for Gemma 4 26B MoE Fine-Tuning

### The 16GB Baseline Constraint
The P.R.I.S.M. architecture strictly optimizes for a **16GB VRAM** local deployment constraint using Unsloth's 4-bit quantization and LoRA. Therefore, *any* of these three GPUs (40GB, 80GB, or 96GB) has significantly more than enough memory to handle the fine-tuning script (`training/finetune.py`) perfectly without crashing.

### The Decision: Time vs. Cost

**Option 1: The G4 Blackwell ($8.57/hr) - The Speed Winner**
*   **Why choose it:** At 96GB of VRAM and featuring next-generation Blackwell Tensor Cores, this GPU will chew through the 60 steps of the SFT trainer blazingly fast. Because the H100 costs exactly the same amount ($8.57), the H100 should be ignored entirely in favor of the newer, larger G4.
*   **The Catch:** It is $3.00/hr more expensive than the A100. However, because it trains significantly faster, the *total* cost of the training run might actually be lower or roughly equal to the A100 run.

**Option 2: The A100 40GB ($5.57/hr) - The Budget Winner**
*   **Why choose it:** It is $3.00 cheaper per hour. 40GB of VRAM is still 2.5x more memory than you actually need for this heavily quantized Unsloth run. It natively supports the `bfloat16` precision required by the script.
*   **The Catch:** The Ampere architecture is two generations older than Blackwell. The training loop will take longer to complete.

### Final Verdict
If you want the **fastest possible completion time**, spin up the **G4 Blackwell ($8.57)**. It makes the H100 completely obsolete at that price point.
If you are strictly optimizing for **lowest hourly burn rate** and don't mind the training loop taking a bit longer, the **A100 ($5.57)** is perfectly capable and safe.