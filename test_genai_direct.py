import google.generativeai as genai
import sys

print("Step 1: Configuring GenAI...", flush=True)
genai.configure(api_key="AIzaSyCqzbb5eocXOgcGy7bo1luqlH8udBstAyA")

print("Step 2: Initializing Model...", flush=True)
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("   Model initialized.", flush=True)
except Exception as e:
    print(f"   Model init failed: {e}", flush=True)

print("Step 3: Generating content...", flush=True)
try:
    res = model.generate_content("Hello")
    print(f"   Response: {res.text}", flush=True)
except Exception as e:
    print(f"   Generation failed: {e}", flush=True)
