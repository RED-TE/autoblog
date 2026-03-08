"""
두 API 키로 각각 사용 가능한 Gemini 모델 목록 조회
"""
from google import genai

keys = {
    "Primary":  "AIzaSyCOBnxu1e-QGtS3l0ZcVg4DrMeK37DD1L0",
    "Fallback": "AIzaSyA15apXjNCUSXxM02w2TNAd3ycN2heI_zs",
}

for label, api_key in keys.items():
    print(f"\n=== {label} Key ===")
    try:
        client = genai.Client(api_key=api_key)
        models = list(client.models.list())
        gen_models = [m.name for m in models if hasattr(m, 'supported_actions') and m.supported_actions and "generateContent" in m.supported_actions]
        if gen_models:
            for name in sorted(gen_models):
                print(f"  {name}")
        else:
            # fallback: print all
            for m in models[:20]:
                print(f"  {m.name}")
    except Exception as e:
        print(f"  Error: {e}")
