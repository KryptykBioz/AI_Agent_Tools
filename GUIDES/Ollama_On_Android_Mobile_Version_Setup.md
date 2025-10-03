# Complete Guide: Running Ollama on Android with Termux

## Overview

This guide will walk you through setting up Ollama on your Android device using Termux. Ollama is a tool that allows you to run large language models (LLMs) locally on your device, giving you privacy and offline access to AI capabilities.

## What You'll Need

### Required Apps
1. **Termux** - A terminal emulator for Android that provides a Linux environment
2. **Storage space** - At least 4-8GB free (depending on model size)
3. **RAM** - Minimum 6GB recommended for smaller models

### Important Notes
- This process works best on devices with 8GB+ RAM
- Larger models require more storage and RAM
- Performance varies based on your device specifications

---

## Step 1: Install Termux

### Download Termux
**Important:** Do NOT install Termux from the Google Play Store (it's outdated and broken).

Download from one of these sources:
- **F-Droid** (recommended): https://f-droid.org/en/packages/com.termux/
- **GitHub Releases**: https://github.com/termux/termux-app/releases

### What is Termux?
Termux is a powerful terminal emulator that provides a Linux environment on Android without requiring root access. It includes a package manager (pkg) that allows you to install Linux tools and applications.

---

## Step 2: Initial Termux Setup

Open Termux and run these commands one by one:

### Update Package Lists
```bash
pkg update && pkg upgrade
```
**What this does:** Updates the list of available packages and upgrades installed packages to their latest versions. Type `y` and press Enter when prompted.

### Grant Storage Access
```bash
termux-setup-storage
```
**What this does:** Requests permission to access your device's storage. A popup will appear - tap "Allow" to grant access.

---

## Step 3: Install Required Dependencies

### Install Essential Tools
```bash
pkg install proot-distro wget curl
```

**What each tool does:**
- **proot-distro**: Allows you to install and run various Linux distributions within Termux
- **wget**: Downloads files from the internet
- **curl**: Transfers data from/to servers (used by Ollama)

---

## Step 4: Install a Linux Distribution

Ollama requires a full Linux environment. We'll use Ubuntu.

### Install Ubuntu
```bash
proot-distro install ubuntu
```
**What this does:** Downloads and installs Ubuntu Linux (about 500MB download).

### Login to Ubuntu
```bash
proot-distro login ubuntu
```
**What this does:** Starts the Ubuntu environment. Your prompt will change to show you're in Ubuntu.

---

## Step 5: Set Up Ubuntu Environment

Run these commands inside the Ubuntu environment:

### Update Ubuntu Packages
```bash
apt update && apt upgrade -y
```

### Install Required Packages
```bash
apt install curl wget -y
```

---

## Step 6: Install Ollama

### Download and Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**What this does:** Downloads and runs the official Ollama installation script. This will:
- Download the Ollama binary
- Set up the necessary directories
- Configure Ollama to run on your system

**Note:** This may take several minutes depending on your internet connection.

---

## Step 7: Start Ollama Server

### Run Ollama in Background
```bash
ollama serve &
```

**What this does:** Starts the Ollama server in the background. The `&` symbol runs it as a background process so you can continue using the terminal.

**Expected output:** You should see messages indicating the server is starting and listening on `http://127.0.0.1:11434`

---

## Step 8: Download and Run a Model

### Pull a Model
Start with a smaller model like Phi-2 or Llama 2 7B:

```bash
ollama pull phi
```

**Other model options:**
- `ollama pull llama2` (7B - requires ~4GB)
- `ollama pull mistral` (7B - requires ~4GB)
- `ollama pull tinyllama` (1.1B - requires ~637MB)

**What this does:** Downloads the selected AI model to your device. This will take time depending on model size and internet speed.

### Run the Model
```bash
ollama run phi
```

**What this does:** Starts an interactive chat session with the model. You can now type questions and get responses!

### Example Usage
```
>>> Hello! Can you help me with Python?
>>> /bye
```

Type `/bye` to exit the chat.

---

## Useful Ollama Commands

### List Downloaded Models
```bash
ollama list
```

### Remove a Model
```bash
ollama rm modelname
```

### Show Model Information
```bash
ollama show modelname
```

### Stop Ollama Server
```bash
pkill ollama
```

---

## Troubleshooting

### Issue: "Command not found"
**Solution:** Make sure you're in the Ubuntu environment (`proot-distro login ubuntu`)

### Issue: Out of Memory
**Solution:** Try smaller models like `tinyllama` or close other apps to free up RAM

### Issue: Ollama server won't start
**Solution:** 
1. Check if it's already running: `ps aux | grep ollama`
2. Kill existing processes: `pkill ollama`
3. Restart: `ollama serve &`

### Issue: Model download fails
**Solution:** 
- Check internet connection
- Try again - downloads can resume
- Clear space on device

---

## Tips for Better Performance

1. **Close background apps** before running models
2. **Use smaller models** on devices with limited RAM
3. **Keep Termux running** - avoid closing it while models are loaded
4. **Acquire a wake lock** in Termux (notification settings) to prevent Android from killing the process

---

## Exiting and Restarting

### To Exit Ubuntu
```bash
exit
```

### To Stop Termux
Simply close the app or type:
```bash
exit
```

### To Restart Everything
1. Open Termux
2. `proot-distro login ubuntu`
3. `ollama serve &`
4. `ollama run modelname`

---

## Model Recommendations by Device RAM

- **4-6GB RAM**: tinyllama, phi (1-3B models)
- **8GB RAM**: llama2, mistral, phi (7B models)
- **12GB+ RAM**: larger variants of popular models

---

## Additional Resources

- Ollama Official Site: https://ollama.com
- Ollama Model Library: https://ollama.com/library
- Termux Wiki: https://wiki.termux.com
- Termux GitHub: https://github.com/termux/termux-app

---

## Security & Privacy Notes

- All models run completely locally on your device
- No data is sent to external servers
- Your conversations are private and stored only on your device
- You can use Ollama offline after downloading models

---

**Congratulations!** You now have Ollama running locally on your Android device. Enjoy exploring AI models with complete privacy and control!