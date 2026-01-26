# VOX-1 Audiobook Maker - User Guide

Welcome to VOX-1! This guide will help you create your first audiobook.

---

## 🚀 Quick Start

### Launching the App

**Double-click:** `RUN VOX-1.bat`

The app will open in your web browser (usually at http://127.0.0.1:7860)

**Note:** Keep the black console window open - closing it will stop the app!

---

## 📖 Creating Your First Audiobook

### Step 1: Prepare Your Text

VOX-1 accepts:
- **TXT files** - Plain text, simple audiobooks
- **JSON files** - Books with chapters (use BookSmith to create)
- **EPUB/PDF files** - Extract chapters using BookSmith tab

### Step 2: Create or Load a Voice

Go to **"The Lab"** tab:

**Option A: Use a Pre-made Voice**
- Click "Load Master Voice"
- Select one of the included voice files (if you have any)

**Option B: Design a New Voice**
1. Enter a text description of the voice you want
   - Example: "A warm, friendly female voice with a slight British accent"
2. Click "Design Voice from Description"
3. Wait a moment for the voice to be created
4. Click "Save as Master Voice"
5. Give it a name (e.g., "narrator_female")

**Option C: Clone a Voice from Audio**
1. Click "Upload Audio" and select a WAV or MP3 file (10-30 seconds)
2. The audio will be optimized automatically
3. Click "Clone Voice from Audio"
4. Click "Save as Master Voice"
5. Give it a name

### Step 3: Prepare Your Book (If using EPUB/PDF)

Go to **"BookSmith"** tab:

1. Click "Load Book" and select your EPUB or PDF
2. Wait for chapters to be extracted
3. Review the chapters in the preview
4. Click "Export to JSON"
5. Save the JSON file

**Skip this step if you already have a TXT or JSON file!**

### Step 4: Generate Your Audiobook

Go to **"Studio"** tab:

1. **Load your voice:**
   - Click "Load Master Voice"
   - Select the voice you created/saved earlier

2. **Load your book:**
   - Click "Load Book"
   - Select your TXT or JSON file

3. **Adjust settings (Optional):**
   - Go to "Advanced Settings" tab
   - Adjust batch size based on your GPU (see table below)
   - Default settings work great for most people!

4. **Start rendering:**
   - Click "Render Audiobook"
   - Watch the progress in the activity log
   - Generation takes time - be patient!

### Step 5: Find Your Audiobook

Your finished audiobook will be in:
- **TXT files** → `VOX-Output/` folder (single MP3 file)
- **JSON files** → `VOX-Output/` folder (M4B file with chapters)

---

## ⚙️ Performance Settings

### Recommended Settings by GPU

Go to **"Advanced Settings"** tab to adjust these:

| Your GPU VRAM | Batch Size | Model Size | Expected Speed |
|---------------|------------|------------|----------------|
| 8-10 GB       | 1-2        | 0.6B       | 1.5x realtime  |
| 12 GB         | 3-5        | 0.6B       | 1.8x realtime  |
| 16 GB+        | 5-10       | 1.7B       | 2.0x realtime  |

**How to check your GPU VRAM:**
- Open Task Manager (Ctrl+Shift+Esc)
- Go to "Performance" tab
- Click "GPU" on the left
- Look for "Dedicated GPU memory"

### What Each Setting Does

**Batch Size:**
- How many text chunks to process at once
- Higher = faster but uses more VRAM
- Lower = slower but safer for small GPUs
- Default: 3 (good for most 12GB GPUs)

**Model Size:**
- 0.6B = Faster, smaller, good quality (default)
- 1.7B = Slower, larger, better quality
- Use 0.6B unless you have 16GB+ VRAM

**Attention Mode:**
- sdpa = Fastest (default)
- sage_attn = Memory efficient
- flash_attn_2 = Fastest but requires special installation
- **Keep it on "sdpa"** unless you know what you're doing

**Temperature:**
- Controls voice variation
- 0.7 = Natural (default)
- Lower (0.3) = More consistent
- Higher (1.0) = More expressive

**Chunk Size:**
- Characters per chunk
- 500 = Default (good balance)
- Larger = Fewer chunks but more VRAM needed

---

## 🔍 Monitoring Progress

### Activity Log

The activity log shows:
- Current chunk being processed
- VRAM usage after each batch
- Errors or warnings
- Generation time per chunk

### Progress Bar

Shows overall progress:
- "Processing chunks 1-3/61" = Working on chunks 1, 2, 3 out of 61 total
- Percentage complete

### VRAM Monitoring

After each batch, you'll see:
```
VRAM: 7.2GB / 12.0GB (60%)
```
- First number = Currently used
- Second number = Total available
- Percentage = How much you're using

**If VRAM reaches 90%+** → Reduce batch size!

---

## 🛠️ Troubleshooting

### "CUDA out of memory" Error

**Fix:**
1. Close other GPU-using applications (games, video editing, etc.)
2. Go to Advanced Settings
3. Reduce Batch Size (try 2, then 1)
4. Switch Model Size to 0.6B
5. Restart the app

### App is Slow (>30 seconds per chunk)

**Possible causes:**
- Batch size too low → Increase it in Advanced Settings
- Wrong attention mode → Switch to "sdpa"
- GPU drivers outdated → Update NVIDIA drivers
- Other apps using GPU → Close them

### Voice Sounds Wrong

**Tips:**
- Voice cloning needs 10-30 seconds of clear audio
- Avoid background noise in reference audio
- Try different text descriptions for designed voices
- Emotion settings affect the voice character

### App Won't Start

1. Make sure you have an NVIDIA GPU (AMD/Intel won't work)
2. Check GPU drivers are up to date
3. Run `RUN VOX-1.bat` (not the VBS file) to see error messages
4. Make sure no antivirus is blocking Python

### Generation Stops or Freezes

- Don't close the black console window
- Check activity log for errors
- If VRAM is at 100%, reduce batch size
- Try restarting the app

---

## 📁 File Locations

### Input Files
Put your books/audio here:
- Anywhere on your computer
- Desktop works fine
- The app will ask you to browse for files

### Output Files
Your audiobooks are saved here:
- `VOX-Output/` - Final audiobooks (M4B/MP3)
- `Output/` - Individual chapter audio files

### Voice Files
Saved voices are stored as JSON files in the app folder.

### Temporary Files
The app creates temp files during processing:
- `temp_work/` - Automatically cleaned up
- These can be deleted if the app crashes

---

## 💡 Tips & Tricks

### For Better Quality
- Use clear, well-punctuated text
- Break very long books into sections
- Use the 1.7B model if you have enough VRAM
- Reference audio for cloning should be clean (no music/noise)

### For Faster Generation
- Increase batch size (if VRAM allows)
- Use 0.6B model instead of 1.7B
- Keep attention mode on "sdpa"
- Close other GPU applications

### For Chapters
- Use BookSmith to extract from EPUB/PDF
- JSON format supports chapters and metadata
- M4B output includes chapter markers (great for audiobook players!)

### Voice Design Tips
- Be specific in descriptions: "deep male voice" vs "warm, friendly male voice with slight southern accent"
- Experiment with emotion settings
- Save multiple versions to compare
- Keep reference audio short (10-30 seconds) and clear

---

## 🎯 Common Workflows

### Simple Audiobook from TXT
1. Launch app → RUN VOX-1.bat
2. Lab tab → Design Voice → Save as Master Voice
3. Studio tab → Load Master Voice → Load TXT file
4. Click "Render Audiobook"
5. Done! Check VOX-Output/ folder

### Chapter-Based Audiobook from EPUB
1. Launch app → RUN VOX-1.bat
2. Lab tab → Design/Clone Voice → Save as Master Voice
3. BookSmith tab → Load EPUB → Export to JSON
4. Studio tab → Load Master Voice → Load JSON file
5. Click "Render Audiobook"
6. Done! You'll get an M4B with chapters

### Multiple Books with Same Voice
1. Create and save your voice once (Lab tab)
2. For each book:
   - Studio tab → Load Master Voice (same one)
   - Load Book (different TXT/JSON)
   - Render Audiobook
3. All books will use the same narrator voice

---

## ❓ FAQ

**Q: How long does it take to generate an audiobook?**
A: Depends on length and settings. Roughly 1.5-2x realtime. A 10-hour audiobook takes 5-7 hours to generate.

**Q: Can I use this offline?**
A: Yes! After first run (models download), no internet needed.

**Q: Does this work on Mac/Linux?**
A: Currently Windows only. Linux support planned.

**Q: Can I use my own voice?**
A: Yes! Use voice cloning with a recording of yourself (10-30 seconds).

**Q: Is this legal for commercial use?**
A: Check license terms. Currently in development. Don't distribute generated content without permission.

**Q: How much GPU memory do I need?**
A: Minimum 8GB VRAM. 12GB recommended. 16GB+ is ideal.

**Q: Can I pause and resume?**
A: Not currently, but generated chunks are cached. If it crashes, restart and it will skip completed chunks.

**Q: What audio formats are supported?**
A: Output: MP3, M4B. Input (for cloning): WAV, MP3.

---

## 🔄 Updating VOX-1

To update to the latest version:
1. Run `Install-VOX-1.bat` again
2. Choose "Yes" when asked to re-download
3. Your voices and output files are safe!

---

## 🆘 Getting Help

If you're stuck:
1. Check the activity log for error messages
2. Read this guide's Troubleshooting section
3. Check GitHub issues: https://github.com/marcusau2/VOX-1-Audiobook-Maker/issues
4. Open a new issue with:
   - Your GPU model and VRAM
   - Error messages from activity log
   - What you were trying to do

---

## 🎉 You're Ready!

Start with a small test:
1. Launch the app
2. Create a simple voice
3. Use a short text file (1-2 paragraphs)
4. Generate your first audiobook!

Once you're comfortable, try longer books and experiment with settings.

**Enjoy creating audiobooks with VOX-1!**

---

Last Updated: January 2026
