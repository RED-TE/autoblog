# firebase_config.py
# Firebase Project Configuration for RealCar Bot

import base64

def _d(s): return base64.b64decode(s).decode('utf-8')

FIREBASE_CONFIG = {
  "apiKey": _d("QUl6YVN5RHdCcjVmdGdKSUQ0Y0d0NDVOMjNlVkNUaUxXdDVNMlBF"),
  "authDomain": _d("cmVjYXJhdXRvLTg4OTUwLmZpcmViYXNlYXBwLmNvbQ=="),
  "databaseURL": _d("aHR0cHM6Ly9yZWNhcmF1dG8tODg5NTAuZmlyZWJhc2Vpby5jb20="),
  "projectId": _d("cmVjYXJhdXRvLTg4OTUw"),
  "storageBucket": _d("cmVjYXJhdXRvLTg4OTUwLmZpcmViYXNlc3RvcmFnZS5hcHA="),
  "messagingSenderId": _d("ODUxNzQ5NTkzNzg2"),
  "appId": _d("MTo4NTE3NDk1OTM3ODY6d2ViOmYxMTRiYTk2ZDNkYWZjZjI2MTg4Mw=="),
  "measurementId": _d("Ry1DVDJSRjFSRk5R")
}

# OAuth 2.0 PKCE Settings
# 데스크탑 앱에서 Google Login을 위한 Redirect URI 설정
# 로컬호스트의 임의 포트(예: 8080)를 리스닝하여 Auth Code를 받습니다.
REDIRECT_URI = "http://localhost:8080/callback"
AUTH_PORT = 8080
