"""
Voice‑only companion for ApnaYaar AI.

Features:
- Sidebar with mode selector (unchanged).
- Central hero banner.
- Push‑to‑talk microphone using Streamlit's native `st.audio_input`.
- After recording: STT → Gemini → TTS → automatic audio playback.
- No chat bubbles or visible transcript are rendered.
- Session state preserves conversation history for context.
- End Conversation button clears state.

All secrets are loaded from `.env` via `python‑dotenv`.
"""

import streamlit as st
import datetime
from pathlib import Path
import os
import requests
from dotenv import load_dotenv
from gemini_service import generate_apna_yaar_response

# ---------------------------------------------------------------------------
# Helper: load environment variables (same logic as config.py)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

_GNANI_API_KEY = os.getenv("GNANI_API_KEY", "").strip()
_PLACEHOLDERS = {"", "your_gnani_api_key_here", "your_key_here"}
GNANI_API_KEY = "" if _GNANI_API_KEY in _PLACEHOLDERS else _GNANI_API_KEY

if not GNANI_API_KEY:
    st.error("GNANI_API_KEY not configured in .env – cannot run voice companion.")
    st.stop()

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "Just Listen"
if "mic_active" not in st.session_state:
    st.session_state.mic_active = True
if "audio_ready" not in st.session_state:
    st.session_state.audio_ready = False
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# ---------------------------------------------------------------------------
# UI components (sidebar, hero banner)
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">🤗 ApnaYaar AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-tagline">“Bol lo. Main sun raha hoon.”</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### 🎭 Conversation Mode")
        selected = st.radio(
            label="How would you like ApnaYaar to respond?",
            options=["Just Listen", "Let's Talk", "Help Me Think"],
            index=["Just Listen", "Let's Talk", "Help Me Think"].index(st.session_state.current_mode),
            format_func=lambda m: m,
        )
        if selected != st.session_state.current_mode:
            st.session_state.current_mode = selected
            st.rerun()
        st.divider()
        st.markdown("### ⚙️ Session")
        st.write(f"💬 Messages stored: **{len(st.session_state.messages)}**")
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            for key in ["messages", "audio_bytes", "audio_ready", "mic_active"]:
                st.session_state.pop(key, None)
            st.success("Conversation cleared!")
            st.rerun()
        st.divider()
        st.caption("💛 ApnaYaar AI – a warm listening companion")

def render_hero_banner():
    st.markdown(
        f"""
        <div class='hero-banner'>
            <div class='hero-title-row'>
                <h1 class='hero-title'>🤗 ApnaYaar AI</h1>
                <div class='mode-indicator'>{st.session_state.current_mode} Mode</div>
            </div>
            <div class='hero-tagline'>“Bol lo. Main sun raha hoon.”</div>
            <p class='hero-subtitle'>A patient, warm, and non‑judgmental space where you can speak your heart out.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# STT helper (uses same endpoint as test_gnani_stt.py)
# ---------------------------------------------------------------------------
def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    endpoint = "https://api.vachana.ai/stt/v3"
    headers = {"X-API-Key-ID": GNANI_API_KEY}
    data = {"language_code": "hi-IN"}
    files = {"audio_file": ("recording.wav", audio_bytes)}
    resp = requests.post(endpoint, headers=headers, data=data, files=files, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    transcription = (
        result.get("transcript")
        or result.get("transcription")
        or result.get("text")
        or result.get("data")
    )
    if not transcription:
        raise RuntimeError("Gnani STT returned no transcription")
    return transcription

# ---------------------------------------------------------------------------
# TTS helper (uses verified voice "Avinash")
# ---------------------------------------------------------------------------
def synthesize_speech(text: str) -> bytes:
    payload = {
        "text": text,
        "voice": "Avinash",
        "model": "timbre-v3.0",
        "language": "hi-IN",
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 48000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav",
        },
    }
    headers = {"X-API-Key-ID": GNANI_API_KEY, "Content-Type": "application/json"}
    endpoint = "https://api.vachana.ai/api/v1/tts/inference"
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.content

# ---------------------------------------------------------------------------
# Playback rendering – ensures audio plays only once per response
# ---------------------------------------------------------------------------
def render_playback():
    if st.session_state.get("audio_ready") and st.session_state.get("audio_bytes"):
        st.audio(st.session_state["audio_bytes"], format="audio/wav", autoplay=True)
        # Reset flags so the same clip is not replayed on reruns
        st.session_state["audio_ready"] = False
        st.session_state["mic_active"] = True

# ---------------------------------------------------------------------------
# Main application flow
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="ApnaYaar AI • Voice Companion", page_icon="💛", layout="wide")
    # Basic light styling – reuse existing CSS from app.py for visual consistency
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        html, body, [class*='css'] {font-family: 'Plus Jakarta Sans', sans-serif;}
        .stApp {background-color: #FAF6F0;}
        .hero-banner {background: linear-gradient(135deg, #FFF9F3 0%, #FDF1E6 100%);border:1px solid #F2DEC9;border-radius:18px;padding:24px 28px;margin-bottom:24px;box-shadow:0 4px 16px rgba(217,119,87,0.06);}
        .hero-title {font-size:2.1rem;font-weight:700;color:#2D3142;}
        .hero-tagline {font-size:1.15rem;color:#C85A32;font-style:italic;}
        .hero-subtitle {font-size:0.98rem;color:#5C5E6E;}
        .mode-indicator {background:#FFF;padding:7px 16px;border:1px solid #E07A5F;border-radius:30px;font-weight:600;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_sidebar()
    render_hero_banner()

    # End Conversation button – placed below hero for visibility
    if st.button("🛑 End Conversation", use_container_width=True):
        for key in ["messages", "audio_bytes", "audio_ready", "mic_active"]:
            st.session_state.pop(key, None)
        st.success("Conversation cleared. Ready to start again.")
        st.rerun()
        return

    # Microphone recorder (push‑to‑talk). Streamlit's audio_input returns UploadedFile.
    if st.session_state.get("mic_active", True):
        audio_file = st.audio_input("🎤 Press to record (push‑to‑talk)")
        if audio_file is not None:
            # Disable further recordings while processing
            st.session_state.mic_active = False
            audio_bytes = audio_file.read()
            try:
                # 1️⃣ STT
                user_text = transcribe_audio_bytes(audio_bytes)
                # 2️⃣ Gemini response (passes full history for context)
                reply = generate_apna_yaar_response(
                    user_text=user_text,
                    mode=st.session_state.current_mode,
                    conversation_history=st.session_state.messages,
                )
                # Store user and assistant messages for future context
                st.session_state.messages.append({"role": "user", "content": user_text, "time": datetime.datetime.now().strftime("%I:%M %p"), "mode": st.session_state.current_mode})
                st.session_state.messages.append({"role": "assistant", "content": reply, "time": datetime.datetime.now().strftime("%I:%M %p"), "mode": st.session_state.current_mode})
                # 3️⃣ TTS
                audio_reply = synthesize_speech(reply)
                st.session_state.audio_bytes = audio_reply
                st.session_state.audio_ready = True
            except Exception as exc:
                st.error(f"Conversation error: {exc}")
                st.session_state.mic_active = True
            # Trigger a rerun so playback block is rendered
            st.rerun()
    else:
        st.info("Processing… please wait before recording again.")

    # Render audio playback if a reply is ready
    render_playback()

if __name__ == "__main__":
    main()
