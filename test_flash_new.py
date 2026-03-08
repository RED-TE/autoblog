from google import genai
import sys

def test_flash():
    api_key = "AIzaSyCOBnxu1e-QGtS3l0ZcVg4DrMeK37DD1L0"
    client = genai.Client(api_key=api_key)
    
    print("Testing gemini-1.5-flash...")
    try:
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hello, respond with 'OK'"
        )
        print("RESULT:", resp.text)
    except Exception as e:
        print("FAILED:", e)

if __name__ == "__main__":
    test_flash()
