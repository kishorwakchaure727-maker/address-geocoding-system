# Setup Guide for Address Geocoding System

This guide will help you set up the Address Geocoding System from scratch.

## Prerequisites

- Python 3.8 or higher
- Google Cloud account (for Maps API)
- Google account (for Sheets storage)

## Step 1: Install Python Dependencies

Navigate to the project directory and install all required packages:

```bash
cd address-geocoding-system
pip install -r requirements.txt
```

If you encounter permission issues, use:
```bash
pip install --user -r requirements.txt
```

## Step 2: Set Up Google Maps Geocoding API

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name your project (e.g., "Address Geocoding")
4. Click "Create"

### 2.2 Enable Geocoding API

1. In the Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Geocoding API"
3. Click on it and click "Enable"

### 2.3 Create API Key

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the API key (you'll need this later)
4. (Optional but recommended) Click "Restrict Key":
   - Under "API restrictions", select "Restrict key"
   - Check only "Geocoding API"
   - Click "Save"

### 2.4 Enable Billing

**Important:** Even though the free tier gives you 40,000 requests/month, you must enable billing.

1. Go to "Billing" in the Cloud Console
2. Follow the prompts to set up a billing account
3. Monitor usage to stay within free tier

## Step 3: Set Up Google Sheets

### 3.1 Create Service Account

1. In Cloud Console, go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name it (e.g., "geocoding-service")
4. Click "Create and Continue"
5. Skip "Grant this service account access to project" (click Continue)
6. Skip "Grant users access" (click Done)

### 3.2 Create Service Account Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select "JSON" format
5. Click "Create"
6. A JSON file will download - **save this as `service_account.json`** in your project root directory

### 3.3 Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it "Address Registry" (or any name you prefer)
4. Open the service account JSON file and find the `client_email` field
5. Share the Google Sheet with this email address:
   - Click "Share" button
   - Paste the service account email
   - Give it "Editor" access
   - Uncheck "Notify people"
   - Click "Send"

### 3.4 Get Sheet ID

From the Sheet URL:
```
https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
```

Copy the `[SHEET_ID]` part.

## Step 4: Configure Environment Variables

### 4.1 Create .env File

Copy the example file:
```bash
cp .env.example .env
```

### 4.2 Edit .env File

Open `.env` in a text editor and fill in your values:

```
# Google Maps API Key (from Step 2.3)
GOOGLE_MAPS_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Google Sheet ID (from Step 3.4)
GOOGLE_SHEETS_ID=1abcDEF0123456789XYZ_example_sheet_id

# Keep these as default (or customize)
WORKSHEET_NAME=address_registry
SERVICE_ACCOUNT_FILE=service_account.json
CONFIDENCE_THRESHOLD=0.80
ENABLE_CACHE=true
CACHE_TYPE=sqlite
CACHE_DB_PATH=.cache.db
CACHE_TTL_HOURS=24
MAX_CACHE_SIZE=10000
MAX_API_CALLS_PER_DAY=1000
WARNING_THRESHOLD=800
LOG_LEVEL=INFO
LOG_FILE=geocoding.log
```

## Step 5: Verify Setup

Test your configuration:

```bash
python -c "from src import config; valid, errors = config.validate_config(); print('✓ Configuration valid!' if valid else f'✗ Errors: {errors}')"
```

## Step 6: Run Your First Lookup

### Option A: CLI

```bash
python interfaces/cli.py lookup --company "Tata Consultancy Services" --site "Pune, India"
```

### Option B: Web Interface

```bash
streamlit run interfaces/streamlit_app.py
```

Then open the URL shown in your browser (usually http://localhost:8501).

## Troubleshooting

### "API key not valid"
- Double-check your API key in `.env`
- Ensure Geocoding API is enabled
- Verify billing is enabled

### "Permission denied" on Google Sheets
- Verify the Sheet is shared with the service account email
- Check the email in `service_account.json` under `client_email`
- Ensure service account has "Editor" access

### "No module named 'googlemaps'"
```bash
pip install -r requirements.txt
```

### Rate limit errors
- Check daily limit in `.env` (`MAX_API_CALLS_PER_DAY`)
- Verify you're within Google's free tier (40,000/month)
- Cache is enabled to minimize API calls

## Next Steps

1. **Customize Golden Mappings:** Edit `data/golden_mappings.json` to add your company name standardizations

2. **Test with Sample Data:**
   ```bash
   python interfaces/cli.py batch --input data/sample_input.csv --output results.csv
   ```

3. **Review Queue:** Check low-confidence results
   ```bash
   python interfaces/cli.py review
   ```

4. **Monitor Usage:**
   ```bash
   python interfaces/cli.py stats
   ```

## Cost Management

**Free Tier:** 40,000 geocoding requests/month

**With Caching:** Repeated lookups are free (served from cache/storage)

**Tips:**
- Enable caching (default)
- Process batches during off-peak
- Review and correct low-confidence results manually
- Use fuzzy matching to avoid duplicate geocoding

## Support

For issues, check:
1. Configuration validation
2. Google Cloud Console for API status
3. Google Sheet sharing settings
4. Log files (`geocoding.log`)
