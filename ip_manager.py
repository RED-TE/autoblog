# -*- coding: utf-8 -*-
# ip_manager.py
# IP Rotation using ADB (Android Debug Bridge)

import os
import time
import subprocess

def check_adb_connection():
    """
    Checks if an Android device is connected via ADB.
    """
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device\n" in result.stdout or "device\r" in result.stdout:
            # Simple check if any device is listed as 'device'
             lines = result.stdout.strip().split('\n')
             for line in lines[1:]:
                 if "\tdevice" in line:
                     return True
        return False
    except Exception as e:
        print(f"   ⚠️ [IP] ADB Check failed: {e}")
        return False

def toggle_airplane_mode():
    """
    Toggles Airplane mode ON and OFF to change IP (LTE/5G).
    Requires rooted device or ADB secure settings permission:
    `adb shell pm grant com.jrummy.apps.build.prop.editor android.permission.WRITE_SECURE_SETTINGS` (example)
    Or generically: `adb shell settings put global airplane_mode_on 1`
    """
    print("   ✈️ [IP] Toggling Airplane Mode...")
    
    if not check_adb_connection():
        print("   ⚠️ [IP] No Android device found. Skipping IP rotation.")
        return False

    try:
        # Enable Airplane Mode
        subprocess.run(["adb", "shell", "settings", "put", "global", "airplane_mode_on", "1"])
        subprocess.run(["adb", "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "true"])
        time.sleep(2)
        
        # Disable Airplane Mode
        subprocess.run(["adb", "shell", "settings", "put", "global", "airplane_mode_on", "0"])
        subprocess.run(["adb", "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "false"])
        
        print("   ✅ [IP] IP Rotation Triggered (Waiting 5s for reconnect)...")
        time.sleep(5)
        return True
        
    except Exception as e:
        print(f"   ❌ [IP] Rotation Failed: {e}")
        return False

def get_current_ip():
    """
    Optional: Get current public IP for verification.
    """
    try:
        import requests
        return requests.get("https://api.ipify.org", timeout=3).text
    except:
        return "Unknown"
