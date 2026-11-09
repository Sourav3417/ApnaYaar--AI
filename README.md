# 🤗 ApnaYaar AI

> **“Bol lo. Main sun raha hoon.”**  
> *A patient, warm, and non-judgmental AI companion for anyone who feels lonely, overwhelmed, or simply wants someone to talk to.*

---

## 📖 About ApnaYaar AI

Many people deal with quiet stress, burnout, isolation, or overwhelming choices. When someone reaches out, they usually don't want cold lectures, robotic checklists, or unsolicited advice. What they need most is someone who **listens patiently, validates their feelings, and offers unconditional warmth**.

**ApnaYaar AI** provides a calm, safe, and soothing space to express whatever is on your mind at your own pace.

---

## ✨ Key Features

1. **Warm, Independent Companion Aesthetic**:
   - Designed with soothing colors (`#FAF6F0`, `#C85A32`, `#2D3142`).
   - Clean, distraction-free modern chat bubbles with gentle timestamps.
   - Fully responsive and mobile-friendly.

2. **Three Conversation Modes**:
   - 👂 **Just Listen**: Pure empathetic listening. Sits with you, validates how you feel, and holds space without offering unsolicited advice.
   - 💬 **Let's Talk**: Warm, casual conversation like chatting with an old, trusted friend over evening chai.
   - 💡 **Help Me Think**: Acts as a gentle thinking partner, asking calm, reflective questions to help you untangle confusing thoughts and choices.

3. **Context-Aware Conversational Intelligence**:
   - Detects emotional themes such as loneliness, workplace burnout, exam stress, anxiety, dilemmas, sadness, or celebration.
   - Avoids repetitive phrasing across the session.

4. **Simple, Transparent Session Controls**:
   - Session-based conversation memory (`st.session_state`).
   - One-click "Clear Conversation" button to start fresh anytime.

---

## 📂 Project Structure

```text
AI Companion/
├── app.py              # Main Streamlit web application
├── config.py           # Secure environment configuration loader
├── .env                # Local private secrets (ignored by Git)
├── .env.example        # Template for environment variables
├── .gitignore          # Git exclusion rules preventing secret leakage
├── requirements.txt    # Project dependencies
└── README.md           # Documentation & AI integration guide
```

---

## 🔒 Secure API Configuration

1. Locate the `.env` file in the project folder (or copy `.env.example` to `.env`).
2. Add your Gnani API key:
   ```env
   GNANI_API_KEY="your_actual_key_here"
   ```
3. Verify that your configuration loads safely (without displaying your secret):
   ```bash
   python config.py
   ```

---

## 🚀 How to Run the App

### 1. Open Terminal or PowerShell
Navigate to your project directory:
```bash
cd "c:\Users\User\Downloads\AI Companion"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python -m streamlit run app.py
```

Open your browser and visit:
```text
http://localhost:8501
```

---

## 🤖 Language Model Status: Connected to Google Gemini AI

ApnaYaar AI is actively connected to **Google Gemini AI** via the official `google-genai` Python SDK.

* **Active Model**: `gemini-3.5-flash` (with automated fallback to `gemini-3.5-flash-lite`).
* **Persona & System Instructions**: Tailored individually for all three modes:
  * **Just Listen**: Pure empathetic listening, emotion validation, zero unsolicited advice.
  * **Let's Talk**: Warm, natural, and relatable casual conversation.
  * **Help Me Think**: Reflective thinking partner asking clarifying questions without dictating choices.
* **Context Preservation**: Maintains multi-turn conversation context across session turns.
* **Credential Safety**: Loaded exclusively from `.env` via `python-dotenv`. Keys are never exposed or printed.

4. **Update `generate_contextual_response()` in `app.py`**:
   - Replace the local template selection with an API call passing a warm system prompt (e.g. instructing the model to act as *ApnaYaar* and strictly follow the selected mode: Just Listen, Let's Talk, or Help Me Think).
