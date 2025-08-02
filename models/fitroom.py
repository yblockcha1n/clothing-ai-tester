import streamlit as st
import requests
import tempfile
import os
import time
import io
from PIL import Image

class FitroomClient:
    """Fitroom API クライアント"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://platform.fitroom.app/api"
        self.headers = {"X-API-KEY": api_key}
    
    def check_model_image(self, model_image):
        """モデル画像の適性をチェック"""
        if not self.api_key:
            st.error("Fitroom API キーが設定されていません。")
            return None
        
        url = f"{self.base_url}/tryon/input_check/v1/model"
        
        # 画像を一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            model_image.save(temp_file.name, format="JPEG", quality=95)
            temp_path = temp_file.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'input_image': ('model.jpg', f, 'image/jpeg')}
                response = requests.post(url, headers=self.headers, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                st.error(f"モデル画像チェックエラー: {response.status_code}")
                return None
        
        except Exception as e:
            st.error(f"モデル画像チェック中にエラーが発生しました: {str(e)}")
            return None
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def check_clothes_image(self, clothes_image):
        """服装画像の適性をチェック"""
        if not self.api_key:
            st.error("Fitroom API キーが設定されていません。")
            return None
        
        url = f"{self.base_url}/tryon/input_check/v1/clothes"
        
        # 画像を一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            clothes_image.save(temp_file.name, format="JPEG", quality=95)
            temp_path = temp_file.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'input_image': ('clothes.jpg', f, 'image/jpeg')}
                response = requests.post(url, headers=self.headers, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                st.error(f"服装画像チェックエラー: {response.status_code}")
                return None
        
        except Exception as e:
            st.error(f"服装画像チェック中にエラーが発生しました: {str(e)}")
            return None
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def create_tryon_task(self, model_image, cloth_image, cloth_type, lower_cloth_image=None):
        """試着タスクを作成"""
        if not self.api_key:
            st.error("Fitroom API キーが設定されていません。")
            return None
        
        url = f"{self.base_url}/tryon/v2/tasks"
        
        # 画像を一時ファイルとして保存
        model_temp_path = None
        cloth_temp_path = None
        lower_cloth_temp_path = None
        
        try:
            # モデル画像の保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                model_image.save(temp_file.name, format="JPEG", quality=95)
                model_temp_path = temp_file.name
            
            # 服装画像の保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                cloth_image.save(temp_file.name, format="JPEG", quality=95)
                cloth_temp_path = temp_file.name
            
            # ファイルデータの準備
            files = {
                'model_image': ('model.jpg', open(model_temp_path, 'rb'), 'image/jpeg'),
                'cloth_image': ('cloth.jpg', open(cloth_temp_path, 'rb'), 'image/jpeg')
            }
            
            data = {'cloth_type': cloth_type}
            
            # コンボ試着の場合の下半身画像処理
            if cloth_type == "combo" and lower_cloth_image is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                    lower_cloth_image.save(temp_file.name, format="JPEG", quality=95)
                    lower_cloth_temp_path = temp_file.name
                
                files['lower_cloth_image'] = ('lower_cloth.jpg', open(lower_cloth_temp_path, 'rb'), 'image/jpeg')
            
            response = requests.post(url, headers=self.headers, files=files, data=data, timeout=30)
            
            # ファイルをクローズ
            for file_obj in files.values():
                if hasattr(file_obj[1], 'close'):
                    file_obj[1].close()
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                error_msg = f"タスク作成エラー: {response.status_code}"
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg += f" - {error_detail['error']}"
                except:
                    error_msg += f" - {response.text}"
                
                st.error(error_msg)
                return None
        
        except Exception as e:
            st.error(f"タスク作成中にエラーが発生しました: {str(e)}")
            return None
        finally:
            # 一時ファイルを削除
            for temp_path in [model_temp_path, cloth_temp_path, lower_cloth_temp_path]:
                if temp_path:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
    
    def get_task_status(self, task_id):
        """タスクのステータスを取得"""
        if not self.api_key:
            st.error("Fitroom API キーが設定されていません。")
            return None
        
        url = f"{self.base_url}/tryon/v2/tasks/{task_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                st.error(f"ステータス取得エラー: {response.status_code}")
                return None
        
        except Exception as e:
            st.error(f"ステータス取得中にエラーが発生しました: {str(e)}")
            return None
    
    def generate(self, model_image, cloth_image, **kwargs):
        """Fitroom Try-On APIを呼び出し（統一インターフェース）"""
        if not self.api_key:
            st.error("Fitroom API キーが設定されていません。")
            return None
        
        # パラメータの取得
        cloth_type = kwargs.get('cloth_type', 'upper')
        lower_cloth_image = kwargs.get('lower_cloth_image', None)
        check_images = kwargs.get('check_images', True)
        
        try:
            # オプション: 画像チェック
            if check_images:
                with st.spinner("画像の適性をチェック中..."):
                    # モデル画像チェック
                    model_check = self.check_model_image(model_image)
                    if model_check:
                        if not model_check.get('is_good', False):
                            error_code = model_check.get('error_code', 'unknown')
                            st.warning(f"モデル画像に問題があります (エラーコード: {error_code})")
                            if error_code.startswith('400'):
                                st.error("モデル画像が使用できません。別の画像をお試しください。")
                                return None
                        else:
                            good_types = model_check.get('good_clothes_types', [])
                            if cloth_type != 'combo' and cloth_type not in good_types:
                                st.warning(f"選択した服装タイプ '{cloth_type}' はこのモデル画像に適していない可能性があります。")
                    
                    # 服装画像チェック
                    cloth_check = self.check_clothes_image(cloth_image)
                    if cloth_check:
                        detected_type = cloth_check.get('clothes_type', 'unknown')
                        is_clothes = cloth_check.get('is_clothes', False)
                        
                        if not is_clothes:
                            st.warning("服装画像が適切でない可能性があります。")
                        
                        if cloth_type != 'combo' and cloth_type != detected_type:
                            st.info(f"検出された服装タイプ: {detected_type}、選択されたタイプ: {cloth_type}")
            
            # タスク作成
            with st.spinner("試着タスクを作成中..."):
                task_result = self.create_tryon_task(model_image, cloth_image, cloth_type, lower_cloth_image)
                
                if not task_result:
                    return None
                
                task_id = task_result.get('task_id')
                if not task_id:
                    st.error("タスクIDが取得できませんでした。")
                    return None
            
            st.info(f"タスクID: {task_id}")
            
            # ステータスをポーリング
            return self._poll_for_result(task_id)
        
        except Exception as e:
            st.error(f"Fitroom API呼び出し中にエラーが発生しました: {str(e)}")
            return None
    
    def _poll_for_result(self, task_id):
        """結果をポーリングして取得"""
        max_attempts = 60  # 最大60回（約2分）
        attempt = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("Fitroom APIで処理中...（最大2分）"):
            while attempt < max_attempts:
                time.sleep(2)  # 2秒待機
                attempt += 1
                
                try:
                    status_result = self.get_task_status(task_id)
                    
                    if not status_result:
                        continue
                    
                    status = status_result.get('status', 'UNKNOWN')
                    progress = status_result.get('progress', 0)
                    
                    # プログレスバーを更新
                    progress_bar.progress(progress / 100.0)
                    status_text.text(f"ステータス: {status} - 進行状況: {progress}% ({attempt * 2}秒経過)")
                    
                    if status == 'COMPLETED':
                        # 結果を取得
                        download_url = status_result.get('download_signed_url')
                        if download_url:
                            # 結果画像をダウンロード
                            img_response = requests.get(download_url, timeout=60)
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
                    
                    elif status == 'FAILED':
                        error_msg = status_result.get('error', '処理に失敗しました')
                        st.error(f"Fitroom API 処理エラー: {error_msg}")
                        return None
                    
                    elif status in ['CREATED', 'PROCESSING']:
                        # 処理継続中
                        continue
                    
                except requests.exceptions.RequestException:
                    # ネットワークエラーの場合は継続
                    continue
                except Exception as e:
                    st.warning(f"ポーリング中に警告: {str(e)}")
                    continue
        
        # タイムアウト
        st.error("Fitroom API 処理がタイムアウトしました。処理に時間がかかりすぎています。")
        return None