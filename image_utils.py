# -*- coding: utf-8 -*-
# image_utils.py — 이미지 완전 고유화 파이프라인 v2
# ① EXIF 완전 삭제  ② 픽셀 노이즈 주입  ③ 미세 크롭
# ④ 밝기/채도/대비 미세 조정  ⑤ 파일 메타데이터 랜덤화

import os
import random
import io
import time
from PIL import Image, ImageEnhance, ImageFilter


def strip_exif(img: Image.Image) -> Image.Image:
    """
    EXIF 메타데이터를 완전 제거합니다.
    새 Image 객체에 픽셀 데이터만 복사하는 방식으로 100% 삭제.
    """
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))
    return clean


def smart_crop(img: Image.Image, min_pct=0.005, max_pct=0.025) -> Image.Image:
    """
    각 면을 0.5~2.5% 랜덤 크롭 — 구도를 미세하게 변경합니다.
    이미지 해시(pHash)가 달라져 '유사 이미지' 감지를 피합니다.
    """
    w, h = img.size
    l = random.randint(int(w * min_pct), int(w * max_pct))
    t = random.randint(int(h * min_pct), int(h * max_pct))
    r = w - random.randint(int(w * min_pct), int(w * max_pct))
    b = h - random.randint(int(h * min_pct), int(h * max_pct))
    return img.crop((l, t, r, b))


def inject_pixel_noise(img: Image.Image, intensity: float = 0.008) -> Image.Image:
    """
    픽셀 단위 RGB 미세 노이즈 주입.
    육안으로는 전혀 보이지 않지만 파일 해시가 매번 달라집니다.
    """
    try:
        import numpy as np
        if img.mode != 'RGB':
            img = img.convert('RGB')
        arr = np.array(img, dtype=np.int16)
        noise = np.random.randint(-int(intensity * 255), int(intensity * 255) + 1,
                                  arr.shape, dtype=np.int16)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)
    except ImportError:
        # numpy 없으면 무작위 단일 픽셀 변조 (폴백)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        data = list(img.getdata())
        for _ in range(max(1, len(data) // 5000)):  # 0.02% 픽셀 변조
            idx = random.randint(0, len(data) - 1)
            r, g, b = data[idx]
            data[idx] = (
                max(0, min(255, r + random.randint(-3, 3))),
                max(0, min(255, g + random.randint(-3, 3))),
                max(0, min(255, b + random.randint(-3, 3))),
            )
        img.putdata(data)
        return img


def adjust_color(img: Image.Image) -> Image.Image:
    """
    밝기 / 대비 / 채도 를 소폭 랜덤 조정합니다.
    """
    img = ImageEnhance.Brightness(img).enhance(random.uniform(0.94, 1.06))
    img = ImageEnhance.Contrast(img).enhance(random.uniform(0.94, 1.06))
    img = ImageEnhance.Color(img).enhance(random.uniform(0.95, 1.05))
    img = ImageEnhance.Sharpness(img).enhance(random.uniform(0.97, 1.03))
    return img


def micro_resize(img: Image.Image) -> Image.Image:
    """
    0.5~1.5% 범위에서 크기를 미세하게 변경합니다.
    """
    w, h = img.size
    nw = int(w * random.uniform(0.985, 1.015))
    nh = int(h * random.uniform(0.985, 1.015))
    return img.resize((nw, nh), Image.LANCZOS)


def process_image(image_path: str, output_path: str = None) -> str:
    """
    이미지 완전 고유화 파이프라인:
    EXIF 삭제 → 미세 크롭 → 픽셀 노이즈 → 색상 조정 → 미세 리사이즈

    Returns: 처리된 이미지 경로
    """
    try:
        img = Image.open(image_path)
        original_mode = img.mode

        # 1. EXIF 완전 제거
        img = strip_exif(img)
        print(f"   🔏 [Image] EXIF 삭제 완료")

        # 2. 미세 크롭 (구도 변경)
        img = smart_crop(img)

        # 3. 픽셀 노이즈 주입
        img = inject_pixel_noise(img)

        # 4. 색상 조정
        img = adjust_color(img)

        # 5. 미세 리사이즈
        img = micro_resize(img)

        # 저장
        if not output_path:
            base, ext = os.path.splitext(image_path)
            # 고유 타임스탬프로 파일명도 매번 다르게
            ts = str(int(time.time() * 1000))[-6:]
            output_path = f"{base}_u{ts}{ext}"

        # JPEG 품질 랜덤화 (88~94) — 파일 크기도 달라짐
        save_kw = {"optimize": True}
        ext_lower = os.path.splitext(output_path)[1].lower()
        if ext_lower in (".jpg", ".jpeg"):
            save_kw["quality"] = random.randint(88, 94)
        elif ext_lower == ".png":
            save_kw["compress_level"] = random.randint(3, 7)

        img.save(output_path, **save_kw)
        size_kb = os.path.getsize(output_path) // 1024
        print(f"   ✅ [Image] 고유화 완료: {os.path.basename(output_path)} ({size_kb}KB)")
        return output_path

    except Exception as e:
        print(f"   ⚠️ [Image] 처리 실패 → 원본 사용: {e}")
        return image_path
