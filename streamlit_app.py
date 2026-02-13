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
    """Generate a response from Gemini for Resy, with local fallback for onboarding."""
    # Local Knowledge Base for Onboarding (No API Key needed)
    LOCAL_KB = {
        "lookup": "The **Individual Lookup** page allows you to find the address of a single company. Just enter the name and an optional site hint (like 'India') to get started!",
        "batch": "The **Batch Processing** page is perfect for processing hundreds of addresses at once. Just upload a CSV with a 'company' column and download the results!",
        "config": "In the **Configuration** tab, you can add your Google Maps and AI API keys to unlock the full power of the system, including AI verification and shared Google Sheets.",
        "stats": "The **Stats** page shows you how many addresses have been found and how much money you've saved using the multi-tier caching system!",
        "instructions": "The **Instructions** page contains a detailed technical overview and a diagram of our multi-tier lookup architecture.",
        "hello": "Hello! I'm Resy, your AI guide. I can help you navigate the app or answer questions about our geocoding features. How can I assist you today?",
        "hi": "Hi there! I'm Resy. Need help with lookups, batch processing, or configuration? Just ask!",
        "who are you": "I'm Resy, the intelligent assistant for this Address Geocoding System. I was designed to make your data standardization journey smooth and easy!"
    }
    
    user_text_lower = user_text.lower()
    
    # Check local knowledge first for onboarding
    for key in LOCAL_KB:
        if key in user_text_lower:
            return LOCAL_KB[key]
            
    # If not in local KB, try Gemini
    api_key = st.session_state.get('ai_key') or os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        return "I can answer basic questions about the app right now, but for advanced AI verification, please add a **Google AI API Key** in the Configuration tab! 🔑"
    
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
            user_input = st.text_input("Ask me anything:", key="resy_input_sb_v1", placeholder="How do I use Batch?")
            
            if user_input:
                with st.spinner("Thinking..."):
                    reply = get_resy_response(user_input)
                    st.info(f"**Resy:** {reply}")
                    
                    audio_html = speak_text(reply)
                    if audio_html:
                        st.components.v1.html(audio_html, height=0)
                        st.audio(base64.b64decode(audio_html.split(',')[1].replace('">', '')), format="audio/mp3")
        st.markdown('</div>', unsafe_allow_html=True)
