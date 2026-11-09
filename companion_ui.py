"""
companion_ui.py
===============
Custom UI components for ApnaYaar AI inspired by the Celestial Neon Orb design.
Renders the header, animated glowing orb, state callouts, mode selector,
voice speed control, and trust badges.

Uses Streamlit's native st.html() to guarantee that SVG, HTML, and CSS are
rendered directly into the DOM as visual elements, completely eliminating
unwanted markdown code blocks or white rectangular source containers.
"""

from pathlib import Path
import textwrap
import streamlit as st


def _render_html(html_str: str):
    """
    Safely renders HTML/SVG without markdown converting indented lines into code blocks.
    Uses textwrap.dedent() and st.html() (Streamlit 1.34+) to render raw visual elements.
    """
    cleaned = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


def inject_companion_css():
    """Reads companion.css and injects it cleanly into the page via st.html()."""
    css_path = Path(__file__).resolve().parent / "companion.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        _render_html(f"<style>\n{css_content}\n</style>")


def render_header():
    """Renders top branding: stylized gradient infinity logo, title, and online pill."""
    _render_html(
        """
        <div class="ay-header-row">
            <div class="ay-logo-block">
                <svg class="ay-logo-icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="ay-infinity-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#C084FC" />
                            <stop offset="45%" stop-color="#818CF8" />
                            <stop offset="100%" stop-color="#38BDF8" />
                        </linearGradient>
                    </defs>
                    <path d="M14 16C8.477 16 4 20.477 4 26C4 31.523 8.477 36 14 36C18.667 36 21.6 32.8 24 29.5C26.4 32.8 29.333 36 34 36C39.523 36 44 31.523 44 26C44 20.477 39.523 16 34 16C29.333 16 26.4 19.2 24 22.5C21.6 19.2 18.667 16 14 16ZM14 21C16.761 21 19 23.239 19 26C19 28.761 16.761 31 14 31C11.239 31 9 28.761 9 26C9 23.239 11.239 21 14 21ZM34 21C36.761 21 39 23.239 39 26C39 28.761 36.761 31 34 31C31.239 31 29 28.761 29 26C29 23.239 31.239 21 34 21Z"
                          fill="url(#ay-infinity-grad)" />
                </svg>
                <div>
                    <h1 class="ay-logo-title">ApnaYaar <span>AI</span></h1>
                    <div class="ay-logo-subtitle">Your Voice Companion</div>
                </div>
            </div>
            <div class="ay-online-badge">
                <div class="ay-online-dot"></div>
                <span>Online</span>
            </div>
        </div>
        """
    )


def render_orb(state: str = "idle"):
    """
    Renders the central glowing planet orb with tilted ring, cute face,
    and glowing pedestal. Animates according to `state`:
    - 'idle': gentle floating & soft breathing pulse
    - 'listening': reactive cyan aura & listening pulse
    - 'thinking': purple rotating aura & thoughtful orbit
    - 'speaking': bouncy rhythmic cadence & vibrant neon glow
    """
    valid_states = {"idle", "listening", "thinking", "speaking"}
    current_state = state if state in valid_states else "idle"

    # SVG mouth expression tailored to active state
    if current_state == "speaking":
        # Animated open mouth for speaking
        mouth_svg = """
            <ellipse cx="50" cy="42" rx="7" ry="8" fill="#FFFFFF" opacity="0.95" />
            <ellipse cx="50" cy="44" rx="4" ry="4" fill="#F43F5E" opacity="0.85" />
        """
    elif current_state == "thinking":
        # Thoughtful small rounded mouth
        mouth_svg = """
            <circle cx="50" cy="41" r="3.5" fill="#FFFFFF" opacity="0.95" />
        """
    else:
        # Cheerful curved smile
        mouth_svg = """
            <path d="M 44 38 Q 50 45 56 38" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" fill="none" opacity="0.95" />
        """

    orb_html = f"""
    <div class="ay-orb-stage state-{current_state}">
        <div class="ay-orb-wrapper">
            <!-- Ambient Glow -->
            <div class="ay-orb-glow"></div>

            <!-- Glowing Planet Sphere -->
            <div class="ay-orb-sphere">
                <!-- Cute Face -->
                <svg class="ay-orb-face" viewBox="0 0 100 60" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <!-- Left Eye (Happy closed arc) -->
                    <path d="M 28 28 Q 36 17 44 28" stroke="#FFFFFF" stroke-width="3.6" stroke-linecap="round" fill="none" />
                    <!-- Right Eye (Happy closed arc) -->
                    <path d="M 56 28 Q 64 17 72 28" stroke="#FFFFFF" stroke-width="3.6" stroke-linecap="round" fill="none" />
                    <!-- Left Blush -->
                    <circle cx="27" cy="36" r="5.5" fill="#FB7185" opacity="0.8" />
                    <!-- Right Blush -->
                    <circle cx="73" cy="36" r="5.5" fill="#FB7185" opacity="0.8" />
                    <!-- Mouth -->
                    {mouth_svg}
                </svg>
            </div>

            <!-- Tilted Planetary Ring -->
            <svg class="ay-orb-ring-svg" viewBox="0 0 280 140" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="ay-ring-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.95" />
                        <stop offset="50%" stop-color="#C084FC" stop-opacity="0.85" />
                        <stop offset="100%" stop-color="#818CF8" stop-opacity="0.9" />
                    </linearGradient>
                    <filter id="ay-ring-glow">
                        <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
                        <feMerge>
                            <feMergeNode in="coloredBlur"/>
                            <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                    </filter>
                </defs>
                <ellipse cx="140" cy="70" rx="126" ry="34" stroke="url(#ay-ring-grad)" stroke-width="3.5" filter="url(#ay-ring-glow)" />
            </svg>

            <!-- Ground Pedestal Glow Rings -->
            <div class="ay-pedestal"></div>
            <div class="ay-pedestal-inner"></div>
        </div>
    </div>
    """
    _render_html(orb_html)


def render_state_callout(state: str = "idle"):
    """Displays the action heading ('Tap to Talk' or current state) and supportive subtitle."""
    if state == "listening":
        headline = "Listening..."
        subline = "Go ahead, main sun raha hoon..."
    elif state == "thinking":
        headline = "Thinking..."
        subline = "Untangling thoughts gently..."
    elif state == "speaking":
        headline = "ApnaYaar is speaking..."
        subline = "Bol raha hoon... 💛"
    else:
        headline = "Tap to Talk"
        subline = "I'm here for you!"

    _render_html(
        f"""
        <div class="ay-state-banner">
            <h2 class="ay-state-headline">{headline}</h2>
            <div class="ay-state-subline">{subline}</div>
        </div>
        """
    )


def render_mode_selector(current_mode: str, on_select=None) -> str:
    """
    Renders the '⭐ CONVERSATION MODE' card container with 3 interactive mode cards.
    Uses native button types ('primary' for active, 'secondary' for inactive)
    to guarantee distinct, high-contrast visual styling in Streamlit.
    """
    modes_data = [
        {"name": "Just Listen", "icon": "🎧", "sub": "I'll listen to you"},
        {"name": "Let's Talk", "icon": "💬", "sub": "Have a conversation"},
        {"name": "Help Me Think", "icon": "💡", "sub": "Let's explore ideas"},
    ]

    _render_html(
        """
        <div class="ay-panel-card">
            <div class="ay-panel-header">⭐ Conversation Mode</div>
        </div>
        """
    )

    col1, col2, col3 = st.columns(3)
    new_mode = current_mode

    for col, m in zip([col1, col2, col3], modes_data):
        with col:
            is_active = (current_mode == m["name"])
            btn_type = "primary" if is_active else "secondary"
            label = f"{m['icon']} {m['name']}\n{m['sub']}"

            if on_select:
                if st.button(
                    label,
                    key=f"mode_select_{m['name']}",
                    type=btn_type,
                    use_container_width=True,
                    on_click=on_select,
                    args=(m["name"],),
                    help=f"Switch to {m['name']} mode",
                ):
                    new_mode = m["name"]
            else:
                if st.button(
                    label,
                    key=f"mode_select_{m['name']}",
                    type=btn_type,
                    use_container_width=True,
                    help=f"Switch to {m['name']} mode",
                ):
                    new_mode = m["name"]

    return new_mode


def render_control_bar(voice_speed: float, is_speaking: bool):
    """
    Renders the '⚡ VOICE & PLAYBACK' card with Voice Speed slider and Stop Speaking button.
    Returns: (new_voice_speed, stop_requested)
    """
    _render_html(
        """
        <div class="ay-panel-card" style="margin-top: 4px; padding-bottom: 8px;">
            <div class="ay-panel-header">⚡ Voice & Playback Controls</div>
        </div>
        """
    )

    col_speed, col_stop = st.columns([1.3, 1], gap="medium")
    stop_clicked = False
    new_speed = voice_speed

    with col_speed:
        _render_html(
            '<div style="color: #FFFFFF; font-weight: 800; font-size: 0.9rem; margin-bottom: 2px;">Voice Speed</div>'
        )
        new_speed = st.slider(
            label="Voice Speed",
            min_value=0.75,
            max_value=1.5,
            value=float(voice_speed),
            step=0.05,
            format="%.2fx",
            label_visibility="collapsed",
            key="voice_speed_slider",
            help="Adjusts Gnani TTS speech generation speed.",
        )

    with col_stop:
        _render_html(
            '<div style="font-size: 0.9rem; opacity: 0; margin-bottom: 2px;">Action</div>'
        )
        stop_type = "primary" if is_speaking else "secondary"
        if st.button(
            "⏹ Stop Speaking",
            key="stop_speaking_btn",
            type=stop_type,
            use_container_width=True,
            help="Stop current voice playback",
            disabled=not is_speaking,
        ):
            stop_clicked = True

    return new_speed, stop_clicked


def render_footer():
    """Renders the bottom trust badges and romantic whisper tagline."""
    _render_html(
        """
        <div class="ay-footer">
            <div class="ay-badges-row">
                <div class="ay-badge-item">
                    <span>💜</span>
                    <span>Friendly</span>
                </div>
                <div class="ay-badge-divider"></div>
                <div class="ay-badge-item">
                    <span>🛡️</span>
                    <span>Private</span>
                </div>
                <div class="ay-badge-divider"></div>
                <div class="ay-badge-item">
                    <span>✨</span>
                    <span>AI Companion</span>
                </div>
            </div>
            <div class="ay-whisper-tagline">
                Always here, always listening... 💜
            </div>
        </div>
        """
    )
