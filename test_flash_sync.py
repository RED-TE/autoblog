import sys
from google import genai

keys = {
    "Primary":  "AIzaSyCOBnxu1e-QGtS3l0ZcVg4DrMeK37DD1L0",
    "Fallback": "AIzaSyA15apXjNCUSXxM02w2TNAd3ycN2heI_zs",
}

for label, api_key in keys.items():
    print(f"\n=== Testing {label} Key ===")
    try:
        client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1'}
        )
        resp = client.models.generate_content(
            model='gemini-1.5-flash',
            contents='Reply with OK'
        )
        print("Success:", len(resp.text), "chars")
    except Exception as e:
        print("Failed:", str(e))
