# Troubleshooting Guide

## ChromaDB / onnxruntime DLL Error on Windows

### Issue
When starting the application, you may encounter:
```
ImportError: DLL load failed while importing onnxruntime_pybind11_state: A dynamic link library (DLL) initialization routine failed.
```

### Root Cause
ChromaDB tries to load its default embedding function (which uses onnxruntime) at import time, even though we're using Google Gemini for embeddings. The onnxruntime package requires Microsoft Visual C++ Redistributable to be installed on Windows.

### Solutions

#### Option 1: Install Microsoft Visual C++ Redistributable (Recommended)
1. Download and install the latest [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
2. Restart your terminal/IDE
3. Run the application again

#### Option 2: Reinstall onnxruntime
```bash
pip uninstall onnxruntime
pip install onnxruntime
```

#### Option 3: Use a different Python environment
If you're using the Windows Store version of Python, try using:
- Python from python.org
- Anaconda/Miniconda
- Python from a virtual environment

### Verification
Test if ChromaDB can be imported:
```bash
python -c "import chromadb; print('Success!')"
```

If this works, the application should start successfully.
