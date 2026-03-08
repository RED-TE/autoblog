import sys
import os

print("Step 1: Importing config...", flush=True)
try:
    import config
    print(f"   Model from config: {config.GEMINI_MODEL}", flush=True)
except Exception as e:
    print(f"   FAILED to import config: {e}", flush=True)

print("Step 2: Importing gemini_core...", flush=True)
try:
    import gemini_core
    print("   Imported gemini_core successfully.", flush=True)
except Exception as e:
    print(f"   FAILED to import gemini_core: {e}", flush=True)
    sys.exit(1)

print("Step 3: Initializing model (implicitly via import)...", flush=True)
client = gemini_core.client
if client.model:
    print(f"   Model initialized: {client.model.model_name}", flush=True)
else:
    print("   Model is NOT initialized.", flush=True)

print("Step 4: Testing simple generation...", flush=True)
try:
    res = client.generate("Hello, say 'Test OK'")
    if res:
        print(f"   SUCCESS! Response: {res}", flush=True)
    else:
        print("   FAILED: Response is None", flush=True)
except Exception as e:
    print(f"   CRASHED: {e}", flush=True)
