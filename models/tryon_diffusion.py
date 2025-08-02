import streamlit as st
import requests
import base64
import io
from PIL import Image
from utils.image_processing import image_to_base64

class TryOnDiffusionClient:
    """Try-On Diffusion API クライアント"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.segmind.com/v1/try-on-diffusion"
    
    def generate(self, model_image, cloth_image, category, num_inference_steps=35, guidance_scale=2, seed=12467):
        """Try-On Diffusion APIを呼び出し"""
        if not self.api_key:
            st.error("Segmind API キーが設定されていません。")
            return None
        
        data = {
            "model_image": image_to_base64(model_image),
            "cloth_image": image_to_base64(cloth_image),
            "category": category,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "seed": seed,
            "base64": True
        }
        
        headers = {'x-api-key': self.api_key}
        
        try:
            with st.spinner("Try-On Diffusionで処理中..."):
                response = requests.post(self.base_url, json=data, headers=headers, timeout=120)
                
            if response.status_code == 200:
                # レスポンスタイプをチェック
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    # JSONレスポンスの場合
                    result_data = response.json()
                    if 'image' in result_data:
                        image_base64 = result_data['image']
                        image_data = base64.b64decode(image_base64)
                        return Image.open(io.BytesIO(image_data))
                    else:
                        st.error("APIレスポンスに画像データが含まれていません。")
                        return None
                else:
                    # 直接画像データが返される場合
                    return Image.open(io.BytesIO(response.content))
            else:
                error_msg = f"Try-On Diffusion API エラー: {response.status_code}"
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg += f" - {error_detail['error']}"
                    elif 'message' in error_detail:
                        error_msg += f" - {error_detail['message']}"
                except:
                    error_msg += f" - {response.text}"
                
                st.error(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            st.error("Try-On Diffusion API のタイムアウトエラーです。処理に時間がかかりすぎています。")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Try-On Diffusion API接続エラー: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Try-On Diffusion API呼び出し中にエラーが発生しました: {str(e)}")
            return None