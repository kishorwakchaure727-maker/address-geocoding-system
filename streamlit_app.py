"""
Streamlit web interface for address geocoding system.
Users can enter API keys directly in the UI.
"""
print("DEBUG: Streamlit app starting...")
import sys
import os
from pathlib import Path

print(f"DEBUG: Current working directory: {os.getcwd()}")
print(f"DEBUG: Python path: {sys.path}")

# Add parent directory to path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)
print(f"DEBUG: Added {project_root} to sys.path")

try:
    import streamlit as st
    print("DEBUG: Streamlit imported successfully")
except Exception as e:
    print(f"DEBUG: Failed to import streamlit: {e}")

try:
    from src import config as cfg
    print("DEBUG: src.config imported successfully")
except Exception as e:
    print(f"DEBUG: Failed to import src.config: {e}")

import pandas as pd
from datetime import datetime
import tempfile
import json


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


def apply_runtime_config():
    """Apply configuration from session state to environment."""
    if st.session_state.api_key:
        os.environ['GOOGLE_MAPS_API_KEY'] = st.session_state.api_key
    if st.session_state.sheet_id:
        os.environ['GOOGLE_SHEETS_ID'] = st.session_state.sheet_id
    
    # Save service account JSON to temp file if provided
    if st.session_state.service_account_json:
        temp_file = Path(tempfile.gettempdir()) / "service_account.json"
        with open(temp_file, 'w') as f:
            f.write(st.session_state.service_account_json)
        os.environ['SERVICE_ACCOUNT_FILE'] = str(temp_file)


def initialize_service():
    """Initialize the lookup service with current configuration."""
    try:
        apply_runtime_config()
        
        # Import after setting environment variables
        from src.lookup_service import AddressLookupService
        from src import config as cfg
        
        # Reload config to pick up new env vars
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
    
    st.info("💡 **Don't have credentials yet?** Check the [SETUP_GUIDE.md](https://github.com) for instructions on getting Google Maps API key and setting up Google Sheets.")
    
    with st.form("config_form"):
        st.subheader("🔑 Google Maps API")
        api_key = st.text_input(
            "Google Maps API Key *",
            value=st.session_state.api_key,
            type="password",
            help="Get this from Google Cloud Console > APIs & Services > Credentials"
        )
        
        st.markdown("---")
        st.subheader("📊 Google Sheets")
        
        sheet_id = st.text_input(
            "Google Sheet ID *",
            value=st.session_state.sheet_id,
            help="From the Sheet URL: https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit"
        )
        
        st.write("**Service Account JSON**")
        st.caption("Upload or paste the service account JSON file content")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Upload service_account.json",
                type=['json'],
                help="Download from Google Cloud Console > IAM & Admin > Service Accounts"
            )
        
        with col2:
            json_text = st.text_area(
                "Or paste JSON content",
                value=st.session_state.service_account_json[:100] + "..." if len(st.session_state.service_account_json) > 100 else st.session_state.service_account_json,
                height=150,
                help="Paste the entire content of your service_account.json file"
            )
        
        submitted = st.form_submit_button("💾 Save Configuration", type="primary", use_container_width=True)
    
    if submitted:
        # Validate inputs
        errors = []
        
        if not api_key:
            errors.append("Google Maps API Key is required")
        if not sheet_id:
            errors.append("Google Sheet ID is required")
        
        # Get JSON content
        service_json = ""
        if uploaded_file:
            service_json = uploaded_file.read().decode('utf-8')
        elif json_text:
            service_json = json_text
        
        if not service_json:
            errors.append("Service Account JSON is required")
        else:
            # Validate JSON
            try:
                json.loads(service_json)
            except json.JSONDecodeError:
                errors.append("Invalid JSON format for Service Account")
        
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Save to session state
            st.session_state.api_key = api_key
            st.session_state.sheet_id = sheet_id
            st.session_state.service_account_json = service_json
            
            # Initialize service
            with st.spinner("Initializing service..."):
                if initialize_service():
                    st.success("✅ Configuration saved and service initialized successfully!")
                    st.balloons()
                    st.rerun()
    
    # Show current status
    st.markdown("---")
    st.subheader("📋 Current Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.api_key:
            st.success("✅ API Key set")
        else:
            st.warning("⚠️ API Key missing")
    
    with col2:
        if st.session_state.sheet_id:
            st.success("✅ Sheet ID set")
        else:
            st.warning("⚠️ Sheet ID missing")
    
    with col3:
        if st.session_state.service_account_json:
            st.success("✅ Service Account set")
        else:
            st.warning("⚠️ Service Account missing")
    
    if st.session_state.configured:
        st.success("🎉 **System is configured and ready to use!**")
        
        # Test connections
        st.markdown("---")
        st.subheader("🔍 Test Connections")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Test Google Maps API", use_container_width=True):
                with st.spinner("Testing..."):
                    try:
                        from src.geocode import GeocodingService
                        geocoder = GeocodingService()
                        results = geocoder.geocode_company("Google", "Mountain View, CA")
                        if results:
                            st.success("✅ Google Maps API working!")
                        else:
                            st.error("❌ No results returned")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        with col2:
            if st.button("Test Google Sheets", use_container_width=True):
                with st.spinner("Testing..."):
                    try:
                        from src.storage import SheetsStorage
                        storage = SheetsStorage()
                        stats = storage.get_stats()
                        st.success(f"✅ Google Sheets working! ({stats['total_records']} records)")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")


def require_configuration():
    """Check if service is configured, show warning if not."""
    if not st.session_state.configured or st.session_state.service is None:
        st.warning("⚠️ **Please configure your API credentials first!**")
        st.info("👉 Go to the **⚙️ Configuration** page in the sidebar to enter your API keys.")
        
        with st.expander("Quick Setup Guide"):
            st.markdown("""
            ### What you need:
            
            1. **Google Maps API Key**
               - Go to [Google Cloud Console](https://console.cloud.google.com/)
               - Enable "Geocoding API"
               - Create API Key
            
            2. **Google Sheet ID**
               - Create a new Google Sheet
               - Copy the ID from the URL
            
            3. **Service Account JSON**
               - Create service account in Google Cloud
               - Download JSON key file
               - Share your Sheet with the service account email
            
            📖 **Full instructions:** See SETUP_GUIDE.md in project folder
            """)
        
        return False
    return True


def main_page():
    """Main lookup page."""
    st.title("🌍 Company Address Geocoding System")
    st.markdown("Get standardized addresses for companies with automatic caching and quality controls.")
    
    if not require_configuration():
        return
    
    # Lookup form
    with st.form("lookup_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            company = st.text_input(
                "Company Name *",
                placeholder="e.g., Tata Consultancy Services"
            )
        
        with col2:
            site_hint = st.text_input(
                "Site Hint (Optional)",
                placeholder="e.g., Pune, India"
            )
        
        submitted = st.form_submit_button("🔍 Look Up Address", use_container_width=True)
    
    if submitted and company:
        with st.spinner("Searching..."):
            record, source = st.session_state.service.lookup(company, site_hint or None)
        
        if record:
            # Source badge
            source_colors = {
                'cache': '🟢',
                'storage': '🔵',
                'storage_fuzzy': '🟣',
                'geocoded': '🟡',
            }
            
            st.success(f"{source_colors.get(source, '⚪')} Found! Source: **{source}**")
            
            # Display result
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📍 Address")
                st.write(f"**Company:** {record.get('company_normalized')}")
                st.write(f"**Street:** {record.get('street_1')}")
                if record.get('street_2'):
                    st.write(f"**Street 2:** {record.get('street_2')}")
                st.write(f"**City:** {record.get('city')}")
                st.write(f"**State/Region:** {record.get('state_region')}")
                st.write(f"**Postal Code:** {record.get('postal_code')}")
                st.write(f"**Country:** {record.get('country')}")
            
            with col2:
                st.subheader("📊 Details")
                
                # Confidence meter
                confidence = float(record.get('confidence', 0))
                confidence_pct = confidence * 100
                
                if confidence >= config.CONFIDENCE_THRESHOLD:
                    st.metric("Confidence", f"{confidence_pct:.1f}%", "✓ High")
                else:
                    st.metric("Confidence", f"{confidence_pct:.1f}%", "⚠️ Low - Needs Review")
                
                st.write(f"**QA Status:** {record.get('qa_status')}")
                st.write(f"**Coordinates:** {record.get('lat')}, {record.get('lng')}")
                st.write(f"**Place ID:** {record.get('geocoder_place_id', 'N/A')}")
            
            # Map
            if record.get('lat') and record.get('lng'):
                st.subheader("🗺️ Map")
                map_df = pd.DataFrame({
                    'lat': [float(record.get('lat'))],
                    'lon': [float(record.get('lng'))]
                })
                st.map(map_df, zoom=12)
            
            # Raw data (expandable)
            with st.expander("View Raw Data"):
                st.json(record)
        
        else:
            st.error(f"❌ No results found for '{company}' ({source})")
    
    elif submitted:
        st.warning("⚠️ Please enter a company name")


def batch_page():
    """Batch processing page."""
    st.title("📊 Batch Processing")
    st.markdown("Upload a CSV file with company names to process multiple lookups at once.")
    
    if not require_configuration():
        return
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=['csv'],
        help="CSV should have 'company' column and optionally 'site_hint' column"
    )
    
    if uploaded_file is not None:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        st.write(f"**Uploaded:** {len(df)} rows")
        st.dataframe(df.head(), use_container_width=True)
        
        if st.button("🚀 Process All", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            
            for i, row in df.iterrows():
                company = str(row.get('company', '')).strip()
                site_hint = str(row.get('site_hint', '')).strip() if 'site_hint' in row else None
                
                if not company:
                    continue
                
                status_text.text(f"Processing {i+1}/{len(df)}: {company}")
                
                record, source = st.session_state.service.lookup(company, site_hint)
                
                if record:
                    results.append({
                        **dict(row),
                        'normalized_company': record.get('company_normalized'),
                        'street_1': record.get('street_1'),
                        'city': record.get('city'),
                        'state_region': record.get('state_region'),
                        'postal_code': record.get('postal_code'),
                        'country': record.get('country'),
                        'lat': record.get('lat'),
                        'lng': record.get('lng'),
                        'confidence': record.get('confidence'),
                        'qa_status': record.get('qa_status'),
                        'source': source,
                    })
                else:
                    results.append({
                        **dict(row),
                        'error': 'not_found',
                        'source': source,
                    })
                
                progress_bar.progress((i + 1) / len(df))
            
            status_text.text("✓ Processing complete!")
            
            # Show results
            results_df = pd.DataFrame(results)
            st.subheader("Results")
            st.dataframe(results_df, use_container_width=True)
            
            # Download button
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Results CSV",
                data=csv,
                file_name=f"geocoding_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


def stats_page():
    """Statistics page."""
    st.title("📈 Statistics")
    
    if not require_configuration():
        return
    
    stats = st.session_state.service.get_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 Storage (Google Sheets)")
        storage_stats = stats['storage']
        
        # Metrics
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Total Records", storage_stats.get('total_records', 0))
        metric_col2.metric("Auto Approved", storage_stats.get('auto_approved', 0))
        metric_col3.metric("Needs Review", storage_stats.get('needs_review', 0))
        
        # Sources chart
        if storage_stats.get('sources'):
            st.write("**Sources:**")
            sources_df = pd.DataFrame([
                {'Source': k, 'Count': v}
                for k, v in storage_stats['sources'].items()
            ])
            st.bar_chart(sources_df.set_index('Source'))
    
    with col2:
        st.subheader("💾 Cache")
        cache_stats = stats['cache']
        
        st.write(f"**Type:** {cache_stats.get('cache_type')}")
        st.write(f"**Memory Entries:** {cache_stats.get('memory_entries', 0)}")
        st.write(f"**SQLite Entries:** {cache_stats.get('sqlite_entries', 0)}")
        st.write(f"**TTL:** {cache_stats.get('ttl_hours', 0)} hours")
        st.write(f"**Max Size:** {cache_stats.get('max_size', 0)}")


def review_page():
    """Review queue page."""
    st.title("🔍 Review Queue")
    st.markdown("Records with low confidence scores that need manual review.")
    
    if not require_configuration():
        return
    
    queue = st.session_state.service.get_review_queue()
    
    if not queue:
        st.success("✓ No records need review!")
        return
    
    st.write(f"**{len(queue)} records** need review:")
    
    # Convert to DataFrame
    df = pd.DataFrame(queue)
    
    # Display as table
    st.dataframe(
        df[[
            'company_normalized', 'city', 'country', 
            'confidence', 'qa_status', 'notes'
        ]],
        use_container_width=True
    )
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download Review Queue CSV",
        data=csv,
        file_name=f"review_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def instructions_page():
    """Instructions and 'How it Works' page."""
    st.title("📖 How it Works & Instructions")
    
    st.markdown("""
    ### 🌟 Application Overview
    The **Address Geocoding System** is a powerful tool designed to standardize company addresses and find their precise geographic coordinates. It uses multiple layers of searching and caching to ensure high accuracy while minimizing costs.

    ### 🛠️ How It Works
    The system follows a multi-tier lookup process to find addresses:
    
    1.  **⚡ Local Cache**: First, it checks the immediate browser session and local SQLite database.
    2.  **📊 Google Sheets Registry**: If not in cache, it searches your team's Google Sheet for previously geocoded results.
    3.  **🤝 Fuzzy Matching**: It uses advanced matching to find similar names even if they aren't exact matches.
    4.  **🌏 Google Maps API**: If the address is totally new, it calls the Google Maps Geocoding API.
    5.  **💾 Automatic Saving**: Once found via API, the standardized address is saved back to Google Sheets and your local cache for future use.

    ### 🚀 Getting Started
    
    #### 1. ⚙️ Configuration
    Before you start, you need to provide your credentials in the **Configuration** tab:
    - **Google Maps API Key**: For looking up new addresses.
    - **Google Sheet ID**: Where all geocoded data is stored and shared.
    - **Service Account JSON**: Credentials to allow the app to write to your Google Sheet.
    
    #### 2. 🔍 Individual Lookup
    Go to the **Lookup** tab to find a single company's address.
    - Enter the **Company Name**.
    - (Optional) Provide a **Site Hint** (like "London" or "NYC") to help the system narrow down the correct branch.
    
    #### 3. 📊 Batch Processing
    Need to process many addresses at once?
    - Upload a CSV file with a `company` column.
    - Click **Process All**.
    - Download the completed results as a new CSV.

    ### 🎯 Quality & Review
    - **Confidence Score**: Every result gets a score. Above 80% is usually perfect.
    - **Review Queue**: Anything with low confidence is sent to the **Review Queue** for manual verification.
    
    ### 💰 Cost Optimization
    By using this system, you save money!
    - **40,000 Free Requests**: Google gives you a large free tier every month.
    - **Don't pay twice**: Because we save results to Google Sheets, your team never pays to geocode the same company twice.
    """)
    
    st.info("💡 **Pro Tip:** Sharing your Google Sheet with team members allows everyone to benefit from shared caching!")


# Sidebar navigation
st.sidebar.title("🌍 Address Geocoding")

# Configuration status indicator
if st.session_state.configured:
    st.sidebar.success("✅ Configured")
else:
    st.sidebar.warning("⚠️ Not Configured")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📖 Instructions", "⚙️ Configuration", "🔍 Lookup", "📊 Batch", "📈 Stats", "🔍 Review Queue"]
)

st.sidebar.markdown("---")

# Quick stats in sidebar if configured
if st.session_state.configured and st.session_state.service:
    try:
        from src.storage import get_cache
        cache = get_cache()
        cache_stats = cache.get_stats()
        
        st.sidebar.caption("**Quick Stats**")
        st.sidebar.caption(f"💾 Cache: {cache_stats.get('memory_entries', 0)} entries")
    except:
        pass

# Route to pages
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

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Address Geocoding System v1.0")
st.sidebar.caption("Built with ❤️ using Streamlit")
