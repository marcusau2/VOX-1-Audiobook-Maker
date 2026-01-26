# GitHub Setup Guide

This guide will walk you through publishing your VOX-1 Audiobook Maker project to GitHub.

---

## Prerequisites

✅ Git is installed (already confirmed)
✅ Project is ready (already prepared)
✅ Initial commit created (already done)

You'll need:
- Your GitHub account credentials
- 5 minutes of time

---

## Step 1: Create GitHub Repository

### Option A: Using GitHub Website (Easiest)

1. Go to: https://github.com/new

2. Fill in the details:
   - **Repository name:** `VOX-1-Audiobook-Maker`
   - **Description:** "GPU-accelerated audiobook generator using Qwen2-TTS"
   - **Visibility:** **Private** ✅
   - **DO NOT** check "Add README" (we already have one)
   - **DO NOT** check "Add .gitignore" (we already have one)
   - **DO NOT** check "Choose a license" (we'll add later)

3. Click "Create repository"

4. **IMPORTANT:** After creating, you'll see a page with commands. Keep this page open!

### Option B: Using Command Line (If you prefer)

```bash
# You'll need GitHub CLI installed for this
gh repo create VOX-1-Audiobook-Maker --private --source=. --remote=origin
```

---

## Step 2: Connect Your Local Repository to GitHub

Copy your GitHub username and run these commands:

**Replace `YOUR_GITHUB_USERNAME` with your actual username!**

```bash
cd "E:\Gemini Projects\Audiobook Maker"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/VOX-1-Audiobook-Maker.git
git branch -M main
git push -u origin main
```

### What Each Command Does:
- `git remote add origin` - Links your local repo to GitHub
- `git branch -M main` - Renames your branch to "main" (GitHub default)
- `git push -u origin main` - Uploads your code to GitHub

---

## Step 3: Authenticate

When you run `git push`, you'll be asked to authenticate. You have two options:

### Option A: GitHub CLI (Recommended)

If you have GitHub CLI installed:
```bash
gh auth login
```
Follow the prompts to authenticate.

### Option B: Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. Set:
   - Note: "VOX-1 Development"
   - Expiration: Your choice
   - Scopes: Check `repo` (all sub-items)
3. Click "Generate token"
4. **Copy the token** (you won't see it again!)
5. When prompted for password during `git push`, paste the token instead

### Option C: Git Credential Manager

Windows may prompt you with a login window. Just enter your GitHub credentials.

---

## Step 4: Update Setup Script with Your Username

After pushing to GitHub, update the portable setup script with your username:

1. Open: `VOX-1-Portable\Setup-Portable.bat`
2. Find line 63: `set GITHUB_USER=YOUR_USERNAME`
3. Replace `YOUR_USERNAME` with your actual GitHub username
4. Save the file
5. Commit and push the change:

```bash
cd "E:\Gemini Projects\Audiobook Maker"
git add VOX-1-Portable/Setup-Portable.bat
git commit -m "Update Setup-Portable.bat with GitHub username"
git push
```

---

## Step 5: Verify Everything Works

1. Go to: `https://github.com/YOUR_USERNAME/VOX-1-Audiobook-Maker`
2. You should see:
   - ✅ README.md displayed
   - ✅ All your files uploaded
   - ✅ Repository marked as "Private"

---

## Testing the Portable Setup

Now that it's on GitHub, you can test on another PC:

1. On the other PC, download just the `VOX-1-Portable` folder
2. Run `Download-Python.bat`
3. Run `Setup-Portable.bat`
4. It will download everything from GitHub automatically!

---

## Using on Your Other Computer

### Method 1: Clone the Entire Repository

```bash
git clone https://github.com/YOUR_USERNAME/VOX-1-Audiobook-Maker.git
cd VOX-1-Audiobook-Maker
pip install -r requirements.txt
python app.py
```

### Method 2: Download ZIP (No git required)

1. Go to your repository on GitHub
2. Click "Code" → "Download ZIP"
3. Extract and follow MANUAL_INSTALL.md

### Method 3: Use Portable Version

1. Download just the `VOX-1-Portable` folder from GitHub
2. Run `Download-Python.bat`
3. Run `Setup-Portable.bat` (downloads everything from GitHub)
4. Launch with `Launch VOX-1 Portable.vbs`

---

## Making It Public Later

When you're ready to share with the world:

1. Go to repository settings: `https://github.com/YOUR_USERNAME/VOX-1-Audiobook-Maker/settings`
2. Scroll to "Danger Zone"
3. Click "Change repository visibility"
4. Select "Make public"
5. Confirm

---

## Updating the Repository

After making changes locally:

```bash
cd "E:\Gemini Projects\Audiobook Maker"
git add .
git commit -m "Description of your changes"
git push
```

---

## Common Issues

### "Authentication failed"
- Use personal access token instead of password
- Or install GitHub CLI: `gh auth login`

### "Permission denied"
- Make sure you're the repository owner
- Check your personal access token has `repo` scope

### "Repository not found"
- Double-check the repository name
- Make sure you replaced YOUR_USERNAME with your actual username

### "Portable setup can't download from private repo"
- Either make the repo public temporarily
- Or manually download and extract the files

---

## Summary

You've completed:
- ✅ Created a private GitHub repository
- ✅ Pushed all your code
- ✅ Set up automatic downloads from GitHub
- ✅ Ready to test on another PC

Next steps:
1. Update Setup-Portable.bat with your GitHub username
2. Test on your other computer
3. Make public when ready

---

**Questions?** Check the GitHub documentation or open an issue in your repository.

---

**Last Updated:** January 2025
