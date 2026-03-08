import google.generativeai as genai
import config

genai.configure(api_key=config.GEMINI_API_KEYS[0])

models_to_test = [
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-preview",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash"
]

print("Testing model availability...")
for m_name in models_to_test:
    try:
        model = genai.GenerativeModel(m_name)
        # Attempt a very small generation to be sure (this might cost tokens but it's the only way to be 100% sure it's valid for this key)
        # However, just initializing might be enough to see if it 404s
        print(f"✅ Model {m_name} initialized successfully.")
    except Exception as e:
        print(f"❌ Model {m_name} failed check: {e}")
