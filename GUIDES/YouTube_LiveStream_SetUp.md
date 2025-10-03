# Complete OBS + YouTube Livestream Setup Guide

## Prerequisites

### Software Installation
1. **Download OBS Studio**: https://obsproject.com/download
2. **Install OBS**: Run installer with default settings
3. **Verify YouTube Account**: Ensure your account has streaming enabled

### YouTube Requirements
- Verified phone number on your Google account
- No live streaming restrictions (24-hour waiting period for first-time streamers)
- Channel must have no Community Guidelines strikes

---

## Part 1: YouTube Studio Setup

### Step 1: Create Your Stream
1. Go to **YouTube Studio** (studio.youtube.com)
2. Click **Create** button (top right) → **Go Live**
3. Choose **Stream** option (not "Webcam" or "Manage")

### Step 2: Configure Stream Settings
```
Stream Title: "AI VTuber Test Stream - Private Testing"
Description: (optional) "Testing AI chat integration - Private stream"
Category: Gaming (or your preference)
```

### Step 3: Set Privacy to Unlisted
1. Under **Visibility** section
2. Select **Unlisted**
3. This ensures only people with the link can access

### Step 4: Additional Settings
```
Age Restriction: No (unless needed)
Enable Live Chat: ✓ YES (critical for your AI)
Enable DVR: ✓ (optional - allows viewers to pause)
Latency: Normal or Low (Low is better for chat interaction)
```

### Step 5: Get Your Stream Key
1. Scroll to **Stream Settings** section
2. Copy the **Stream Key** (keep this secret!)
3. Copy the **Stream URL** (usually `rtmp://a.rtmp.youtube.com/live2`)
4. Save both for OBS configuration

### Step 6: Get Video ID for Your AI
1. After creating the stream, note the **waiting room URL**
2. URL format: `youtube.com/watch?v=VIDEO_ID`
3. Extract `VIDEO_ID` (the part after `v=`)
4. Example: `https://youtube.com/watch?v=dQw4w9WgXcQ` → ID is `dQw4w9WgXcQ`

---

## Part 2: OBS Studio Setup

### Step 1: Initial OBS Configuration

**Launch OBS for the first time:**
1. Auto-Configuration Wizard will appear
2. Select **"Optimize for streaming"**
3. Choose your primary usage: **"Streaming"**
4. Click **Next**

**Video Settings:**
```
Base Resolution: 1920x1080 (or your monitor resolution)
Output Resolution: 1280x720 (good balance for testing)
FPS: 30 (sufficient for static content/testing)
```

### Step 2: Configure Streaming Service

1. **Settings** → **Stream** tab
2. Configure as follows:

```
Service: YouTube - RTMPS
Server: Primary YouTube ingest server
Stream Key: [Paste your key from YouTube Studio]
```

**Important:** Click **"Connect Account (recommended)"** for easier management

### Step 3: Output Settings

**Settings** → **Output**

```
Output Mode: Simple (for testing)

Streaming:
  Video Bitrate: 2500 Kbps (sufficient for 720p)
  Encoder: x264 (CPU) or Hardware (NVENC/AMD if available)
  Audio Bitrate: 160 (CBR)

Recording (optional):
  Quality: High Quality, Medium File Size
  Format: mp4
```

### Step 4: Audio Settings

**Settings** → **Audio**

```
Sample Rate: 48 kHz
Channels: Stereo

Desktop Audio: Default (captures computer sounds)
Mic/Auxiliary Audio: Your microphone (if testing voice)
```

### Step 5: Video Settings

**Settings** → **Video**

```
Base (Canvas) Resolution: 1920x1080
Output (Scaled) Resolution: 1280x720
Downscale Filter: Lanczos (best quality)
FPS: 30
```

---

## Part 3: Creating a Simple Test Scene

### Scene 1: Static Image Stream (Minimal Setup)

**Add Sources:**

1. **Add Image Source** (for static test)
   - Click **+** in Sources panel
   - Select **Image**
   - Name it "Test Background"
   - Browse to an image file (or create one)
   - Right-click → **Transform** → **Fit to Screen**

2. **Add Text Source** (optional status indicator)
   - Click **+** → **Text (GDI+)**
   - Name it "Stream Status"
   - Add text: "🤖 AI Chat Bot Active - Testing Mode"
   - Choose font and size
   - Position at top of screen

3. **Add Browser Source** (optional - for dynamic content)
   - Click **+** → **Browser**
   - Can show a webpage, timer, or custom HTML
   - Useful for displaying stream info

### Scene 2: Screen Capture (For Desktop/Application Testing)

1. **Display Capture** (entire screen)
   - Click **+** → **Display Capture**
   - Select your monitor
   - Good for showing your AI interface

2. **Window Capture** (specific application)
   - Click **+** → **Window Capture**
   - Select your AI GUI window
   - More focused view

---

## Part 4: Starting Your Stream

### Pre-Stream Checklist

```
✓ YouTube Studio shows "Waiting to Start"
✓ OBS has your stream key configured
✓ Test scene is visible in OBS preview
✓ Audio levels are visible (check mixer)
✓ CPU usage is reasonable (<50% when streaming)
```

### Start Streaming

1. In OBS, click **"Start Streaming"** button (bottom right)
2. Wait 5-10 seconds for connection
3. Check YouTube Studio - status should change to **"Live"**
4. Bottom right in OBS shows:
   - Green indicator
   - "Live" status
   - Duration counter

### Verify Chat is Active

1. Open your stream URL in a different browser/incognito
2. Sign in with a different YouTube account
3. Verify chat box is visible
4. Send a test message
5. Check if your AI bot receives it

---

## Part 5: AI Bot Integration

### Configure Your .env File

```env
# YouTube Live Chat Integration
YOUTUBE_ENABLED=true
YOUTUBE_VIDEO_ID=your_video_id_here
YOUTUBE_AUTO_START=true
YOUTUBE_MAX_MESSAGES=10
```

### Start Your AI Bot

```bash
# Terminal/Command Prompt
cd /path/to/your/ai_project

# For CLI interface
python bot.py

# For GUI interface
python gui_interface.py
```

### Verify Integration

**System should show:**
```
[System] YouTube chat monitoring started for video: your_video_id
[YouTube Chat] Started monitoring
```

**In GUI:**
- YouTube Live Chat panel shows "Status: Running"
- Message counter updates as chat messages arrive

---

## Part 6: Testing the Complete System

### Test Sequence

1. **Start OBS Stream**
   - Click "Start Streaming" in OBS
   - Verify "Live" status in YouTube Studio

2. **Start AI Bot**
   - Launch bot.py or gui_interface.py
   - Verify YouTube integration started

3. **Open Stream in Another Browser**
   - Use incognito mode or different account
   - Navigate to your unlisted stream URL

4. **Send Test Messages**
   ```
   Test Account: "Hello bot!"
   Test Account: "Can you hear me?"
   Test Account: "What's the weather like?"
   ```

5. **Monitor AI Response**
   - Check if bot sees messages in system log
   - Verify bot includes chat context in responses
   - Confirm bot replies naturally to chat

---

## Part 7: Troubleshooting

### OBS Won't Connect
```
Problem: "Failed to connect to server"
Solutions:
  - Verify stream key is correct
  - Check YouTube stream is in "waiting" state
  - Try regenerating stream key in YouTube Studio
  - Check firewall isn't blocking OBS
```

### Chat Messages Not Appearing in Bot
```
Problem: Bot shows "Status: Running" but no messages
Solutions:
  - Verify VIDEO_ID is correct (not stream key!)
  - Check stream is actually LIVE (not just created)
  - Ensure pytchat is installed: pip install pytchat
  - Check system log for error messages
  - Try stopping/starting YouTube monitoring
```

### High CPU Usage in OBS
```
Problem: Computer slowing down
Solutions:
  - Lower output resolution to 720p or 480p
  - Reduce FPS to 24 or 30
  - Change encoder to hardware (NVENC/AMD VCE)
  - Close unnecessary applications
  - Use "Performance Mode" preset in OBS
```

### Stream Quality Issues
```
Problem: Pixelated or laggy stream
Solutions:
  - Increase video bitrate (try 3500-5000 Kbps)
  - Check your upload speed (should be 2x bitrate minimum)
  - Lower output resolution
  - Use "Quality" preset instead of "Performance"
```

### Bot Crashes When Reading Chat
```
Problem: Bot stops responding when chat is active
Solutions:
  - Check pytchat version: pip install --upgrade pytchat
  - Reduce YOUTUBE_MAX_MESSAGES to 5
  - Check for error messages in terminal
  - Verify video ID format (no extra characters)
```

---

## Part 8: Optimal Settings for AI Testing

### Recommended OBS Settings for Minimal Load

```
Output Resolution: 1280x720 (or lower)
FPS: 30
Video Bitrate: 2000 Kbps
Encoder: Hardware (if available)
CPU Preset: veryfast or faster
Audio Bitrate: 128 Kbps
```

### Recommended AI Settings

```python
# In your .env
YOUTUBE_MAX_MESSAGES=5  # Start small
YOUTUBE_AUTO_START=true  # Convenience
YOUTUBE_ENABLED=true
```

### Scene Recommendations

**For Testing:**
- Use static image or simple text
- Minimizes CPU usage
- Focuses on chat functionality

**For Demo/Production:**
- Screen capture of AI interface
- Webcam (if VTuber avatar)
- Overlay graphics
- Chat replay on screen (optional)

---

## Part 9: Advanced: Chat Replay Overlay

### Add Chat to Your Stream

1. **Get Chat Popup URL**
   - YouTube Studio → Stream Settings
   - Find "Live Chat" section
   - Click "Pop out chat"
   - Copy URL

2. **Add to OBS**
   - Add **Browser Source**
   - Paste chat popup URL
   - Set dimensions: 400x600 (adjust as needed)
   - Position on screen
   - Can add CSS filters for transparency

3. **Style Chat Overlay**
   ```css
   /* Add in Browser Source CSS field */
   body {
     background-color: rgba(0,0,0,0.7) !important;
   }
   ```

---

## Part 10: Going Live Checklist

### Before Stream
```
□ OBS configured with stream key
□ Test scene created and visible
□ Audio levels checked
□ .env file configured with correct VIDEO_ID
□ Bot tested with manual input
□ Second account ready for chat testing
```

### During Stream
```
□ OBS shows "Live" with green indicator
□ YouTube Studio shows stream active
□ Bot shows "YouTube monitoring: Running"
□ Test messages from second account work
□ Bot receives and responds to chat
□ CPU usage is manageable
```

### After Stream
```
□ Click "Stop Streaming" in OBS
□ Stop bot gracefully (not force-kill)
□ Check YouTube Studio for stream completion
□ Review any error logs
□ Save stream recording (if enabled)
```

---

## Quick Start Summary

```bash
# 1. YouTube Studio
Create Stream → Unlisted → Copy Stream Key & Video ID

# 2. OBS
Settings → Stream → Paste Stream Key → Start Streaming

# 3. AI Bot .env
YOUTUBE_ENABLED=true
YOUTUBE_VIDEO_ID=your_id_here

# 4. Start Bot
python gui_interface.py

# 5. Test
Open stream in incognito → Send chat message → Verify bot sees it
```

Your AI bot should now respond to YouTube live chat messages naturally, incorporating them into conversation context alongside its other capabilities (vision, search, memory).