# 🎥 Warudo + OBS Avatar Overlay Setup Guide

This guide explains how to record or stream your **Warudo VRM avatar** in **OBS Studio** with a transparent background — perfect for overlaying your character on videos, gameplay, or live scenes.

---

## 🧰 Requirements

### Software
| Tool | Purpose | Notes |
|------|----------|-------|
| [Warudo](https://warudo.app) | Loads and animates your VRM model | Any recent version |
| [OBS Studio](https://obsproject.com/) | Captures and streams your avatar | Version 29+ recommended |
| (Optional) [Spout2 Plugin for OBS](https://github.com/Off-World-Live/obs-spout2-plugin) | Enables real-time transparent capture | Required if using Warudo’s Spout output |

---

## ⚙️ Overview

There are **two main methods** to isolate your avatar:

| Method | Description | Difficulty | Quality |
|--------|--------------|-------------|----------|
| 🟩 **Chroma Key (Green Screen)** | Use a solid background color and remove it in OBS | Easy | Good |
| 🪟 **Alpha Transparency (Spout / Game Capture)** | Capture a true transparent output directly | Moderate | Excellent |

---

## 🟩 Option 1: Green Screen (Chroma Key)

### Step 1: Configure Warudo Background
1. Launch **Warudo**.
2. Load your **VRM model**.
3. Open the **Scene** or **Environment** panel.
4. Locate **Background Color** or **Skybox** settings.
5. Set the color to **pure green** (`#00FF00`) or **pure blue** (`#0000FF`).
6. Disable any lighting effects or gradients for a consistent color.

> 💡 Tip: Choose a color that contrasts with your avatar’s outfit or hair.

---

### Step 2: Frame Your Avatar
- Adjust camera position and zoom so your avatar appears exactly as desired.
- Avoid cutting off parts of the model.

---

### Step 3: Capture in OBS
1. Open **OBS Studio**.
2. Add a **Window Capture** source:
   - `Sources → + → Window Capture`
   - Select the **Warudo** window.
3. Right-click the Warudo source → **Transform → Fit to Screen**.

---

### Step 4: Apply the Chroma Key Filter
1. Right-click the **Warudo source** → **Filters**.
2. Under **Effect Filters**, click the **+** and choose **Chroma Key**.
3. In the filter settings:
   - **Key Color Type:** Green (or Blue)
   - **Similarity:** 400–450
   - **Smoothness:** 50–100
   - **Key Color Spill Reduction:** 50–75
4. Adjust the sliders until the background disappears and your avatar remains cleanly visible.

> 🧠 Tip: If you see green edges, increase “Similarity” slightly or add a **Color Correction** filter afterward.

---

### Step 5: Overlay on Your Content
- Add your **gameplay**, **presentation**, or **camera** layer **below** the avatar source.
- Resize and position the avatar wherever you like.

---

## 🪟 Option 2: Transparent Background (Alpha Channel Capture)

This method yields a perfect, crisp overlay with no green screen artifacts.

### Step 1: Enable Transparency in Warudo
1. In **Warudo**, open:
   - `Settings → Video Output` or `Settings → Render`
2. Enable one of the following (depending on version):
   - ✅ **“Transparent Background”**
   - ✅ **“Enable Alpha Channel”**
   - ✅ **“Spout2 Output (With Alpha)”**

If your version of Warudo includes **Spout output**, enable it — this will allow direct transparent streaming to OBS.

---

### Step 2: Add Warudo Capture in OBS

#### Option A: Using Game Capture (Built-in Alpha)
1. In OBS, go to **Sources → + → Game Capture**.
2. Select **Capture Specific Window**.
3. Choose the **Warudo** window.
4. Check the box **Allow Transparency (Alpha Channel)**.
5. Click **OK** — your avatar should appear with a transparent background.

#### Option B: Using Spout2 (if enabled)
1. Install the [OBS Spout2 Plugin](https://github.com/Off-World-Live/obs-spout2-plugin).
2. In OBS, add a new **Spout2 Capture** source.
3. From the dropdown list, select **Warudo** (it will show up automatically when Warudo is running).
4. Toggle **Use Alpha Channel** on.
5. The avatar will now render transparently over your scene.

---

### Step 3: Verify Transparency
- Add a **background source** (like a video, window, or color).
- Move the Warudo source **above** it.
- If transparency is working, your avatar will appear cleanly on top.

---

### Step 4: Fine-Tune Performance
- In Warudo, lower render resolution or disable post-processing for faster output.
- In OBS, set:
  - **FPS** to match Warudo’s framerate.
  - **Output Resolution:** 1080p or 720p depending on stream setup.
- Lock the source transforms once positioned.

---

## 🎨 Visual Example (Conceptual)
