import shutil
import os

files_to_copy = [
    "firebase_config.py",
    "hwid_manager.py",
    "firebase_auth.py",
    "firebase_db.py",
    "plan_manager.py",
    "auth_client.py"
]

src_dir = r"C:\Users\jhxox\Desktop\sales_progerm\inphoto\RealCar_bot"
dst_dir = r"C:\Users\jhxox\Desktop\blolg_aoto"
for f in files_to_copy:
    src_path = os.path.join(src_dir, f)
    dst_path = os.path.join(dst_dir, f)
    print(f"Copying {f} from {src_path} to {dst_path}...")
    shutil.copy2(src_path, dst_path)

print("Copy completed")
