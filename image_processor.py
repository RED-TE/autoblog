import os
import random
import shutil
from PIL import Image, ImageDraw, ImageFont

class ImageEvasionProcessor:
    """네이버 유사 문서(유사 이미지) 탐지 회피용 워터마크 및 이미지 세탁 클래스"""
    
    @staticmethod
    def wash_and_watermark(image_path, output_path, watermark_text, opacity_percent="30%"):
        try:
            # 1단계. 이미지 세탁 (크롭 및 미세 회전) - 해시값 완전 변경
            with Image.open(image_path) as img:
                if img.mode != 'RGB': 
                    img = img.convert('RGB')
                
                w, h = img.size
                
                # 1-1. 랜덤 크롭 (상하좌우 1~3% 무작위 잘라내기)
                # 시각적으로는 티가 안 나지만 픽셀 배치가 완전히 달라져 이미지 DB 검색을 피함
                crop_ratio = random.uniform(0.01, 0.03)
                img = img.crop((
                    int(w * crop_ratio), 
                    int(h * crop_ratio), 
                    w - int(w * crop_ratio), 
                    h - int(h * crop_ratio)
                ))
                
                # 1-2. 미세 회전 (-1도 ~ +1도 사이 무작위 회전)
                img = img.rotate(random.uniform(-1, 1), resample=Image.BICUBIC)
                
                # 2단계. 워터마크 합성 준비
                img_rgba = img.convert('RGBA')
                img_w, img_h = img_rgba.size
                
                # 투명도(Alpha) 파싱 ("30%" -> 76)
                if isinstance(opacity_percent, str):
                    opacity_value = int(opacity_percent.replace('%', '').strip())
                else:
                    opacity_value = int(opacity_percent)
                    
                alpha = int(255 * (opacity_value / 100))
                
                # 투명한 워터마크 전용 레이어 생성
                watermark_layer = Image.new('RGBA', img_rgba.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(watermark_layer)
                
                # 분산값 (font_size ratio, x_spacing_pad, y_spacing_pad, angle) 전부 랜덤화
                font_ratio = random.randint(20, 35) 
                pad_x = random.randint(20, 80)
                pad_y = random.randint(20, 80)
                
                # 폰트 자동 설정 (이미지 크기에 비례하게 조절, 20~35 비율)
                font_size = max(img_w, img_h) // font_ratio  
                font = ImageEvasionProcessor._get_korean_font(font_size)
                
                # 텍스트 크기 측정 (타일링 간격 계산용)
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 랜덤 여백 설정 (격자 간격)
                x_spacing = text_width + pad_x
                y_spacing = text_height + pad_y
                
                # 3단계. 대각선 패턴 타일링 (화면 가득 워터마크 도배)
                # 이미지를 벗어난 곳부터 촘촘히 루프를 돌며 텍스트를 찍음
                for y in range(-text_height * 2, img_h + text_height * 2, max(20, y_spacing)):
                    for x in range(-text_width * 2, img_w + text_width * 2, max(20, x_spacing)):
                        draw.text(
                            (x, y), 
                            watermark_text, 
                            fill=(255, 255, 255, alpha), # 흰색 텍스트 + 투명도 적용
                            font=font
                        )
                
                # 4단계. 워터마크 레이어 통째로 회전시키기
                angle = random.randint(-45, 45) # -45도 ~ +45도 랜덤 회전
                watermark_layer = watermark_layer.rotate(angle, expand=False)
                
                # 원본 이미지(img_rgba) 위에 기울어진 워터마크 레이어(watermark_layer) 올리기
                final_img = Image.alpha_composite(img_rgba, watermark_layer)
                
                # 5단계. ⭐ 픽셀 미세 변경 (중요! - 해시값 완전 변경)
                # 저장 직전에 RGB로 변환하고 맨 왼쪽 위 픽셀의 값을 1만큼 변경
                final_rgb = final_img.convert('RGB')
                pixels = final_rgb.load()
                
                try:
                    r, g, b = pixels[0, 0]
                    # 값 조정 (오버플로우 방지)
                    if r > 250: r -= 1
                    else: r += 1
                    pixels[0, 0] = (r, g, b)
                    # print(f"   🔬 [Pixel Tweak] 맨 위 픽셀 1만큼 변경 완료 (Hash 회피)")
                except: pass
                
                # 6단계. 품질 랜덤 조정 후 저장 (93~98)
                quality = random.randint(93, 98)
                final_rgb.save(output_path, quality=quality, optimize=True)
                
                return True
                
        except Exception as e:
            print(f"❌ 이미지 세탁/워터마크 처리 실패: {e}")
            try: shutil.copy2(image_path, output_path)
            except: pass
            return False
            
    @staticmethod
    def _get_korean_font(font_size):
        """OS 환경에 맞춰 한글 지원 폰트를 자동으로 찾아오는 내부 헬퍼 함수"""
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",                     # 윈도우 기본 1. 맑은 고딕
            "C:/Windows/Fonts/gulim.ttc",                      # 윈도우 기본 2. 굴림
            "/System/Library/Fonts/AppleGothic.ttf",           # 맥OS
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # 리눅스 우분투
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, font_size)
                except: continue
                
        return ImageFont.load_default()
