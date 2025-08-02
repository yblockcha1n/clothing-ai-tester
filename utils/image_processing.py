import streamlit as st
import base64
import io
from PIL import Image

def preprocess_image(image):
    """画像を前処理（リサイズ、カラーモード変換等）"""
    # 最大サイズを制限（APIの制限に合わせて）
    max_size = 1024
    
    # リサイズが必要かチェック
    width, height = image.size
    if width > max_size or height > max_size:
        # アスペクト比を保持してリサイズ
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        st.info(f"画像をリサイズしました: {width}x{height} → {new_width}x{new_height}")
    
    # RGBAやP（パレット）モードの場合はRGBに変換
    if image.mode in ('RGBA', 'LA', 'P'):
        # 白背景でアルファチャンネルを合成
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode in ('RGBA', 'LA'):
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)
        image = background
        st.info(f"画像をRGBに変換しました")
    
    return image

def image_to_base64(image):
    """PIL ImageをBase64文字列に変換"""
    buffer = io.BytesIO()
    
    # RGBAやP（パレット）モードの場合はRGBに変換
    if image.mode in ('RGBA', 'LA', 'P'):
        # 白背景でアルファチャンネルを合成
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        if image.mode in ('RGBA', 'LA'):
            background.paste(image, mask=image.split()[-1])
        else:
            background.paste(image)
        image = background
    
    image.save(buffer, format="JPEG", quality=95)
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')