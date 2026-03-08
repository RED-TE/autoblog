from gemini_core import client
import traceback

print("Testing Gemini generation...")
try:
    result = client.rewrite_content(
        facts="테슬라 모델3 하이랜드 장기렌트 출시. 월 50만원대.",
        persona="search_intent",
        keyword="테슬라 장기렌트"
    )
    if result:
        print("SUCCESS! Response received.")
        print(result[:200] + "...")
    else:
        print("FAILED: Result is None")
except Exception as e:
    print("CRASHED during generation:")
    traceback.print_exc()
