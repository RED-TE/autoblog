import requests
from fake_useragent import UserAgent

def debug_requests():
    ua = UserAgent(platforms='pc')
    headers = {
        "User-Agent": ua.random,
        "Referer": "https://www.naver.com/"
    }
    url = "https://search.naver.com/search.naver?where=blog&query=장기렌트"
    print(f"Fetching {url}...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        with open("debug_html.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Saved to debug_html.html")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_requests()
