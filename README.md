# France Radio Transcription Project

This project uses Python 3.11, Whisper, and related packages to transcribe French radio streams.

---

## Requirements

- Windows 10 or 11
- Python 3.11.x installed
- PowerShell or Command Prompt
- Optional: long paths enabled for deep folder structures

---

## 1. Python Installation

1. Download **Python 3.11 Windows installer (64-bit)** from [python.org](https://www.python.org/downloads/windows/).  
2. Run the installer:
   - Check **Add Python to PATH**
   - Ensure **pip** is selected
   - Virtual environment support (`venv`) is included by default
   - Optional: "Disable MaxPath limit" to enable long paths (recommended for deep folders)
3. Verify installation:

```powershell
py -3.11 --version
```

Expected output:

```
Python 3.11.x
```

---

## 2. Enable Long Paths (if needed)

Check current value:

```powershell
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled
```

- `0` = disabled
- `1` = enabled

Enable long paths (requires Administrator PowerShell):

```powershell
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled -Value 1
```

Verify:

```powershell
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name LongPathsEnabled
```

**Why this matters:** Long paths are recommended if your project folder has a deep directory structure (like `D:\Shared Downloads\Study in France\French Media\FranceInfo fr\Simple Subtitles`). Without this, Python and pip may fail when installing packages with nested dependencies.

---

## 3. Create and Activate Virtual Environment

In your project folder:

```powershell
cd "D:\Shared Downloads\Study in France\French Media\FranceInfo fr\Simple Subtitles"
py -3.11 -m venv venv
```

**What this does:**
- Creates a virtual environment in `./venv`
- Isolated from system Python
- Packages installed here do not affect Python 3.12 or other versions

### Activating the venv

```powershell
.\venv\Scripts\Activate.ps1
```

**What this script does:**

1. **Modifies your PATH**
   - `python` now points to `venv\Scripts\python.exe`
   - `pip` now points to the venv's pip

2. **Sets the VIRTUAL_ENV environment variable**
   - Tells Python and other tools which folder is the active virtual environment

3. **Changes your shell prompt**
   - Adds `(venv)` to remind you the environment is active

**While active**, all `python` and `pip` commands use the venv only, leaving your system Python untouched.

**Important:** If you close PowerShell, you must activate again for new sessions.

### Alternative: Run Python directly without activating

```powershell
.\venv\Scripts\python.exe france_radio.py
```

This works without activation and still uses the venv's packages.

---

## 4. Install Dependencies

Once the venv is active (you'll see `(venv)` in your prompt):

```powershell
python -m pip install --upgrade pip
python -m pip install openai-whisper torch transformers pydub requests sentencepiece
```

**What happens:**
- Packages are installed inside `venv\Lib\site-packages`
- Fully isolated from system Python
- No conflicts with other Python versions

---

## 5. Running the Script

With the venv active:

```powershell
python france_radio.py
```

Python uses the packages in the venv.

**If you close the terminal:** Re-activate the venv next time before running your script.

---

## Notes

### Virtual Environment (venv)

- **Location:** Stored in `./venv` inside project folder
- **Isolation:** Completely separate from system Python
- **Packages:** All installed packages live in `venv\Lib\site-packages`

### Activation

- **Required:** Each new shell session needs activation to ensure Python/pip point to venv
- **Optional:** Call `.\venv\Scripts\python.exe` directly without activating

### Long Paths

- **Purpose:** Helps with deeply nested folders
- **Registry key:** `HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled`
- **Default:** Windows sets this to `0` (disabled) for backward compatibility
- **Requirement:** Windows 10/11 or later

### Future Maintenance

- **Remove venv:** Delete `venv` folder and start fresh
- **Update packages:** Activate venv, then `pip install --upgrade <package>`
- **Check installed packages:** `pip list` (with venv active)

---

## One-Shot Setup (Copy-Paste)

For a fresh setup, run these commands in sequence:

```powershell
# Navigate to project folder
cd "D:\Shared Downloads\Study in France\French Media\FranceInfo fr\Simple Subtitles"

# Create virtual environment
py -3.11 -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
python -m pip install openai-whisper torch transformers pydub requests

# Verify installation
python -c "import whisper; print('Whisper installed successfully!')"
```

---

## Troubleshooting

### "Activate.ps1 cannot be loaded because running scripts is disabled"

Run this in Administrator PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Python not found" after installation

- Open a **new** PowerShell window (PATH updates only affect new sessions)
- Verify with: `py -3.11 --version`

### "Path too long" errors during pip install

- Enable long paths (see Section 2)
- Requires Windows 10/11

### Packages not found when running script

- Make sure venv is activated (you should see `(venv)` in prompt)
- Or use: `.\venv\Scripts\python.exe france_radio.py`

---

## Why Python 3.11 (not 3.12)?

Python 3.12 has dependency conflicts with some packages used in this project:
- NumPy/Numba compatibility issues
- Whisper may not work correctly

Python 3.11 provides a stable, tested environment for this transcription workflow.

---

**Last updated:** February 2026
