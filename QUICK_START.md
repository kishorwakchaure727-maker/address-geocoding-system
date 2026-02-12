# Quick Start Guide - No Setup Required!

## Run the App Without Credentials

You can run the Streamlit app immediately and configure it through the web interface!

### Step 1: Install Dependencies

```bash
cd C:\Users\KishorWakchaure\.gemini\antigravity\scratch\address-geocoding-system
pip install -r requirements.txt
```

### Step 2: Run the App

```bash
streamlit run interfaces\streamlit_app.py
```

The app will open in your browser at http://localhost:8501

### Step 3: Configure Through UI

1. Go to the **⚙️ Configuration** page (it opens by default)
2. Enter your credentials:
   - **Google Maps API Key**
   - **Google Sheet ID** 
   - **Service Account JSON** (upload file or paste content)
3. Click **"💾 Save Configuration"**
4. Test your connections!

That's it! The credentials are stored in your browser session (not saved to disk).

## What You Need

### 1. Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Geocoding API"
4. Create API Key
5. Copy the key

**Free Tier:** 40,000 requests/month

### 2. Google Sheet ID

1. Create a new Google Sheet
2. Get the ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
   ```

### 3. Service Account JSON

1. In Google Cloud Console → IAM & Admin → Service Accounts
2. Create service account
3. Create JSON key
4. Download the file
5. Upload or paste in the app

**Important:** Share your Google Sheet with the service account email (found in the JSON file under `client_email`)

## Features in the App

### ⚙️ Configuration Page
- Enter all credentials through forms
- Test connections with one click
- Visual status indicators

### 🔍 Lookup Page
- Enter company name
- Optional location hint
- See results with confidence scores
- View on interactive map

### 📊 Batch Processing
- Upload CSV file with companies
- Process all at once
- Download results

### 📈 Statistics
- Total records
- Cache performance
- Source breakdown

### 🔍 Review Queue
- Low-confidence results
- Manual review workflow

## No .env File Needed!

All configuration happens through the web UI - perfect for:
- Quick demos
- Testing with different accounts
- Team members with their own API keys
- No file system access needed

## Security Note

Credentials are stored in Streamlit's session state (RAM only). They're not written to disk and are cleared when you close the browser tab.

For production use, you can still use the `.env` file approach as documented in SETUP_GUIDE.md.

## Troubleshooting

**App won't start:**
```bash
pip install -r requirements.txt
```

**Can't find localhost:8501:**
Check the terminal output for the correct URL

**Configuration won't save:**
- Verify API key format
- Check Sheet ID (no spaces)
- Validate JSON syntax (use a JSON validator if needed)

**Test connections fail:**
- Verify API key is correct
- Check Sheet is shared with service account email
- Ensure Geocoding API is enabled in Google Cloud
