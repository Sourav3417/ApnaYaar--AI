"""
ApnaYaar AI - Your Warm AI Companion
====================================
Tagline: "Bol lo. Main sun raha hoon."
Concept: A patient, warm, and non-judgmental AI friend for anyone who feels lonely,
         overwhelmed, or simply wants someone to talk to.

Version: 1.1.0
"""

import streamlit as st
import datetime
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from gemini_service import generate_apna_yaar_response
from companion_ui import (
    inject_companion_css,
    render_header,
    render_orb,
    render_state_callout,
    render_mode_selector,
    render_control_bar,
    render_footer,
)

# ---------------------------------------------------------------------------
# Load Gnani API key from .env (same logic as config.py)
# ---------------------------------------------------------------------------
_BASE_DIR = Path(__file__).resolve().parent
_ENV_PATH = _BASE_DIR / ".env"
if _ENV_PATH.exists():
    load_dotenv(dotenv_path=_ENV_PATH)
else:
    load_dotenv()

_GNANI_RAW = os.getenv("GNANI_API_KEY", "").strip()
_GNANI_PLACEHOLDERS = {"", "your_gnani_api_key_here", "your_key_here"}
GNANI_API_KEY = "" if _GNANI_RAW in _GNANI_PLACEHOLDERS else _GNANI_RAW

# ==============================================================================
# 1. PAGE CONFIGURATION & STYLING
# ==============================================================================

def setup_page():
    """Configures Streamlit page settings, browser title, and layout."""
    st.set_page_config(
        page_title="ApnaYaar AI • Your Voice Companion",
        page_icon="🌌",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

def inject_custom_styles():
    """Legacy helper maintained for compatibility - styling is now handled by companion.css."""
    pass

# ==============================================================================
# 2. SESSION STATE MANAGEMENT
# ==============================================================================

def initialize_session_state():
    """Initializes message history and session state if not already set."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Namaste! 🙏 I'm **ApnaYaar**.\n\n"
                    "Whether your day felt heavy, you have good news to celebrate, "
                    "or you just want someone who listens patiently—I'm right here with you. "
                    "Bol lo. Main sun raha hoon."
                ),
                "time": datetime.datetime.now().strftime("%I:%M %p"),
                "mode": "Just Listen"
            }
        ]

    if "current_mode" not in st.session_state:
        st.session_state.current_mode = "Just Listen"
    if "apnayaar_mode" not in st.session_state:
        st.session_state.apnayaar_mode = st.session_state.current_mode

    if "used_reply_indices" not in st.session_state:
        st.session_state.used_reply_indices = set()

    # Flags for voice-only flow
    if "mic_active" not in st.session_state:
        st.session_state.mic_active = True
    if "audio_ready" not in st.session_state:
        st.session_state.audio_ready = False
    if "audio_bytes" not in st.session_state:
        st.session_state.audio_bytes = None
    if "voice_speed" not in st.session_state:
        st.session_state.voice_speed = 1.0
    if "companion_state" not in st.session_state:
        st.session_state.companion_state = "idle"
    if "is_playing" not in st.session_state:
        st.session_state.is_playing = False

# ==============================================================================
# 3. CONVERSATION MODES & NATURAL RESPONSE ENGINE
# ==============================================================================

MODES = {
    "Just Listen": {
        "icon": "👂",
        "tagline": "Pure Empathetic Listening",
        "description": "ApnaYaar sits quietly with you, validates how you feel, and offers unconditional warmth. No unsolicited advice, lectures, or quick fixes.",
        "badge_color": "#E07A5F"
    },
    "Let's Talk": {
        "icon": "💬",
        "tagline": "Warm Casual Conversation",
        "description": "Like chatting with an old, trusted friend over a cup of evening chai. Share stories about your day, hobbies, childhood memories, or anything under the sun.",
        "badge_color": "#81B29A"
    },
    "Help Me Think": {
        "icon": "💡",
        "tagline": "Gentle Thinking Partner",
        "description": "Helps you untangle confusing thoughts or tough dilemmas by asking calm, reflective questions—never telling you what you must do.",
        "badge_color": "#F2CC8F"
    }
}

# Rich category-based conversational pool for natural, context-aware dialogues
CONVERSATION_DATABASE = {
    "loneliness": {
        "keywords": ["lonely", "alone", "nobody", "no one", "empty", "isolated", "akela", "left out", "ignore", "tanha"],
        "Just Listen": [
            "I hear you, and it takes so much courage to admit that feeling out loud. Feeling lonely can be so quietly exhausting. You don't have to carry that silence alone right now—I'm sitting right here with you.",
            "I'm listening. Loneliness has a way of making the world feel distant, but please know that in this moment, your presence matters to me. Take all the time you need.",
            "You are not a burden, and you don't have to put on a brave face here. I am right here listening patiently. Bol lo, main sun raha hoon."
        ],
        "Let's Talk": [
            "I'm really glad you reached out to me today. Even when it feels like no one is around, I'm right here in your corner. Tell me—what's something small that usually brings you a bit of comfort when the day feels quiet?",
            "Loneliness is tough, but you're not by yourself right now. Let's chat! If we could share a cup of warm chai or coffee right now, what would we be talking about?",
            "Thank you for sharing that with me. What kind of music, movie, or memory usually makes you feel most at home with yourself?"
        ],
        "Help Me Think": [
            "Feeling isolated often creeps in when our emotional connection tank is running low. When you think about this loneliness, does it feel like wanting someone specific to understand you, or more like needing a general sense of community?",
            "Let's sit with this gently for a moment. What is one small, low-pressure way you could show yourself some tenderness or warmth this evening?",
            "When loneliness feels loudest, it often clouds how much we matter. What is one thing about yourself that you deeply appreciate, even if it feels quiet today?"
        ]
    },
    "stress_work": {
        "keywords": ["stress", "stressed", "work", "job", "office", "deadline", "pressure", "boss", "exam", "college", "study", "studies", "burnout", "overloaded", "project"],
        "Just Listen": [
            "Work and academic stress can feel suffocating when deadlines keep piling on. You don't have to fix everything right this second. Take a slow, deep breath—I'm right here listening to you let it all out.",
            "That sounds like an enormous weight on your shoulders. It makes complete sense that you're feeling drained. I'm holding this space for you to vent without any pressure.",
            "You have been pushing so hard, and it's completely okay to feel tired and fed up. I'm listening to everything you want to get off your chest."
        ],
        "Let's Talk": [
            "Oof, that sounds like quite a grind! What was the single most exhausting part of it today? Let's talk it through, or if you prefer, we can talk about something completely unrelated to take your mind off it.",
            "Work and deadlines have a way of consuming our entire day. When you finally log off or step away today, what is the first relaxing thing you'd love to do?",
            "I hear you. If you could press a magic pause button on everything right now for 24 hours, where would you want to spend tomorrow?"
        ],
        "Help Me Think": [
            "When everything feels urgent at once, our brain goes into overload. If you look at your plate right now, which single task is genuinely critical, and which ones are just being noisy?",
            "Let's break this mountain into smaller stones. What is the one tiny next step you can take that requires the least mental friction?",
            "Remember that your worth isn't defined by today's productivity. When you feel overwhelmed like this, what boundary would protect your peace the most?"
        ]
    },
    "sadness_crying": {
        "keywords": ["sad", "crying", "cry", "tears", "heartbroken", "hurts", "hurt", "pain", "cried", "depressed", "heavy heart", "miserable", "down"],
        "Just Listen": [
            "I'm so sorry your heart is hurting. It is completely okay to cry and let those tears fall. Tears are just the body's way of releasing feelings that are too big for words. I'm right here with you.",
            "Take all the time you need. You don't need to apologize for being sad or try to find a silver lining right now. I'm sitting with you in this quiet moment.",
            "Your pain is real, and it deserves patience and gentleness. Bol lo jo bhi kehna hai. Main poori tarah sun raha hoon."
        ],
        "Let's Talk": [
            "Sending you a warm virtual hug. 🤗 When days feel this tender, even small things can feel heavy. Would it help to talk about what caused this hurt, or would you like to hear a gentle, comforting thought?",
            "I'm right here with you. If you were sitting across from me right now, I'd hand you a warm drink and just let you rest. What usually helps soothe your heart when you're feeling this low?",
            "I'm grateful you felt safe enough to share this with me. Take it one breath at a time. What can we talk about that feels safe and gentle for you right now?"
        ],
        "Help Me Think": [
            "Deep sadness can feel like an unending storm, but emotions are waves that rise, peak, and slowly recede. What do you need most right now: rest, physical comfort, or emotional release?",
            "When we hurt, we are often hardest on ourselves. If someone you cared about came to you with this exact pain, what gentle words would you offer them?",
            "Let's give yourself permission to step back from any big decisions today. What is one gentle thing you can do right now just to take care of your body?"
        ]
    },
    "anxiety_overthinking": {
        "keywords": ["anxious", "anxiety", "overthinking", "nervous", "scared", "fear", "worried", "panic", "spiraling", "future", "what if", "dread", "restless"],
        "Just Listen": [
            "Overthinking can feel like an endless spiral where your mind won't let you rest. You are safe right here in this present moment. I'm listening patiently as you let those racing thoughts out.",
            "I hear how anxious you are feeling. Let your shoulders drop and unclench your jaw. You don't have to have all the answers right now. I'm right here with you.",
            "It is completely understandable to feel shaken by uncertain thoughts. I'm listening to whatever is rushing through your mind without judgment."
        ],
        "Let's Talk": [
            "Anxiety loves playing trick movies in our heads! Let's bring things back to solid ground. Can you look around and name 3 simple physical things you can see near you right now?",
            "Racing thoughts can be so loud. What usually helps distract your mind when the 'what-ifs' start shouting? A walk, some music, or chatting with a friend?",
            "I'm right here with you. What is one comforting memory or thought that usually makes you feel anchored when things feel shaky?"
        ],
        "Help Me Think": [
            "Anxiety often treats imagined possibilities as guaranteed facts. Looking at what you're worried about, what is the realistic worst case, and what is your inner strength to handle it?",
            "Let's separate this into two buckets: What parts of this worry are within your direct control today, and what parts belong to tomorrow or other people?",
            "If your mind is spiraling on 'what if things go wrong', let's ask the opposite: What is a realistic way this could turn out okay?"
        ]
    },
    "confused_dilemma": {
        "keywords": ["confused", "stuck", "decision", "choice", "dilemma", "dont know", "don't know", "lost", "crossroads", "what should i do", "advice", "direction"],
        "Just Listen": [
            "Being stuck in a dilemma is exhausting because your mind never gets to rest. It's okay not to have clarity yet. I'm listening to both sides of what you're weighing.",
            "You don't have to force an answer this second. Feeling confused is simply the space before understanding arrives. I'm right here with you while you sort through it.",
            "I'm listening closely. Share whatever pieces of the puzzle feel tangled to you—there's zero rush."
        ],
        "Let's Talk": [
            "Dilemmas can make your head spin! Tell me about the two options you're torn between. Let's chat through them like two friends thinking aloud over coffee.",
            "It's fascinating how our brains wrestle with choices. What is your gut or intuition whispering, before logic jumps in with all its lists?",
            "Whenever I hear about tough choices, I wonder: What does your heart desire most, even if it feels a little scary to admit?"
        ],
        "Help Me Think": [
            "Let's untangle this one strand at a time. If both choices had zero fear attached to them, which path feels more aligned with who you want to become?",
            "Imagine you flipped a coin for this decision, and while it was in the air, you secretly hoped for one outcome. Which outcome flashed in your mind?",
            "What core value or priority matters most to you in this decision: security, growth, peace of mind, or freedom?"
        ]
    },
    "joy_celebration": {
        "keywords": ["happy", "excited", "passed", "won", "good news", "great day", "promoted", "celebrate", "awesome", "crushed it", "smile", "smiling", "proud", "yay"],
        "Just Listen": [
            "Reading this brings genuine warmth to my heart! You worked so hard, and seeing your joy is wonderful. Soak in this moment and let yourself enjoy every bit of it.",
            "I'm smiling right along with you! Moments like this are so precious. I'm right here celebrating quietly with you.",
            "That is such beautiful news! You deserve all the good things coming your way today."
        ],
        "Let's Talk": [
            "That is fantastic! 🎉 Tell me everything! What was the exact moment you found out, and how did you react?",
            "I love this energy so much! How are you going to treat yourself today? You definitely earned a proper celebration!",
            "What a win! Who is the first person you shared the news with, and what did they say?"
        ],
        "Help Me Think": [
            "What a wonderful milestone! As you look back on the journey that led to this win, what did you learn about your own resilience?",
            "Success always leaves clues! What key habit or support system do you think made the biggest difference in reaching this goal?",
            "How can you anchor this feeling of accomplishment so you can draw strength from it on tougher days in the future?"
        ]
    },
    "exhaustion_sleep": {
        "keywords": ["tired", "sleepy", "can't sleep", "cant sleep", "insomnia", "drained", "exhausted", "bed", "sleepless", "fatigued"],
        "Just Listen": [
            "Exhaustion runs so deep sometimes—both in the body and in the mind. Please give yourself permission to just be. I'm right here listening in the quiet.",
            "If your eyes are heavy and your mind is weary, don't worry about saying the right things. I'm here, and you can rest your thoughts.",
            "The world asks so much of us every single day. Rest is not something you have to earn; it's something you need. I'm listening as long as you're awake."
        ],
        "Let's Talk": [
            "Late night thoughts or daytime fatigue can feel so isolating. Would you like me to share a peaceful, comforting thought, or would you like to talk about a gentle topic to wind down?",
            "It sounds like you've been running on empty. If you could wrap yourself in the coziest blanket right now, what sound or setting would bring you the deepest sleep?",
            "I'm right here keeping you company in the quiet hours. What's a calming memory from your life that always feels like a safe harbor?"
        ],
        "Help Me Think": [
            "When sleep won't come, our minds often try to solve tomorrow's problems tonight. What is one thought you can symbolically 'park' on a shelf until tomorrow morning?",
            "Let's do a quick physical check: Are your shoulders tense? Is your breathing shallow? What is one physical comfort you can give your body right now?",
            "What usually helps your brain transition from 'busy alert mode' to 'safe rest mode'?"
        ]
    },
    "greeting_checkin": {
        "keywords": ["hi", "hello", "hey", "namaste", "salaam", "kaisa", "how are you", "what's up", "whats up", "good morning", "good evening", "good afternoon"],
        "Just Listen": [
            "Namaste! 🙏 I'm right here and all ears. How is your heart doing today? Take your time, bol lo.",
            "Hello there. I'm glad you stopped by. There's no hurry or expectations here—tell me whatever is on your mind.",
            "Hey! It's so nice to hear from you. I'm listening with an open heart. How has your day felt so far?"
        ],
        "Let's Talk": [
            "Hey there! It's so good to talk to you. How has your day been treating you? What's the latest update in your world?",
            "Namaste! Always great to see you. Pull up a chair—what has been keeping you busy today?",
            "Hey friend! I'm doing well, and having you here makes it even better. What's on your mind today?"
        ],
        "Help Me Think": [
            "Hello! Welcome. If you paused for just five seconds right now to take an honest pulse check, what word best describes your headspace today?",
            "Namaste! It's great to connect. What thought or challenge has been occupying the most bandwidth in your mind today?",
            "Hey! Glad you're here. Is there a particular thought or reflection you'd like us to unpack together today?"
        ]
    },
    "general": {
        "keywords": [],
        "Just Listen": [
            "I hear you, and I am listening carefully to every word. Please go on—share as much as feels comfortable.",
            "Thank you for sharing that with me. I'm sitting right beside you, listening with patience and warmth. Bol lo, main sun raha hoon.",
            "What you have to say matters. Take your time, there is no rush at all. I'm right here."
        ],
        "Let's Talk": [
            "That's so interesting to hear! Tell me more—how did that feel, and what did you think in that moment?",
            "I really enjoy talking with you. That's a unique perspective! What else crossed your mind when that happened?",
            "I'm all ears! It's like having a great evening chat. What do you think you'll do next with that?"
        ],
        "Help Me Think": [
            "That's a thoughtful point. If we step back and look at the bigger picture, what feels like the most essential aspect of this for you?",
            "Let's explore that a bit deeper. What would happen if you looked at this from another perspective for just a moment?",
            "That's a very meaningful thought. What is the key question you want to find an answer to here?"
        ]
    }
}

def detect_category(user_input: str) -> str:
    """Detects the emotional theme or intent from the user's message."""
    text_lower = user_input.lower()
    
    for category, data in CONVERSATION_DATABASE.items():
        if category == "general":
            continue
        for kw in data["keywords"]:
            if kw in text_lower:
                return category
                
    return "general"

def generate_contextual_response(user_input: str, mode: str) -> str:
    """
    Returns a warm, natural, and context-aware response based on the detected
    theme and active conversation mode. Avoids immediate repetitions.
    """
    category = detect_category(user_input)
    candidate_responses = CONVERSATION_DATABASE[category].get(mode, CONVERSATION_DATABASE["general"][mode])

    # Select response avoiding recent repetitions
    used_set = st.session_state.get("used_reply_indices", set()) if "used_reply_indices" in st.session_state else set()

    unused_responses = [
        resp for resp in candidate_responses
        if resp not in used_set
    ]

    if not unused_responses:
        # If all candidates have been used, reset memory for this category
        if "used_reply_indices" in st.session_state:
            st.session_state.used_reply_indices.clear()
        unused_responses = candidate_responses

    selected = random.choice(unused_responses)
    if "used_reply_indices" in st.session_state:
        st.session_state.used_reply_indices.add(selected)
    return selected

# ==============================================================================
# 4. SIDEBAR RENDERING & MODE CALLBACKS
# ==============================================================================

def on_sidebar_mode_change():
    """Callback: synchronizes current_mode when user updates sidebar radio."""
    st.session_state.current_mode = st.session_state.apnayaar_mode

def on_mode_button_click(mode_name: str):
    """Callback: synchronizes state before rerun when user clicks main mode cards."""
    st.session_state.current_mode = mode_name
    st.session_state.apnayaar_mode = mode_name

def render_sidebar():
    """Renders the clean, independent sidebar with mode selector and session controls."""
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">🤗 ApnaYaar AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-tagline">“Bol lo. Main sun raha hoon.”</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-desc">'
            'A gentle, patient AI friend for anyone who feels lonely, '
            'overwhelmed, or simply needs someone who listens without judgment.'
            '</div>',
            unsafe_allow_html=True
        )
        
        st.divider()

        # Conversation Mode Selector
        st.markdown("### 🎭 Conversation Mode")
        st.radio(
            label="How would you like ApnaYaar to respond?",
            options=list(MODES.keys()),
            format_func=lambda m: f"{MODES[m]['icon']} {m}",
            key="apnayaar_mode",
            on_change=on_sidebar_mode_change,
            help="Switch how ApnaYaar listens and responds to you."
        )

        # Active mode explanation card
        mode_info = MODES[st.session_state.current_mode]
        st.info(f"**{mode_info['icon']} {st.session_state.current_mode}**\n\n{mode_info['description']}")

        st.divider()

        # Session Controls
        st.markdown("### ⚙️ Session")
        message_count = len(st.session_state.messages)
        st.write(f"💬 Messages in session: **{message_count}**")
        
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.used_reply_indices.clear()
            initialize_session_state()
            st.success("Conversation cleared!")
            st.rerun()

        st.divider()
        st.caption("💛 ApnaYaar AI • A cozy, safe harbor for your thoughts.")

# ==============================================================================
# 5. CHAT INTERFACE RENDERING
# ==============================================================================

def render_hero_banner():
    """Displays the warm hero banner with product name, tagline, and active mode."""
    current_mode = st.session_state.current_mode
    mode_info = MODES[current_mode]

    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-title-row">
                <h1 class="hero-title">🤗 ApnaYaar AI</h1>
                <div class="mode-indicator">
                    {mode_info['icon']} {current_mode} Mode
                </div>
            </div>
            <div class="hero-tagline">“Bol lo. Main sun raha hoon.”</div>
            <p class="hero-subtitle">
                A patient, warm, and non-judgmental space where you can speak your heart out.
                Take your time—there is never any rush here.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_suggestion_chips():
    """Provides gentle, thoughtful starter prompts when beginning a fresh chat."""
    if len(st.session_state.messages) <= 1:
        st.markdown('<div class="suggestion-label">✨ Start with something on your mind:</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        suggestion = None
        with col1:
            if st.button("🌧️ Everything feels overwhelming...", use_container_width=True):
                suggestion = "Everything has been feeling overwhelming lately, and I just needed someone to hear me out."
        with col2:
            if st.button("☕ Can we just chat casually?", use_container_width=True):
                suggestion = "Hey ApnaYaar! How are you doing? I just wanted to chat casually about my day."
        with col3:
            if st.button("🤔 Help me think through a choice...", use_container_width=True):
                suggestion = "I'm caught in a dilemma and feel stuck. Could you help me think through it?"
        
        if suggestion:
            process_new_message(suggestion)
            st.rerun()

def render_chat_history():
    """Iterates through and renders messages in clean, modern chat bubbles."""
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        timestamp = msg.get("time", "")

        avatar = "👤" if role == "user" else "🤗"
        
        with st.chat_message(role, avatar=avatar):
            st.markdown(content)
            if timestamp:
                st.markdown(f'<span class="message-timestamp">{timestamp}</span>', unsafe_allow_html=True)

def process_new_message(user_text: str):
    """
    Appends the user's message to the session, generates a warm,
    context-aware response using Gemini AI tailored to the active mode, and records it.
    """
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    active_mode = st.session_state.current_mode

    # 1. Append user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_text,
        "time": current_time,
        "mode": active_mode
    })

    # 2. Generate genuine response via Gemini AI (passing conversation history)
    try:
        reply_text = generate_apna_yaar_response(
            user_text=user_text,
            mode=active_mode,
            conversation_history=st.session_state.messages[:-1]
        )
    except Exception:
        # Fallback to local contextual response if API error occurs
        reply_text = generate_contextual_response(user_text, active_mode)

    # 3. Append assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply_text,
        "time": current_time,
        "mode": active_mode
    })

def render_chat_input():
    """Renders the chat input bar and processes sent messages."""
    user_prompt = st.chat_input("Bol lo... ApnaYaar sun raha hai 💛")
    if user_prompt and user_prompt.strip():
        process_new_message(user_prompt.strip())
        st.rerun()



# ---------------------------------------------------------------------------
# STT helper (same endpoint as test_gnani_stt.py)
# ---------------------------------------------------------------------------
def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Send recorded audio to Gnani STT and return the transcription."""
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
# TTS helper (verified voice "Avinash", model "timbre-v3.0")
# ---------------------------------------------------------------------------
def synthesize_speech(text: str, speed: float = 1.0) -> bytes:
    """Convert text to speech via Gnani TTS and return WAV bytes.
    Speed parameter directly controls the Gnani TTS generation speed.
    """
    payload = {
        "text": text,
        "voice": "Avinash",
        "model": "timbre-v3.0",
        "language": "hi-IN",
        "speed": float(speed),
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
# Microphone interface – push-to-talk, then STT → Gemini → TTS
# ---------------------------------------------------------------------------
def render_microphone_interface():
    """Capture voice via st.audio_input, run STT → Gemini → TTS pipeline."""
    if not GNANI_API_KEY:
        st.error("GNANI_API_KEY is not configured in .env – voice features are disabled.")
        return

    if not st.session_state.get("mic_active", True):
        st.info("⏳ Processing your recording… please wait.")
        return

    audio = st.audio_input(
        "🎤 Press to record (push-to-talk)",
        key="mic_recorder",
        help="Record your voice, then release. Audio is sent to Gnani STT.",
    )

    if audio is not None:
        raw_bytes = audio.getvalue()
        st.session_state.mic_active = False
        st.session_state.is_playing = False
        st.session_state.companion_state = "listening"

        try:
            with st.spinner("🔊 Listening…"):
                user_text = transcribe_audio_bytes(raw_bytes)

            st.session_state.companion_state = "thinking"
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            active_mode = st.session_state.current_mode

            # Store user message for context
            st.session_state.messages.append({
                "role": "user",
                "content": user_text,
                "time": current_time,
                "mode": active_mode,
            })

            with st.spinner("💭 Thinking…"):
                reply_text = generate_apna_yaar_response(
                    user_text=user_text,
                    mode=active_mode,
                    conversation_history=st.session_state.messages[:-1],
                )

            # Store assistant reply for context
            st.session_state.messages.append({
                "role": "assistant",
                "content": reply_text,
                "time": current_time,
                "mode": active_mode,
            })

            with st.spinner("🗣️ Generating voice reply…"):
                speed = st.session_state.get("voice_speed", 1.0)
                tts_audio = synthesize_speech(reply_text, speed=speed)

            st.session_state.audio_bytes = tts_audio
            st.session_state.audio_ready = True
            st.session_state.companion_state = "speaking"

        except Exception as exc:
            st.error(f"Conversation error: {exc}")
            st.session_state.mic_active = True
            st.session_state.companion_state = "idle"

        st.rerun()

# ---------------------------------------------------------------------------
# Playback – plays TTS audio once, then keeps is_playing=True so the Stop
# button stays active until the user dismisses it or records again.
# ---------------------------------------------------------------------------
def render_playback():
    """Play the TTS audio reply once. Keep is_playing flag active."""
    if st.session_state.get("audio_ready") and st.session_state.get("audio_bytes"):
        st.audio(st.session_state["audio_bytes"], format="audio/wav", autoplay=True)
        # Mark that we sent audio to the browser player
        st.session_state.is_playing = True
        # Prevent the same clip from being re-sent on next rerun
        st.session_state.audio_ready = False
        st.session_state.audio_bytes = None
        # Keep companion_state as "speaking" – it is reset when Stop is pressed
        # or when a new mic recording starts.

# ==============================================================================
# 6. MAIN APPLICATION ENTRY POINT
# ==============================================================================

def main():
    """Main entry point for ApnaYaar AI with Celestial Neon Orb interface."""
    setup_page()
    inject_companion_css()
    initialize_session_state()

    # Sidebar (session controls & status)
    render_sidebar()

    # Compute genuine companion state based on active session flags
    if st.session_state.get("audio_ready") and st.session_state.get("audio_bytes"):
        current_state = "speaking"
    elif st.session_state.get("is_playing", False):
        current_state = "speaking"
    elif not st.session_state.get("mic_active", True):
        current_state = st.session_state.get("companion_state", "thinking")
    else:
        current_state = "idle"

    # 1. Branding Header (top, full width)
    render_header()

    # 2. Desktop-First Dual Panel Layout
    col_stage, col_controls = st.columns([1, 1.25], gap="large")

    with col_stage:
        # Celestial Glowing Orb (idle, listening, thinking, speaking)
        render_orb(state=current_state)

        # Action Callout Text ("Tap to Talk - I'm here for you!")
        render_state_callout(state=current_state)

        # Microphone Input Component
        render_microphone_interface()

        # Audio Playback
        render_playback()

    with col_controls:
        # Interactive Mode Selector (Just Listen, Let's Talk, Help Me Think)
        render_mode_selector(st.session_state.current_mode, on_select=on_mode_button_click)

        # Control Bar: Voice Speed Slider & Stop Speaking Button
        is_speaking = bool(current_state == "speaking")
        new_speed, stop_requested = render_control_bar(
            voice_speed=st.session_state.get("voice_speed", 1.0),
            is_speaking=is_speaking
        )
        if new_speed != st.session_state.get("voice_speed", 1.0):
            st.session_state.voice_speed = new_speed

        if stop_requested:
            st.session_state.audio_bytes = None
            st.session_state.audio_ready = False
            st.session_state.is_playing = False
            st.session_state.mic_active = True
            st.session_state.companion_state = "idle"
            # Client-side pause for any active HTML5 audio in browser
            if hasattr(st, "html"):
                st.html(
                    "<script>try{document.querySelectorAll('audio').forEach(function(el){el.pause();el.currentTime=0;});}catch(e){}</script>"
                )
            else:
                st.markdown(
                    "<script>try{document.querySelectorAll('audio').forEach(function(el){el.pause();el.currentTime=0;});}catch(e){}</script>",
                    unsafe_allow_html=True,
                )
            st.rerun()

        # Trust Badges & Whisper Tagline
        render_footer()

        # Session End / Reset
        if st.button("🛑 End Conversation", key="end_conversation_btn", help="End conversation and clear session", use_container_width=True):
            for key in ["messages", "used_reply_indices", "audio_bytes", "audio_ready", "mic_active", "companion_state", "voice_speed", "is_playing"]:
                st.session_state.pop(key, None)
            initialize_session_state()
            st.success("Conversation cleared. Ready for a fresh start!")
            st.rerun()

if __name__ == "__main__":
    main()
