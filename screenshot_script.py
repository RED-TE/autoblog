import pyautogui
import time
import os

print("Waiting 3 seconds before taking screenshot...")
time.sleep(3)
file_path = os.path.join(r"C:\Users\jhxox\.gemini\antigravity\brain\1787938e-b331-4f31-9b65-d2fae77cfd36", "lite_plan_ui_test.png")
pyautogui.screenshot(file_path)
print(f"Screenshot saved to {file_path}")
