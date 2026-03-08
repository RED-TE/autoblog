import google.generativeai as genai
import sys

# config.py 로드 시도
try:
    import config
    API_KEY = config.GEMINI_API_KEYS[0]
except:
    API_KEY = "발급받은_API_키를_여기에_넣어보세요"

print("--- Gemini API 진단 도구 ---")
print(f"1. API 키 확인: {API_KEY[:10]}...")

try:
    genai.configure(api_key=API_KEY)
    print("2. 연결 시도 중...")
    
    # 가용 모델 목록 가져오기
    models = genai.list_models()
    print("3. 사용 가능한 모델 목록:")
    found = False
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f"   [OK] {m.name}")
            found = True
    
    if not found:
        print("   [!] 사용 가능한 생성 모델이 하나도 없습니다.")
        print("   -> Google AI Studio에서 'Generative Language API'가 활성화되어 있는지 확인하세요.")

except Exception as e:
    print(f"\n[❌] 에러 발생: {e}")
    if "404" in str(e):
        print("\n--- 해결 방법 ---")
        print("현재 404 에러는 '모델 이름' 문제가 아니라 'API 키의 권한' 문제일 확률이 99%입니다.")
        print("1. https://aistudio.google.com/ 에 접속하세요.")
        print("2. 왼쪽 메뉴의 'Get API key'를 클릭하세요.")
        print("3. 현재 사용 중인 API 키가 있는 프로젝트에서 'Generative Language API'가 'Enabled' 상태인지 확인하세요.")
        print("4. 잘 모르겠다면 'Create API key in new project'로 새 키를 발급받으시는 것이 가장 빠릅니다.")

print("\n진단 종료.")
input("엔터를 누르면 창이 닫힙니다...")
