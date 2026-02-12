# Address Geocoding & Normalization System

🌍 Smart company address geocoding with intelligent caching and quality controls.

## Features

- 🔍 **Smart Lookup** - Find company addresses with automatic normalization
- 💾 **Intelligent Caching** - Multi-tier caching saves API costs
- 📊 **Batch Processing** - Process multiple companies at once
- 🎯 **Quality Controls** - Automatic validation and confidence scoring
- 🗺️ **Visual Maps** - See locations on interactive maps
- 📈 **Usage Stats** - Monitor performance and cache effectiveness

## Live Demo

🚀 **[Try the app here](https://your-app-url.streamlit.app)** (replace with your actual URL after deployment)

## Quick Start

### Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/address-geocoding-system.git
   cd address-geocoding-system
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python -m streamlit run interfaces/streamlit_app.py
   ```

4. **Configure in the UI:**
   - Open http://localhost:8501
   - Go to ⚙️ Configuration page
   - Enter your Google Maps API key and Google Sheets credentials
   - Start geocoding!

## What You Need

- **Google Maps API Key** - [Get one here](https://console.cloud.google.com/) (40,000 free requests/month)
- **Google Sheet** - For storing addresses
- **Service Account JSON** - For Sheet access

📖 **See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions**

## How It Works

1. **Enter company name** + optional location hint
2. **System checks cache** → instant if found
3. **Checks Google Sheets** → fast if previously geocoded
4. **Calls Google Maps API** → if new, then stores for future
5. **Returns standardized address** with confidence score

## Architecture

```
User Query
    ↓
Cache Check (instant) ──→ Found? Return ✓
    ↓ Not found
Sheets Check (fast) ──→ Found? Return ✓
    ↓ Not found
Google Maps API ──→ Geocode & Store
    ↓
Return Result
```

## Project Structure

```
address-geocoding-system/
├── src/                    # Core modules
│   ├── config.py          # Configuration
│   ├── normalize.py       # Name normalization
│   ├── geocode.py         # Geocoding service
│   ├── matching.py        # Fuzzy matching
│   ├── validators.py      # Data validation
│   ├── lookup_service.py  # Main service
│   └── storage/           # Storage adapters
├── interfaces/            # User interfaces
│   ├── cli.py            # Command-line tool
│   └── streamlit_app.py  # Web interface
├── data/                  # Data files
└── docs/                  # Documentation
```

## Usage Examples

### Web Interface (Recommended)

```bash
python -m streamlit run interfaces/streamlit_app.py
```

### Command Line

```bash
# Single lookup
python interfaces/cli.py lookup --company "Tata Consultancy Services" --site "Pune, India"

# Batch processing
python interfaces/cli.py batch --input companies.csv --output results.csv

# View statistics
python interfaces/cli.py stats

# Review low-confidence results
python interfaces/cli.py review
```

## Documentation

- 📖 [Setup Guide](SETUP_GUIDE.md) - Detailed setup instructions
- 🚀 [Quick Start](QUICK_START.md) - Get started in 5 minutes
- ☁️ [Deployment](DEPLOYMENT.md) - Deploy to Streamlit Cloud
- 📝 [Walkthrough](C:\Users\KishorWakchaure\.gemini\antigravity\brain\18ec0747-9021-4d4d-b9f7-41aec40fd814\walkthrough.md) - Complete feature overview

## Tech Stack

- **Python 3.8+**
- **Streamlit** - Web interface
- **Google Maps API** - Geocoding
- **Google Sheets** - Data storage
- **SQLite** - Local caching
- **rapidfuzz** - Fuzzy matching

## Cost Optimization

✅ **Multi-tier caching** minimizes API calls  
✅ **Fuzzy matching** finds similar entries  
✅ **Google Sheets storage** for team sharing  
✅ **Free tier:** 40,000 requests/month  
✅ **Most teams stay within free tier!**

## Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## License

This project is for internal/educational use.

## Support

For questions or issues:
1. Check the documentation in `/docs`
2. Review error logs in the app
3. Open an issue on GitHub

---

**Built with ❤️ using Streamlit and Google APIs**
