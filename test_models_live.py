import sys
from google import genai

keys = [
    "AIzaSyCOBnxu1e-QGtS3l0ZcVg4DrMeK37DD1L0",
    "AIzaSyA15apXjNCUSXxM02w2TNAd3ycN2heI_zs",
]

models_to_test = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro"
]

for api_key in keys:
    print(f"\n=== Testing Key {api_key[:10]}... ===")
    
    # 순수 기본 클라이언트 (v1beta/v1 강제 지정 없음)
    client = genai.Client(api_key=api_key)
    
    for model_name in models_to_test:
        try:
            print(f"  Testing {model_name}... ", end="")
            resp = client.models.generate_content(
                model=model_name,
                contents='Reply with OK'
            )
            print(f"✅ Success! ({len(resp.text)} chars)")
        except Exception as e:
            err = str(e).replace('\n', ' ')
            print(f"❌ Failed: {err}")
