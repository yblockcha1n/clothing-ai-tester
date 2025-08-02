import streamlit as st
import requests
import tempfile
import os
from PIL import Image
import io

class PixelCutClient:
    """PixelCut API クライアント"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.developer.pixelcut.ai/v1/try-on"
    
    def generate(self, person_image, garment_image, garment_mode="auto", 
                preprocess_garment=True, remove_background=False, wait_for_result=True):
        """PixelCut Try-On APIを呼び出し"""
        if not self.api_key:
            st.error("PixelCut API キーが設定されていません。")
            return None
        
        # 画像を一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as person_temp:
            person_image.save(person_temp.name, format="JPEG", quality=95)
            person_temp_path = person_temp.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as garment_temp:
            garment_image.save(garment_temp.name, format="JPEG", quality=95)
            garment_temp_path = garment_temp.name
        
        try:
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': self.api_key
            }
            
            files = {
                'person_image': ('person.jpg', open(person_temp_path, 'rb'), 'image/jpeg'),
                'garment_image': ('garment.jpg', open(garment_temp_path, 'rb'), 'image/jpeg')
            }
            
            data = {
                'garment_mode': garment_mode,
                'preprocess_garment': str(preprocess_garment).lower(),
                'remove_background': str(remove_background).lower(),
                'wait_for_result': str(wait_for_result).lower()
            }
            
            with st.spinner("PixelCutで処理中..."):
                response = requests.post(self.base_url, headers=headers, files=files, data=data, timeout=120)
            
            # ファイルをクローズ
            files['person_image'][1].close()
            files['garment_image'][1].close()
            
            if response.status_code == 200:
                result = response.json()
                if 'result_url' in result:
                    # 結果画像をダウンロード
                    img_response = requests.get(result['result_url'], timeout=60)
                    if img_response.status_code == 200:
                        return Image.open(io.BytesIO(img_response.content))
                    else:
                        st.error(f"結果画像のダウンロードに失敗しました: {img_response.status_code}")
                        return None
                else:
                    st.error("APIレスポンスに結果URLが含まれていません。")
                    return None
            elif response.status_code == 202:
                # 非同期処理の場合（wait_for_result=Falseの場合）
                result = response.json()
                st.info("処理がキューに追加されました。job_idでの状態確認機能は未実装です。")
                return None
            else:
                error_msg = f"PixelCut API エラー: {response.status_code}"
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
            st.error("PixelCut API のタイムアウトエラーです。処理に時間がかかりすぎています。")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"PixelCut API接続エラー: {str(e)}")
            return None
        except Exception as e:
            st.error(f"PixelCut API呼び出し中にエラーが発生しました: {str(e)}")
            return None
        finally:
            # 一時ファイルを削除
            try:
                os.unlink(person_temp_path)
                os.unlink(garment_temp_path)
            except:
                pass