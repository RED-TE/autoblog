import json
import os
import subprocess
import sys

VERSION_FILE = 'version.json'

def run_cmd(cmd):
    """명령어 실행 및 결과 출력"""
    print(f"▶ 실행 중: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 에러 발생:\n{result.stderr}")
        return False
    print(f"✅ 결과:\n{result.stdout}")
    return True

def increment_version():
    """version.json의 버전을 +1 올려서 저장"""
    if not os.path.exists(VERSION_FILE):
        print(f"❌ {VERSION_FILE} 파일을 찾을 수 없습니다.")
        sys.exit(1)

    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    old_version = data.get('version', '1.0.0')
    parts = old_version.split('.')
    
    # 마지막 자리 숫자 1 증가 (예: 1.0.3 -> 1.0.4)
    parts[-1] = str(int(parts[-1]) + 1)
    new_version = '.'.join(parts)
    
    data['version'] = new_version
    
    # 변경된 버전 저장
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    print(f"🚀 버전 업데이트 완료: {old_version} -> {new_version}")
    return new_version

def main():
    print("=" * 50)
    print("  📦 RealCar Bot 배포 및 자동 버전 업데이트 툴")
    print("=" * 50)

    # 1. 버전 업데이트
    new_version = increment_version()

    # 2. Git 명령어 실행 (1편 제약 등 패치 노트 포함)
    commit_msg = f"Release version {new_version} - Auto Update"
    
    commands = [
        "git add .",
        f'git commit -m "{commit_msg}"',
        "git push origin main"
    ]

    for cmd in commands:
        success = run_cmd(cmd)
        if not success:
            print("⚠️ 진행이 중단되었습니다. Git 상태를 확인하세요.")
            sys.exit(1)

    print("=" * 50)
    print(f"🎉 배포가 성공적으로 완료되었습니다! (현재 버전: {new_version})")
    print("=" * 50)

if __name__ == "__main__":
    main()
