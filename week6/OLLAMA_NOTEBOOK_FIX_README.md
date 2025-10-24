# Ollama Fine-Tuning Notebook - Installation Fix

## Problem Summary

The Unsloth installation was failing with:
```
❌ Installation failed: Command '[...python3', '-m', 'pip', 'install', '-q', 'xformers']' returned non-zero exit status 1.
```

## Root Causes

1. **xformers compilation issue**: `xformers` requires CUDA and specific compilation tools that may not be available on all systems (especially macOS)
2. **bitsandbytes compatibility**: `bitsandbytes` typically only works on Linux with NVIDIA GPUs, not on macOS
3. **Rigid installation**: Previous installation script required all packages to succeed, causing failure if any optional package couldn't install

## Solutions Implemented

### 1. Updated Installation Cell (Cell 17)

**Key Changes**:
- Made `xformers` optional (not required for basic functionality)
- Made `bitsandbytes` optional with graceful fallback
- Added detailed error handling with informative messages
- Installation continues even if optional packages fail

**New Installation Flow**:
```
Step 1/5: Install transformers==4.56.2 (REQUIRED)
Step 2/5: Try xformers (OPTIONAL - continues if fails)
Step 3/5: Install core libraries: trl, peft, accelerate, datasets (REQUIRED)
Step 4/5: Try bitsandbytes (OPTIONAL - needed for 4-bit quantization)
Step 5/5: Install Unsloth from git (REQUIRED)
Step 6/5: Verify installation
```

### 2. Updated Model Configuration Cell (Cell 18)

**Key Changes**:
- Automatically detects if `bitsandbytes` is available
- Falls back to full-precision model if 4-bit quantization isn't available
- Provides clear feedback about what's being used

**Logic**:
```python
# Auto-detect bitsandbytes availability
try:
    import bitsandbytes
    load_in_4bit = True
    model_name = "unsloth/gpt-oss-20b-unsloth-bnb-4bit"
except ImportError:
    load_in_4bit = False
    model_name = "unsloth/llama-3-8b"  # Smaller full-precision model
```

## What You Should See Now

When you run the updated **Cell 17** (installation cell), you should see:

✅ **Success Case** (Linux with NVIDIA GPU):
```
Step 1/5: Installing transformers...
Step 2/5: Installing xformers (optional)...
Step 3/5: Installing core libraries...
Step 4/5: Installing bitsandbytes...
Step 5/5: Installing Unsloth...
Step 6/5: Verifying installation...

✅ Installation successful!
✅ Unsloth installed and ready to use
```

✅ **Success Case** (macOS or systems without CUDA):
```
Step 1/5: Installing transformers...
Step 2/5: Installing xformers (optional)...
⚠️  Optional package xformers failed to install (this is OK)
Step 3/5: Installing core libraries...
Step 4/5: Installing bitsandbytes...
⚠️  Optional package bitsandbytes failed to install (this is OK)
ℹ️  bitsandbytes not installed - 4-bit quantization will not be available
Step 5/5: Installing Unsloth...
Step 6/5: Verifying installation...

✅ Installation successful!
✅ Unsloth installed and ready to use
```

When you run **Cell 18** (configuration cell):

**If bitsandbytes is available**:
```
✅ bitsandbytes available - 4-bit quantization enabled

Model: unsloth/gpt-oss-20b-unsloth-bnb-4bit
Max sequence length: 1024
4-bit quantization: True
```

**If bitsandbytes is NOT available**:
```
⚠️  bitsandbytes not available - using full precision (requires more memory)
ℹ️  Using full precision model - consider using a machine with GPU + bitsandbytes for larger models

Model: unsloth/llama-3-8b
Max sequence length: 1024
4-bit quantization: False
```

## Updated File

**File**: `/Users/Gen_AI_Projects/llm_engineering/week6/dz_day5.ipynb`

**Status**: ✅ Ready to run

## Next Steps

1. **Run Cell 17** (Installation cell)
   - This should now complete successfully
   - It will install Unsloth and all required dependencies
   - Optional packages (xformers, bitsandbytes) will be skipped if they fail

2. **Run Cell 18** (Configuration cell)
   - This will detect your system capabilities
   - Automatically select the appropriate model

3. **Verify with Cell 19**:
   ```python
   !pip show unsloth
   ```
   - Should show Unsloth package information

4. **Continue with the rest of the notebook**
   - All subsequent cells should work normally

## System Compatibility

### Full Functionality (Linux + NVIDIA GPU):
- ✅ All packages install
- ✅ 4-bit quantization available
- ✅ Can use large models (20B parameters)
- ✅ xformers acceleration available

### Limited Functionality (macOS / No CUDA):
- ✅ Core Unsloth functionality works
- ⚠️  No 4-bit quantization (uses more memory)
- ⚠️  Must use smaller models (8B parameters recommended)
- ⚠️  No xformers acceleration

## Troubleshooting

### If installation still fails:

1. **Check Python version**: Unsloth requires Python 3.8+
   ```bash
   python3 --version
   ```

2. **Try manual installation**:
   ```bash
   pip install transformers==4.56.2
   pip install trl peft accelerate datasets
   pip install unsloth @ git+https://github.com/unslothai/unsloth.git
   ```

3. **Check virtual environment**: Make sure you're in the correct venv
   ```bash
   which python3
   ```

4. **Update pip**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

### If you get memory errors during training:

1. Reduce the number of training examples:
   ```python
   fine_tune_train = train[:100]  # Instead of 200
   fine_tune_validation = train[100:125]  # Instead of 200:250
   ```

2. Use a smaller model:
   ```python
   model_name = "unsloth/llama-3-8b"  # Instead of 20B model
   ```

3. Reduce batch size in training arguments (Cell 24):
   ```python
   per_device_train_batch_size = 1  # Instead of 2
   ```

## Key Differences from day5.ipynb (OpenAI Version)

| Feature | day5.ipynb (OpenAI) | dz_day5.ipynb (Ollama) |
|---------|---------------------|------------------------|
| **Infrastructure** | Cloud API | Local GPU |
| **Cost** | Pay per token | Free (local) |
| **Model Size** | 8B parameters | 8B-20B parameters |
| **Installation** | API key only | Requires dependencies |
| **Fine-tuning Time** | ~5-10 minutes | ~15-30 minutes |
| **Export Format** | API model ID | GGUF for Ollama |
| **Quantization** | Managed by OpenAI | Optional 4-bit with bitsandbytes |

## Benefits of This Approach

1. **Graceful Degradation**: Works on systems with or without GPU acceleration
2. **Clear Feedback**: User knows exactly what's installed and what features are available
3. **No Unnecessary Failures**: Optional packages don't block core functionality
4. **Automatic Adaptation**: Configuration automatically adjusts to system capabilities
5. **Educational**: User learns which components are essential vs optional

## Files Modified

- ✅ `/Users/Gen_AI_Projects/llm_engineering/week6/dz_day5.ipynb` - Updated with robust installation

## Date

2025-10-13

---

**Status**: ✅ READY TO USE - Installation and configuration cells updated with robust error handling
