import google.generativeai as genai
import sys

def test_gemini():
    api_key = "AIzaSyCOBnxu1e-QGtS3l0ZcVg4DrMeK37DD1L0" # The one currently in config.py
    genai.configure(api_key=api_key)
    
    print("Testing gemini-1.5-pro...")
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content("Hello")
        print("1.5-pro OK:", resp.text)
    except Exception as e:
        print("1.5-pro FAILED:", e)

    print("\nTesting gemini-3.1-pro-preview...")
    try:
        model = genai.GenerativeModel("gemini-3.1-pro-preview")
        resp = model.generate_content("Hello")
        print("3.1-pro-preview OK:", resp.text)
    except Exception as e:
        print("3.1-pro-preview FAILED:", e)

    print("\nTesting gemini-1.5-flash...")
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content("Hello")
        print("1.5-flash OK:", resp.text)
    except Exception as e:
        print("1.5-flash FAILED:", e)

test_gemini()
