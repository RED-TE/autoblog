import subprocess
import hashlib
import platform
import os

def get_cmd_output(cmd):
    """CMD 명령어 실행 결과 반환 (공백 제거)"""
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # [TIMEOUT] 5초 타임아웃 추가하여 시스템 지연 시 행 방지
        output = subprocess.check_output(cmd, shell=True, startupinfo=startupinfo, timeout=5).decode('utf-8').strip()
        return output
    except subprocess.TimeoutExpired:
        print(f"   ⚠️ [HWID] Timeout: {cmd}")
        return "TIMEOUT"
    except Exception as e:
        return "UNKNOWN"

def get_hwid():
    """
    강력한 하드웨어 고유 ID 생성 (Fingerprint)
    조합: Mainboard Serial + CPU Serial + MAC Address (Optional)
    """
    sys_os = platform.system()
    
    if sys_os == "Windows":
        # 1. Mainboard Serial
        board_serial = get_cmd_output("wmic baseboard get serialnumber")
        if "SerialNumber" in board_serial:
            board_serial = board_serial.split('\n')[-1].strip()
            
        # 2. CPU ID
        cpu_id = get_cmd_output("wmic cpu get processorid")
        if "ProcessorId" in cpu_id:
            cpu_id = cpu_id.split('\n')[-1].strip()
            
        # 3. Disk Serial (C:) - Optional (가상환경 체크용)
        # disk_serial = get_cmd_output("vol c:") 
        
        raw_id = f"{board_serial}-{cpu_id}"
        
        # 가상머신/샌드박스 등의 경우 값이 비어있거나 "None" 일 수 있음
        if "None" in raw_id or len(raw_id) < 5:
            # Fallback: MAC Address
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
            raw_id = f"MAC-{mac}"

    elif sys_os == "Darwin": # Mac
        # Mac IOPlatformUUID
        raw_id = get_cmd_output("ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'")
        if not raw_id:
            raw_id = "MAC-UNKNOWN"
    else:
        raw_id = "LINUX-UNKNOWN"

    # 해싱 (길이 통일 및 난독화)
    hashed_hwid = hashlib.sha256(raw_id.encode()).hexdigest().upper()
    return hashed_hwid

if __name__ == "__main__":
    print(f"🖥️  System Fingerprint: {get_hwid()}")
    # print(f"    (Raw: {get_cmd_output('wmic baseboard get serialnumber')})")
