# Streamlit Cloud Deployment Guide

## 🚀 Deploy Your Address Geocoding System to the Cloud

This guide will help you deploy the app to Streamlit Cloud so it's accessible from anywhere!

---

## Prerequisites

- GitHub account
- Streamlit Cloud account (free - sign up at [share.streamlit.io](https://share.streamlit.io))
- Your Google Maps API key and Service Account JSON (but these will be entered in the UI)

---

## Step 1: Push to GitHub

### 1.1 Create GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click **"+"** → **"New repository"**
3. Name it: `address-geocoding-system`
4. Make it **Public** (required for free Streamlit Cloud)
5. **Don't** initialize with README (we already have files)
6. Click **"Create repository"**

### 1.2 Initialize Git in Your Project

Open PowerShell in your project directory and run:

```powershell
cd C:\Users\KishorWakchaure\.gemini\antigravity\scratch\address-geocoding-system

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Address Geocoding System"

# Connect to GitHub (replace YOUR-USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR-USERNAME/address-geocoding-system.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** You may need to authenticate with GitHub. Use a Personal Access Token if prompted.

---

## Step 2: Deploy on Streamlit Cloud

### 2.1 Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"**
3. Sign in with your **GitHub account**
4. Authorize Streamlit to access your repositories

### 2.2 Create New App

1. Click **"New app"**
2. Select:
   - **Repository**: `YOUR-USERNAME/address-geocoding-system`
   - **Branch**: `main`
   - **Main file path**: `interfaces/streamlit_app.py`
3. Click **"Deploy!"**

### 2.3 Wait for Deployment

- Initial deployment takes 2-5 minutes
- You'll see build logs in real-time
- Once complete, you'll get a URL like: `https://your-app-name.streamlit.app`

---

## Step 3: Using the Deployed App

### No Secrets Needed! 🎉

Since we built the app with **UI-based configuration**, users can enter their credentials directly:

1. **Share the app URL** with your team
2. Each user opens the app
3. They go to **⚙️ Configuration** page
4. Enter their own:
   - Google Maps API Key
   - Google Sheet ID
   - Service Account JSON (upload or paste)
5. Click **Save Configuration**
6. Start using the app!

**Important Notes:**
- Credentials are stored in the user's browser session (RAM only)
- Not saved to server or disk
- Each user can use their own API keys
- Session clears when they close the browser tab

---

## Step 4: Optional - Configure Shared Credentials

If you want to provide **pre-configured credentials** for all users:

### 4.1 Add Streamlit Secrets

1. In Streamlit Cloud, click on your app
2. Go to **Settings** → **Secrets**
3. Add your credentials in TOML format:

```toml
# Google Maps API
GOOGLE_MAPS_API_KEY = "your_api_key_here"

# Google Sheets
GOOGLE_SHEETS_ID = "your_sheet_id_here"

# Service Account JSON (paste entire content)
SERVICE_ACCOUNT_JSON = '''
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  ...
}
'''
```

4. Click **Save**

### 4.2 Update App to Use Secrets (Optional)

If you add secrets, the app will automatically use them as defaults, but users can still override with their own credentials in the UI.

---

## Step 5: Managing Your Deployed App

### View App
- Your app URL: `https://your-app-name.streamlit.app`
- Share this with anyone!

### Monitor Usage
1. Go to Streamlit Cloud dashboard
2. Click on your app
3. View:
   - Active users
   - Resource usage
   - Error logs

### Update App
Whenever you push changes to GitHub:
```powershell
git add .
git commit -m "Update description"
git push
```

The app **automatically redeploys** within 1-2 minutes!

### Reboot App
If the app gets stuck:
1. Go to app settings
2. Click **"Reboot app"**

---

## 🎯 Quick Deployment Checklist

- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Sign up for Streamlit Cloud
- [ ] Deploy app from GitHub
- [ ] Share app URL with team
- [ ] (Optional) Configure shared secrets

---

## 💡 Best Practices

### For Individual Use
- Each user enters their own API credentials
- Perfect for testing or small teams
- No shared quota limits

### For Team Use
- Set up shared Service Account and Sheet
- Configure secrets in Streamlit Cloud
- Everyone uses the same address registry
- Monitor Google API usage

### Security Tips
- Use separate API keys for production vs. development
- Set API restrictions in Google Cloud Console
- Restrict API key to Geocoding API only
- Monitor usage to avoid unexpected charges
- Keep Service Account JSON secure

---

## 🔒 Data Security

**What's stored where:**

| Data | Location | Security |
|------|----------|----------|
| User credentials (UI entry) | Browser session only | Not saved anywhere |
| Shared secrets (optional) | Streamlit Cloud (encrypted) | Secure |
| Address data | Your Google Sheet | Your control |
| Cache | Temporary memory | Cleared on restart |

---

## 🆓 Streamlit Cloud Free Tier

**Includes:**
- ✅ Unlimited apps
- ✅ Unlimited viewers
- ✅ 1 GB RAM per app
- ✅ Auto-scaling
- ✅ Custom domains
- ✅ HTTPS by default

**Limits:**
- Repository must be public
- Apps sleep after inactivity (wake up on access)

---

## 🐛 Troubleshooting

### App Won't Deploy
- Check build logs for errors
- Verify `requirements.txt` is correct
- Ensure all imports are available

### App Keeps Rebooting
- Check resource usage (might need to optimize)
- Review error logs in Streamlit Cloud

### Configuration Not Saving
- Check browser console for errors
- Verify session state is working
- Try clearing browser cache

### GitHub Authentication Issues
- Create a [Personal Access Token](https://github.com/settings/tokens)
- Use token as password when pushing

---

## 📚 Additional Resources

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [GitHub Docs](https://docs.github.com)
- [Managing Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

## 🎉 You're Done!

Your app is now live and accessible worldwide! Share the URL and start geocoding addresses from anywhere!

**Need help?** Check the logs in Streamlit Cloud or review the error messages.
