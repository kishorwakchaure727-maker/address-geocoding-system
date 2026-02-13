import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import tempfile
import base64
from pathlib import Path

# Title and Layout
st.set_page_config(page_title="LuxeStore Assistant Prototype", page_icon="🤖")

st.title("🤖 LuxeStore Voice AI Assistant")
st.markdown("""
This is a prototype of an **AI Voice Guide**. It demonstrates how an AI assistant can talk to users verbally 
to explain the app, its purpose, and instructions.
""")

# --- Configuration (Using session state for this demo) ---
with st.sidebar:
    st.header("⚙️ Assistant Settings")
    api_key = st.text_input("Enter Google AI API Key", type="password")
    voice_speed = st.slider("Voice Speed", 0.5, 2.0, 1.0)
    
    if api_key:
        genai.configure(api_key=api_key)

# --- AI Persona Definition ---
SYSTEM_PROMPT = """
You are "LuxeStore Assistant", a high-end, friendly, and professional voice-enabled guide for an 
Address Geocoding & Verification System.

Your purpose is to explain the app to users verbally.
Key facts about the app:
1. It standardizes company addresses (STREET ADDRESS1, CITY NAME, PIN CODE, etc.).
2. It uses multi-tier caching (Session, SQLite, Google Sheets) to save costs.
3. It has a "Fully Agentic Mode" using Gemini AI to verify addresses by searching the web.
4. It features a batch processing tool for CSV files and a manual Review Queue.

Keep your responses VERY CONCISE (max 2-3 sentences) because you are being converted to voice.
Sound enthusiastic, premium, and helpful. Always greet the user warmly if it's the start of the conversation.
"""

def get_ai_response(user_text):
    if not api_key:
        return "Please enter your API Key in the sidebar to hear me talk!"
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(f"System: {SYSTEM_PROMPT}\nUser: {user_text}")
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def speak_text(text):
    """Converts text to speech and returns an HTML audio tag."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            
            # Read back for base64 encoding to play in Streamlit
            with open(fp.name, "rb") as audio_file:
                audio_bytes = audio_file.read()
            
            # Clean up temp file
            os.remove(fp.name)
            
            # Encode for HTML
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_tag = f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}">'
            return audio_tag
    except Exception as e:
        st.error(f"TTS Error: {e}")
        return ""

# --- UI interaction ---
st.info("💡 **Try asking:** 'What is this app for?' or 'How do I use the Agentic mode?'")

user_input = st.text_input("Ask me anything about the app:", key="user_input")

if st.button("🗣️ Get AI Voice Reply") or user_input:
    if user_input:
        with st.spinner("LuxeStore Assistant is thinking..."):
            reply = get_ai_response(user_input)
            
        st.subheader("Assistant Reply:")
        st.write(reply)
        
        # Audio generation and playback
        audio_html = speak_text(reply)
        if audio_html:
            # We use st.components.v1.html to allow autoplay
            st.components.v1.html(audio_html, height=0)
            st.audio(base64.b64decode(audio_html.split(',')[1].replace('">', '')), format="audio/mp3")
    else:
        st.warning("Please type something first!")

# --- Visual Demo ---
st.markdown("---")
st.subheader("How this helps users:")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("🚶 **Onboarding**")
    st.caption("Verbal walkthrough for first-time users.")
with col2:
    st.write("🔍 **Instant FAQs**")
    st.caption("Ask questions hands-free while working.")
with col3:
    st.write("✨ **Premium Feel**")
    st.caption("Modern brand experience like Google Assistant.")
