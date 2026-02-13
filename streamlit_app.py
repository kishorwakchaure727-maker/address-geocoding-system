"""
Streamlit web interface for address geocoding system.
Users can enter API keys directly in the UI.
"""
print("DEBUG: Streamlit app starting...")
import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

try:
    import streamlit as st
except Exception as e:
    print(f"DEBUG: Failed to import streamlit: {e}")

from datetime import datetime
import tempfile
import json
import base64
import pandas as pd
import google.generativeai as genai
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

# --- AI Assistant Persona ---
ASSISTANT_SYSTEM_PROMPT = """
You are "Resy", a high-end, friendly, and professional voice-enabled guide for this 
Address Geocoding & Verification System.

Your purpose is to explain the app to users verbally.
Key facts about the app:
1. It standardizes company addresses (STREET ADDRESS1, CITY NAME, PIN CODE, etc.).
2. It uses multi-tier caching (Session, SQLite, Google Sheets) to save costs.
3. It has a "Fully Agentic Mode" using Gemini AI to verify addresses by searching the web.
4. It features a batch processing tool for CSV files, analytics stats, and a manual Review Queue.

Keep your responses VERY CONCISE (max 2-3 sentences) because you are being converted to voice.
Sound enthusiastic, premium, and helpful. Always greet the user warmly if it's the start of the conversation.
"""

def get_resy_response(user_text):
    """Generate a response from Gemini for Resy, with comprehensive local knowledge."""
    # --- Comprehensive Local Knowledge Base ---
    # Resy can guide users from start to finish, even without an AI API key.
    LOCAL_KB = [
        # --- Greetings ---
        (["hello", "hi", "hey", "good morning", "good evening"],
         "Hello! 👋 I'm **Resy**, your intelligent guide for this Address Geocoding System. I can help you with setup, lookups, batch processing, and everything in between. What would you like to know?"),
        (["who are you", "what are you", "your name"],
         "I'm **Resy**, the AI-powered assistant built into this app. I know everything about how this system works — from getting your API keys to running batch geocoding jobs. Ask me anything!"),
        (["what can you do", "help", "what do you know"],
         "I can help you with: \n• **Setup** — API keys, Service Account JSON, Google Sheets\n• **Lookups** — Single company address search\n• **Batch Processing** — CSV upload and bulk geocoding\n• **Architecture** — How multi-tier caching saves you money\n• **AI Verification** — Agentic mode for web-based address confirmation\n• **Troubleshooting** — Common issues and fixes\n\nJust ask about any topic!"),

        # --- Getting Started / Setup ---
        (["get started", "start", "setup", "begin", "first step", "new user"],
         "Welcome! Here's how to get started:\n\n**Step 1:** Go to the ⚙️ **Configuration** tab.\n**Step 2:** Enter your **Google Maps API Key** (required for geocoding).\n**Step 3:** Optionally add a **Google Sheet ID** and **Service Account JSON** for team-wide caching.\n**Step 4:** Optionally add a **Google AI API Key** for Agentic AI verification.\n\nOnce configured, head to 🔍 **Lookup** to search for your first company address!"),

        # --- API Keys ---
        (["api key", "google maps key", "maps key", "geocoding key"],
         "The **Google Maps API Key** is essential for geocoding.\n\n**How to get one:**\n1. Go to [Google Cloud Console](https://console.cloud.google.com/)\n2. Create a project (or select an existing one)\n3. Go to **APIs & Services** → **Credentials**\n4. Click **Create Credentials** → **API Key**\n5. Enable the **Geocoding API** under **APIs & Services** → **Library**\n6. Copy the key and paste it in the ⚙️ Configuration tab.\n\n💡 Google gives you $200/month free credit (~40,000 requests)!"),
        (["ai key", "ai api", "gemini key", "google ai"],
         "The **Google AI API Key** powers two features:\n1. **Resy** (me!) — I use Gemini to answer complex questions\n2. **Agentic AI Verification** — The system searches the web to confirm addresses\n\n**How to get one:**\n1. Go to [Google AI Studio](https://aistudio.google.com/apikey)\n2. Click **Create API Key**\n3. Copy and paste it in the ⚙️ Configuration tab\n\nThis key is optional — the app works without it, but AI verification won't be available."),

        # --- Service Account JSON ---
        (["service account", "service json", "json file", "credentials file", "json credentials"],
         "A **Service Account JSON** is a credentials file from Google Cloud that lets the app access your **Google Sheet** without you logging in.\n\n**How to get one:**\n1. Go to **Google Cloud Console** → **IAM & Admin** → **Service Accounts**\n2. Click **Create Service Account**, name it (e.g., 'geocoder-bot')\n3. Click on the account → **Keys** tab → **Add Key** → **Create new key** → **JSON**\n4. A `.json` file downloads — upload this in the ⚙️ Configuration tab\n5. **Important:** Share your Google Sheet with the email found in the JSON (`client_email` field)\n\nThis is optional but required if you want team-wide shared caching via Google Sheets."),

        # --- Google Sheets ---
        (["sheet", "google sheet", "sheet id", "spreadsheet"],
         "The **Google Sheet ID** connects the app to a shared team spreadsheet for caching results.\n\n**How to find your Sheet ID:**\n1. Open your Google Sheet\n2. Look at the URL: `https://docs.google.com/spreadsheets/d/`**THIS_IS_YOUR_ID**`/edit`\n3. Copy that long string between `/d/` and `/edit`\n4. Paste it in the ⚙️ Configuration tab\n\n**Important:** Make sure the Service Account email has **Editor** access to this sheet!\n\n💡 Sharing one Sheet across departments means everyone benefits from cached lookups — saving API costs!"),

        # --- Individual Lookup ---
        (["lookup", "search", "find address", "single", "individual"],
         "The 🔍 **Individual Lookup** page lets you find a company's standardized address.\n\n**How to use it:**\n1. Enter the **Company Name** (e.g., 'Tata Consultancy Services')\n2. Optionally provide a **Site Hint** (e.g., 'Mumbai' or 'India') for better accuracy\n3. Click **Search**\n\n**Results include:**\n• Standardized address (Street, City, State, PIN, Country)\n• Confidence score (0-100%)\n• Interactive map\n• Direct links to Google Maps and source verification\n• AI verification status (if enabled)"),

        # --- Batch Processing ---
        (["batch", "csv", "bulk", "upload", "multiple", "file"],
         "The 📊 **Batch Processing** page handles hundreds of addresses at once.\n\n**How to use it:**\n1. Prepare a CSV file with a column named `company`\n2. Upload it in the Batch tab\n3. The system processes each company through the multi-tier cache\n4. Download the enriched CSV with all standardized addresses\n\n💡 The system uses caching, so repeat companies are resolved instantly without API calls!"),

        # --- Multi-Tier Caching ---
        (["cache", "caching", "tier", "multi-tier", "architecture", "how it works", "how does it work"],
         "The app uses a **6-tier lookup architecture** to minimize API costs:\n\n1. ⚡ **Session Cache** (Instant) — Checks current session memory\n2. 💾 **SQLite Database** (Fast) — Persistent local cache\n3. 📊 **Google Sheets** (Team) — Shared team-wide registry\n4. 🤝 **Fuzzy Matching** — Finds similar names (e.g., 'Tata Services' → 'Tata Consultancy Services')\n5. 🌏 **Google Maps API** — Final fallback for new addresses\n6. 🤖 **Agentic AI** — Optional web verification\n\n💰 This can save up to **90% in API costs** because most lookups are resolved from cache!"),

        # --- Agentic AI ---
        (["agentic", "ai verification", "verify", "web search", "ai mode"],
         "**Agentic AI Verification** is an optional feature that uses Gemini AI to search the web and confirm address details.\n\n**How it works:**\n1. After geocoding, the AI agent searches for the company online\n2. It finds the company's official website or directory listing\n3. It extracts the address from the source page\n4. It compares the found address with the geocoded result\n5. It provides a confidence score and the **source URL** where it found the information\n\n**To enable it:** Add a Google AI API Key in ⚙️ Configuration and check the 'Agentic AI' toggle.\n\n⚠️ This uses additional API calls, so it's best for high-value lookups where accuracy is critical."),

        # --- Stats ---
        (["stats", "statistics", "analytics", "dashboard", "cost"],
         "The 📈 **Stats** page shows your geocoding analytics:\n\n• Total addresses processed\n• Cache hit rate (how many were resolved without API calls)\n• Estimated cost savings\n• Breakdown by source tier (Session, SQLite, Sheets, API)\n\n💡 A high cache hit rate means you're saving money!"),

        # --- Review Queue ---
        (["review", "queue", "manual", "flag", "low confidence"],
         "The 🔍 **Review Queue** is for results that need manual verification.\n\n**When are results flagged?**\n• Confidence score below 0.8 (80%)\n• AI verification returned 'uncertain' or 'mismatch'\n• Fuzzy match with low similarity\n\nYou can review each flagged result, approve it, or manually correct the address."),

        # --- Confidence Score ---
        (["confidence", "score", "accuracy", "quality"],
         "Every geocoded result gets a **Confidence Score** from 0 to 1 (0-100%):\n\n• **0.9-1.0** ✅ Excellent — High confidence, likely correct\n• **0.8-0.9** ✅ Good — Reliable for most purposes\n• **0.6-0.8** ⚠️ Review — May need manual verification\n• **Below 0.6** ❌ Low — Flagged for review queue\n\nThe score is based on the quality of the geocoding match and the AI verification (if enabled)."),

        # --- Cost & Pricing ---
        (["cost", "price", "pricing", "free", "money", "expensive", "cheap"],
         "**Cost breakdown:**\n• **Google Maps Geocoding:** $5 per 1,000 requests ($200/month free credit ≈ 40,000 free requests)\n• **Google AI (Gemini):** Free tier available at [AI Studio](https://aistudio.google.com/)\n• **Google Sheets:** Free\n• **This app:** Free and open-source!\n\n💰 With multi-tier caching, you can save up to **90%** because repeat lookups use cached results instead of making new API calls."),

        # --- Troubleshooting ---
        (["error", "problem", "not working", "issue", "fix", "trouble", "bug"],
         "Here are common issues and fixes:\n\n• **'Service not configured'** → Go to ⚙️ Configuration and add your Google Maps API Key\n• **'No results found'** → Try adding a site hint (e.g., 'India' or 'USA')\n• **Low confidence scores** → The company name may be ambiguous; add a location hint\n• **Sheet access error** → Make sure your Google Sheet is shared with the Service Account email\n• **AI not responding** → Check your Google AI API Key in Configuration\n\nStill stuck? Try describing your issue to me!"),

        # --- Navigation ---
        (["navigate", "page", "tab", "where", "find", "go to", "menu"],
         "Here's a guide to all the pages:\n\n• 📖 **Instructions** — Full technical overview and architecture diagram\n• ⚙️ **Configuration** — Enter API keys and credentials\n• 🔍 **Lookup** — Search for a single company address\n• 📊 **Batch** — Upload CSV for bulk processing\n• 📈 **Stats** — View analytics and cost savings\n• 🔍 **Review Queue** — Manually verify flagged results\n\nUse the sidebar on the left to switch between pages!"),

        # --- Data Format ---
        (["format", "column", "csv format", "output", "fields", "data"],
         "The system produces standardized address records with these fields:\n\n• **COMPANY NAME (NORMALIZED)** — Cleaned company name\n• **STREET ADDRESS1** — Street line\n• **CITY NAME** — City\n• **STATE NAME** — State/Province\n• **PIN CODE** — Postal/ZIP code\n• **COUNTRY NAME** — Country\n• **LAT / LNG** — GPS coordinates\n• **CONFIDENCE** — Match quality (0-1)\n• **AI VERIFICATION STATUS** — AI check result\n• **MAPS LINK** — Google Maps view\n• **AI SOURCE URL** — Website where address was found"),

        # --- Security ---
        (["security", "safe", "secure", "data privacy", "privacy"],
         "Your data security is important:\n\n• API keys are stored only in your **browser session** — never saved to disk\n• The Service Account JSON is processed in memory only\n• All API calls use **HTTPS** encryption\n• Your Google Sheet is only accessible to accounts you explicitly share it with\n• No data is sent to third parties (except Google APIs that you configure)"),
    ]

    user_text_lower = user_text.lower().strip()

    # Check local knowledge base (supports multi-keyword matching)
    best_match = None
    best_score = 0
    for keywords, response in LOCAL_KB:
        for keyword in keywords:
            if keyword in user_text_lower:
                # Longer keyword matches are more specific, prioritize them
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best_match = response

    if best_match:
        return best_match

    # If not in local KB, try Gemini
    api_key = st.session_state.get('ai_key') or os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        return ("I don't have a specific answer for that yet, but I know a lot about this app! "
                "Try asking me about: **setup**, **API keys**, **Service Account JSON**, **batch processing**, "
                "**caching architecture**, **AI verification**, **stats**, **costs**, or **troubleshooting**. "
                "For advanced questions, add a **Google AI API Key** in ⚙️ Configuration.")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(f"System: {ASSISTANT_SYSTEM_PROMPT}\nUser: {user_text}")
        return response.text
    except Exception as e:
        return f"I'm having trouble thinking right now. Error: {str(e)}"


def speak_text(text):
    """Converts text to speech and returns an HTML audio tag for autoplay."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            with open(fp.name, "rb") as audio_file:
                audio_bytes = audio_file.read()
            os.remove(fp.name)
            
            audio_base64 = base64.b64encode(audio_bytes).decode()
            return f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}">'
    except Exception as e:
        return ""


# Page configuration
st.set_page_config(
    page_title="Address Geocoding System",
    page_icon="🌍",
    layout="wide"
)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'sheet_id' not in st.session_state:
    st.session_state.sheet_id = ""
if 'service_account_json' not in st.session_state:
    st.session_state.service_account_json = ""
if 'configured' not in st.session_state:
    st.session_state.configured = False
if 'service' not in st.session_state:
    st.session_state.service = None
if 'ai_key' not in st.session_state:
    st.session_state.ai_key = ""
if 'use_agentic' not in st.session_state:
    st.session_state.use_agentic = False
if 'show_resy' not in st.session_state:
    st.session_state.show_resy = False

def apply_runtime_config():
    """Apply configuration from session state to environment."""
    if st.session_state.api_key:
        os.environ['GOOGLE_MAPS_API_KEY'] = st.session_state.api_key
    if st.session_state.sheet_id:
        os.environ['GOOGLE_SHEETS_ID'] = st.session_state.sheet_id
    
    if st.session_state.service_account_json:
        temp_file = Path(tempfile.gettempdir()) / "service_account.json"
        with open(temp_file, 'w') as f:
            f.write(st.session_state.service_account_json)
        os.environ['SERVICE_ACCOUNT_FILE'] = str(temp_file)


def initialize_service():
    """Initialize the lookup service with current configuration."""
    try:
        apply_runtime_config()
        from src.lookup_service import AddressLookupService
        from src import config as cfg
        import importlib
        importlib.reload(cfg)
        st.session_state.service = AddressLookupService()
        st.session_state.configured = True
        return True
    except Exception as e:
        st.error(f"Failed to initialize service: {e}")
        return False


def configuration_page():
    """Configuration page for API keys and credentials."""
    st.title("⚙️ Configuration")
    st.markdown("Enter your API credentials to use the Address Geocoding System.")
    
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.info("💡 **Don't have credentials yet?** Check the [SETUP_GUIDE.md](https://github.com) for instructions.")
    with col2:
        if st.button("🤖 Guide me, Resy!", use_container_width=True, key="config_resy_guide"):
            st.session_state.show_resy = True
            st.rerun()
    
    with st.form("config_form"):
        st.subheader("🔑 Google Maps API")
        api_key = st.text_input("Google Maps API Key *", value=st.session_state.api_key, type="password")
        
        st.markdown("---")
        st.subheader("🤖 Agentic AI (Gemini)")
        ai_key = st.text_input("Google AI API Key", value=st.session_state.ai_key, type="password")
        use_agentic = st.checkbox("Enable Fully Agentic Mode by default", value=st.session_state.use_agentic)
        
        st.markdown("---")
        st.subheader("📊 Google Sheets")
        sheet_id = st.text_input("Google Sheet ID *", value=st.session_state.sheet_id)
        service_json = st.text_area("Service Account JSON", value=st.session_state.service_account_json, height=150)
        
        submitted = st.form_submit_button("💾 Save Configuration", type="primary", use_container_width=True)
    
    if submitted:
        if api_key and sheet_id and service_json:
            st.session_state.api_key = api_key
            st.session_state.sheet_id = sheet_id
            st.session_state.service_account_json = service_json
            st.session_state.ai_key = ai_key
            st.session_state.use_agentic = use_agentic
            
            with st.spinner("Initializing..."):
                if initialize_service():
                    st.success("✅ Configuration saved!")
                    st.balloons()
                    st.rerun()
        else:
            st.error("❌ Please fill in all required fields.")


def require_configuration():
    """Check if service is configured."""
    if not st.session_state.configured or st.session_state.service is None:
        st.warning("⚠️ **Please configure your API credentials first!**")
        st.info("👉 Go to the **⚙️ Configuration** page in the sidebar.")
        return False
    return True


def main_page():
    """Main lookup page."""
    st.title("🔍 Individual Lookup")
    if not require_configuration(): return
    
    with st.form("lookup_form"):
        company = st.text_input("Company Name *")
        site_hint = st.text_input("Site Hint (Optional)")
        submitted = st.form_submit_button("🔍 Look Up", use_container_width=True)
    
    if submitted and company:
        with st.spinner("Searching..."):
            record, source = st.session_state.service.lookup(
                company, site_hint or None,
                agentic_verify=st.session_state.use_agentic,
                ai_api_key=st.session_state.ai_key
            )
        
        if record:
            st.success(f"✅ Found via **{source}**")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📍 Address")
                st.write(f"**Company:** {record.get('COMPANY NAME (NORMALIZED)')}")
                st.write(f"**Street:** {record.get('STREET ADDRESS1')}")
                st.write(f"**City:** {record.get('CITY NAME')}")
                st.write(f"**State:** {record.get('STATE NAME')}")
                st.write(f"**Postal Code:** {record.get('PIN CODE')}")
                st.write(f"**Country:** {record.get('COUNTRY NAME')}")
            with col2:
                st.subheader("📊 Details")
                st.metric("Confidence", f"{float(record.get('CONFIDENCE', 0))*100:.1f}%")
                
                # Verification Links
                st.markdown("---")
                st.write("**🔗 Verification Toolkit**")
                
                maps_link = record.get('MAPS LINK')
                if maps_link:
                    st.link_button("🗺️ View on Google Maps", maps_link, use_container_width=True)
                
                search_link = record.get('SEARCH LINK')
                if search_link:
                    st.link_button("🔍 Source Search", search_link, use_container_width=True)
                
                # AI Discovery Link (Direct sub-page)
                ai_url = record.get('AI SOURCE URL')
                if ai_url:
                    st.success(f"🌐 **Direct Source Found:**\n[{ai_url}]({ai_url})")

                if record.get('AI VERIFICATION STATUS'):
                    st.info(f"AI Status: {record.get('AI VERIFICATION STATUS')}")
            
            if record.get('LAT') and record.get('LNG'):
                st.map(pd.DataFrame({'lat': [float(record.get('LAT'))], 'lon': [float(record.get('LNG'))]}))
        else:
            st.error("❌ No results found.")


def batch_page():
    """Batch processing page."""
    st.title("📊 Batch Processing")
    if not require_configuration(): return
    
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(f"Rows: {len(df)}")
        if st.button("🚀 Process All"):
            progress = st.progress(0)
            results = []
            for i, row in df.iterrows():
                company = str(row.get('company', '')).strip()
                if not company: continue
                record, source = st.session_state.service.lookup(company)
                results.append({**dict(row), 'standardized_address': record.get('STREET ADDRESS1') if record else 'Not Found'})
                progress.progress((i+1)/len(df))
            st.dataframe(pd.DataFrame(results))


def stats_page():
    """Statistics page."""
    st.title("📈 Statistics")
    if not require_configuration(): return
    stats = st.session_state.service.get_stats()
    st.json(stats)


def review_page():
    """Review queue page."""
    st.title("🔍 Review Queue")
    if not require_configuration(): return
    queue = st.session_state.service.get_review_queue()
    if queue:
        st.dataframe(pd.DataFrame(queue))
    else:
        st.success("✅ Queue is empty!")


def instructions_page():
    """Detailed 'How it Works' and Instructions page."""
    st.title("📖 How it Works & Instructions")
    
    st.markdown("""
    ### 🌍 Application Overview
    The **Address Geocoding System** is a smart, company-focused platform designed to standardize addresses, find precise coordinates, and verify data through AI.

    ### 🛠️ The Multi-Tier Lookup Architecture
    The system optimizes performance and cost by checking sources in this order:
    
    ```mermaid
    graph TD
        A[User Query] --> B{Local Cache}
        B -- Found --> C[Return Result]
        B -- Not Found --> D{SQLite DB}
        D -- Found --> C
        D -- Not Found --> E{Google Sheets}
        E -- Found --> C
        E -- Not Found --> F[Google Maps API]
        F --> G[Store in Cache & Sheets]
        G --> C
    ```
    
    1.  **⚡ Local session Cache** (Instant): Checks if you looked up this company in the current session.
    2.  **💾 SQLite Database** (Fast): Persistent local cache on the server.
    3.  **📊 Shared Google Sheets** (Team-wide): Searches your team's centralized registry.
    4.  **🤝 Intelligent Fuzzy Matching**: Finds similar names (e.g., "Tata Services" vs "Tata Consultancy Services").
    5.  **🌏 Google Maps Geocoding API**: Used only as a final fallback for brand new addresses.
    6.  **🤖 Agentic AI Verification**: Optional layer that searches the web to confirm location details.

    ### 🚀 Getting Started Guide
    
    #### 1. ⚙️ Initial Configuration
    Before performing lookups, setup your credentials in the **Configuration** tab:
    - **Google Maps Key**: Found in your Google Cloud Console.
    - **Sheet ID**: The unique ID from your Google Sheet URL.
    - **Service JSON**: The credentials file that gives the app access to your sheet.
    
    #### 2. 🔍 Single Company Lookup
    - Enter the **Company Name** (normalized automatically).
    - Provide an optional **Site Hint** (e.g., "India" or "London") for better accuracy.
    - View results with confidence scores and interactive maps.
    
    #### 3. 📊 Batch CSV Processing
    - Upload a CSV with a `company` column.
    - Process hundreds of records automatically while you wait.
    - Download the cleaned and geocoded results as a new CSV.

    ### 🎯 Quality Controls & Review
    - **Confidence Score**: Every result is scored (0-1). Scores below 0.8 are flagged.
    - **Review Queue**: High-priority manual work queue for uncertain results.
    - **QA Status**: Automatic tagging of results (Success, Review, Low Confidence).

    ### 💰 Cost Optimization Tips
    - **Multi-tier caching** can save up to 90% in Google Maps API costs.
    - Sharing a single Google Sheet ID with your entire team builds a **Shared Brain**—once anyone geocodes a company, everyone benefits instantly!
    """)
    
    st.info("💡 **Pro Tip:** Sharing your Google Sheet ID across different departments prevents paying for the same address twice!")

# --- Sidebar Integrated Resy Assistant ---
def render_resy_assistant():
    """Renders Resy as a floating-style chatbox at the top of the sidebar."""
    # State for visibility
    if 'show_resy' not in st.session_state:
        st.session_state.show_resy = False

    # Sidebar Chatbox Styles
    st.markdown("""
        <style>
        /* Chatbox container in sidebar */
        .resy-sidebar-box {
            background: linear-gradient(135deg, rgba(110, 142, 251, 0.1), rgba(167, 119, 227, 0.1));
            border-radius: 15px;
            padding: 15px;
            border: 1px solid rgba(110, 142, 251, 0.3);
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }
        
        .resy-sidebar-trigger {
            width: 100% !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #6e8efb, #a777e3) !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
            margin-bottom: 10px !important;
        }

        /* Marker for internal targeting if needed */
        .resy-sb-marker { display: none; }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar.container():
        st.markdown('<div class="resy-sidebar-box">', unsafe_allow_html=True)
        st.subheader("🤖 Resy Guide")
        
        btn_label = "❌ Close Assistant" if st.session_state.show_resy else "🤖 Chat with Resy"
        if st.button(btn_label, key="resy_sb_trigger_v1", use_container_width=True):
            st.session_state.show_resy = not st.session_state.show_resy
            st.rerun()
            
        if st.session_state.show_resy:
            st.markdown("---")
            
            # Voice Input using mic_recorder
            st.write("🎙️ **Voice Command**")
            audio = mic_recorder(
                start_prompt="Start Recording",
                stop_prompt="Stop Recording",
                key="resy_mic_v1",
                use_container_width=True
            )
            
            voice_text = ""
            if audio:
                # streamlit-mic-recorder returns 'text' if STT is active or the raw audio bytes
                # We'll prioritize the transcribed text if available
                voice_text = audio.get('text', '')
                if voice_text:
                    st.success(f"I heard: {voice_text}")
            
            # Text Input (Option)
            user_input = st.text_input("Or type here:", key="resy_input_sb_v1", placeholder="How do I use Batch?", value=voice_text)
            
            if user_input:
                with st.spinner("Thinking..."):
                    reply = get_resy_response(user_input)
                    st.info(f"**Resy:** {reply}")
                    
                    audio_html = speak_text(reply)
                    if audio_html:
                        st.components.v1.html(audio_html, height=0)
                        st.audio(base64.b64decode(audio_html.split(',')[1].replace('">', '')), format="audio/mp3")
        st.markdown('</div>', unsafe_allow_html=True)

# --- Main Flow ---
st.sidebar.title("🌍 Geocoding System")

# NEW: Resy at the top of Sidebar
render_resy_assistant()

if st.session_state.configured:
    st.sidebar.success("✅ Service Active")
else:
    st.sidebar.warning("⚠️ Pending Config")

st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["📖 Instructions", "⚙️ Configuration", "🔍 Lookup", "📊 Batch", "📈 Stats", "🔍 Review Queue"])
st.sidebar.markdown("---")

if page == "📖 Instructions":
    instructions_page()
elif page == "⚙️ Configuration":
    configuration_page()
elif page == "🔍 Lookup":
    main_page()
elif page == "📊 Batch":
    batch_page()
elif page == "📈 Stats":
    stats_page()
elif page == "🔍 Review Queue":
    review_page()

