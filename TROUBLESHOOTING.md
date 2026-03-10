# Troubleshooting

## PyTorch on macOS Intel (x86_64)

Recent PyTorch versions do **not** publish wheels for macOS on Intel (x86_64). To avoid install errors, **torch, transformers, and trl are omitted** on that platform when you run `uv sync`. Sync will succeed; training-related notebooks (e.g. Week 7) need PyTorch elsewhere or via Conda.

**If you need training (SFTTrainer, etc.) on this machine:**

1. **Run in the cloud**  
   Use **Google Colab** or **Modal** for Week 7 and other training notebooks (Linux has normal PyTorch wheels).

2. **Use Conda on your Intel Mac**  
   Install PyTorch and training deps with Conda, then use the rest from this project:
   ```bash
   conda create -n llm python=3.12
   conda activate llm
   conda install pytorch transformers
   pip install trl peft datasets bitsandbytes accelerate
   cd /path/to/llm_engineering
   uv sync   # installs the rest (torch/transformers/trl skipped on this platform)
   ```
   Or install the project in the conda env: `pip install -e .` may pull conflicting torch; prefer `uv sync` for non-torch deps and conda for torch/transformers/trl.

3. **Build PyTorch from source**  
   See [PyTorch “from source”](https://github.com/pytorch/pytorch#from-source) (only if you need a recent PyTorch locally on Intel Mac).
