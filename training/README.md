# P.R.I.S.M. Training Components

This directory contains all training-related components for the P.R.I.S.M. project.

## Training Agent

The `training_agent.py` script provides a specialized interface for managing all training components:

- **Data Generation**: Automated creation of synthetic training datasets
- **Fine-tuning Management**: Execution of Jupyter notebooks for model fine-tuning
- **Dataset Analysis**: Quality control and metrics for training data
- **Model Evaluation**: Testing and validation of trained models

## Directory Structure

```
training/
├── P_R_I_S_M_Finetune_One.ipynb     # Primary fine-tuning notebook
├── P_R_I_S_M_Finetune_Two.ipynb     # Secondary fine-tuning notebook
├── p-r-i-s-m-eval.ipynb             # Evaluation notebook
├── training_agent.py              # Main training agent script
├── data/                           # Data generation and augmentation scripts
│   ├── CLAUDE_PROMPT.md           # Prompt for dataset generation
│   ├── generate_samples.py         # Sample generation script
│   ├── augment_dataset.py         # Dataset augmentation script
│   ├── augment_dataset_fixed.py    # Fixed dataset augmentation script
│   ├── analyze_dataset.py        # Dataset analysis script
│   └── deliberation_dataset*.json # Training datasets
└── README.md                       # This file
```

## Key Components

### Fine-tuning Notebooks

1. **P_R_I_S_M_Finetune_One.ipynb** - Primary fine-tuning implementation with Unsloth optimization
2. **P_R_I_S_M_Finetune_Two.ipynb** - Advanced fine-tuning with clean stack approach
3. **p-r-i-s-m-eval.ipynb** - Model evaluation and testing

### Data Generation Scripts

- `generate_samples.py` - Creates synthetic training data based on clinical scenarios
- `augment_dataset.py` - Augments existing datasets with additional examples
- `analyze_dataset.py` - Analyzes dataset quality and structure

### Datasets

- `deliberation_dataset.json` - Main training dataset
- `deliberation_dataset_clean.json` - Cleaned version of training data
- `deliberation_dataset_augmented.json` - Augmented training data
- `safe_combinations_augmented.json` - Safe drug combination data for balanced training

## Usage

To use the training agent:

```bash
python training_agent.py
```

The agent will:
1. List all available training components
2. Show current training status
3. Provide interfaces for data generation and fine-tuning execution
```