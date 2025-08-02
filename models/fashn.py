import streamlit as st
import requests
import time
import io
from PIL import Image
from utils.image_processing import image_to_base64

class FASHNClient:
    """FASHN API クライアント"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.run_url = "https://api.fashn.ai/v1/run"
        self.status_url = "https://api.fashn.ai/v1/status"
    
    def generate(self, model_image, garment_image, **kwargs):
        """FASHN Try-On APIを呼び出し"""
        if not self.api_key:
            st.error("FASHN API キーが設定されていません。")
            return None
        
        # パラメータの取得とデフォルト値設定
        model_version = kwargs.get('model_version', 'tryon-v1.6')
        category = kwargs.get('category', 'auto')
        mode = kwargs.get('mode', 'balanced')
        garment_photo_type = kwargs.get('garment_photo_type', 'auto')
        seed = kwargs.get('seed', 42)
        num_samples = kwargs.get('num_samples', 1)
        
        # Base64エンコード時にdata URIプレフィックスを追加
        model_image_b64 = f"data:image/jpeg;base64,{image_to_base64(model_image)}"
        garment_image_b64 = f"data:image/jpeg;base64,{image_to_base64(garment_image)}"
        
        # リクエストデータの構築（モデルバージョンに応じて）
        if model_version == "tryon-v1.6":
            inputs = {
                "model_image": model_image_b64,
                "garment_image": garment_image_b64,
                "category": category,
                "mode": mode,
                "garment_photo_type": garment_photo_type,
                "moderation_level": "permissive" if not kwargs.get('nsfw_filter', True) else "strict",
                "seed": seed,
                "num_samples": num_samples,
                "segmentation_free": True,
                "output_format": "png"
            }
        else:  # tryon-v1.5 or fallback
            inputs = {
                "model_image": model_image_b64,
                "garment_image": garment_image_b64,
                "category": category,
                "garment_photo_type": garment_photo_type,
                "cover_feet": kwargs.get('cover_feet', False),
                "adjust_hands": kwargs.get('adjust_hands', False),
                "restore_background": kwargs.get('restore_background', False),
                "restore_clothes": kwargs.get('restore_clothes', False),
                "long_top": kwargs.get('long_top', False),
                "guidance_scale": kwargs.get('guidance_scale', 2),
                "timesteps": kwargs.get('timesteps', 50),
                "seed": seed,
                "num_samples": num_samples,
                "nsfw_filter": kwargs.get('nsfw_filter', True)
            }
        
        run_data = {
            "model_name": model_version,
            "inputs": inputs
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        try:
            # 処理を開始
            with st.spinner("FASHN APIで処理を開始中..."):
                run_response = requests.post(self.run_url, json=run_data, headers=headers, timeout=30)
            
            if run_response.status_code != 200:
                error_msg = f"FASHN API 実行エラー: {run_response.status_code}"
                try:
                    error_detail = run_response.json()
                    if 'error' in error_detail:
                        error_msg += f" - {error_detail['error']}"
                    elif 'message' in error_detail:
                        error_msg += f" - {error_detail['message']}"
                except:
                    error_msg += f" - {run_response.text}"
                
                st.error(error_msg)
                return None
            
            # 処理IDを取得
            run_result = run_response.json()
            if 'id' not in run_result:
                st.error("処理IDが取得できませんでした。")
                return None
            
            prediction_id = run_result['id']
            st.info(f"処理ID: {prediction_id}")
            
            # 結果をポーリング
            return self._poll_for_result(prediction_id, headers)
            
        except requests.exceptions.Timeout:
            st.error("FASHN API のタイムアウトエラーです。")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"FASHN API接続エラー: {str(e)}")
            return None
        except Exception as e:
            st.error(f"FASHN API呼び出し中にエラーが発生しました: {str(e)}")
            return None
    
    def _poll_for_result(self, prediction_id, headers):
        """結果をポーリングして取得"""
        status_url = f"{self.status_url}/{prediction_id}"
        max_attempts = 40  # 最大40回（約2分）
        attempt = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("FASHN APIで処理中...（最大40秒）"):
            while attempt < max_attempts:
                time.sleep(3)  # 3秒待機
                attempt += 1
                
                # プログレスバーを更新
                progress = min(attempt / max_attempts, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"処理中... {attempt}/{max_attempts} ({attempt * 3}秒経過)")
                
                try:
                    status_response = requests.get(status_url, headers=headers, timeout=10)
                    
                    if status_response.status_code != 200:
                        continue
                    
                    status_result = status_response.json()
                    status = status_result.get('status', 'unknown')
                    
                    if status == 'completed':
                        # 結果を取得
                        if 'output' in status_result and status_result['output']:
                            output_urls = status_result['output']
                            if isinstance(output_urls, list) and len(output_urls) > 0:
                                # 最初の結果画像をダウンロード
                                img_response = requests.get(output_urls[0], timeout=60)
                                if img_response.status_code == 200:
                                    progress_bar.progress(1.0)
                                    status_text.text("処理完了！")
                                    return Image.open(io.BytesIO(img_response.content))
                                else:
                                    st.error(f"結果画像のダウンロードに失敗: {img_response.status_code}")
                                    return None
                            else:
                                st.error("結果画像のURLが取得できませんでした。")
                                return None
                        else:
                            st.error("処理は完了しましたが、結果画像が見つかりませんでした。")
                            return None
                    
                    elif status == 'failed':
                        error_detail = status_result.get('error', '不明なエラー')
                        st.error(f"FASHN API 処理エラー: {error_detail}")
                        return None
                    
                    elif status in ['starting', 'in_queue', 'processing']:
                        # 処理継続中
                        continue
                    
                except requests.exceptions.RequestException:
                    # ネットワークエラーの場合は継続
                    continue
        
        # タイムアウト
        st.error("FASHN API 処理がタイムアウトしました。処理に時間がかかりすぎています。")
        return None