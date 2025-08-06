import streamlit as st
import requests
import time
import io
import base64
from PIL import Image
import json

class FASHNClient:
    """FASHN API クライアント"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.run_url = "https://api.fashn.ai/v1/run"
        self.status_url = "https://api.fashn.ai/v1/status"
    
    def _validate_model_image(self, image):
        """モデル画像の適性を検証"""
        try:
            # 基本的な画像情報をチェック
            width, height = image.size
            
            # 最小サイズチェック
            if width < 256 or height < 256:
                st.warning("画像が小さすぎます。最小256x256px必要です。")
                return False
            
            # アスペクト比チェック（極端に細長い画像は避ける）
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 3.0:
                st.warning("画像のアスペクト比が極端です。より正方形に近い画像を使用してください。")
                return False
            
            # 縦向き画像を推奨
            if width > height:
                st.warning("横向きの画像です。縦向きの全身画像を推奨します。")
            
            return True
            
        except Exception as e:
            st.error(f"画像検証中にエラー: {str(e)}")
            return False
    
    def _prepare_image_data(self, image, is_model_image=False):
        """画像データを適切な形式で準備"""
        try:
            # モデル画像の場合は検証を実行
            if is_model_image and not self._validate_model_image(image):
                st.warning("画像に問題がありますが、処理を続行します。")
            
            # 画像がRGBモードでない場合は変換
            if image.mode != 'RGB':
                image = image.convert('RGB')
                st.info(f"画像をRGBモードに変換しました")
            
            # 画像サイズを調整（FASHN APIの推奨に合わせる）
            width, height = image.size
            
            # モデル画像の場合はより大きなサイズを維持（ポーズ検出のため）
            if is_model_image:
                max_size = 1024
                # 縦長画像の場合、高さを基準にリサイズ
                if height > width:
                    if height > max_size:
                        new_height = max_size
                        new_width = int(width * (max_size / height))
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        st.info(f"モデル画像をリサイズ: {width}x{height} → {new_width}x{new_height}")
                else:
                    if width > max_size or height > max_size:
                        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        st.info(f"モデル画像をリサイズ: {width}x{height} → {image.width}x{image.height}")
            else:
                # 服装画像は標準的なリサイズ
                max_size = 768
                if width > max_size or height > max_size:
                    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    st.info(f"服装画像をリサイズ: {width}x{height} → {image.width}x{image.height}")
            
            # Base64エンコード（高品質で保存）
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=95)
            img_data = buffer.getvalue()
            
            base64_string = base64.b64encode(img_data).decode('utf-8')
            
            # data URIとして返す
            return f"data:image/jpeg;base64,{base64_string}"
        
        except Exception as e:
            st.error(f"画像データの準備中にエラー: {str(e)}")
            return None
    
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
        
        # 画像データを準備
        st.info("モデル画像を準備中...")
        model_image_b64 = self._prepare_image_data(model_image, is_model_image=True)
        
        st.info("服装画像を準備中...")
        garment_image_b64 = self._prepare_image_data(garment_image, is_model_image=False)
        
        if not model_image_b64 or not garment_image_b64:
            st.error("画像データの準備に失敗しました。")
            return None
        
        # ポーズ検出に関するヒントを表示
        with st.expander("💡 ポーズエラーが発生した場合のヒント"):
            st.markdown("""
            **FASHN APIが人物のポーズを検出できない場合の対処法:**
            
            **推奨する人物画像:**
            • 1人だけが写っている画像
            • 正面を向いて立っている姿勢
            • 全身が写っている（3/4身以上）
            • 明るく鮮明な画像
            • シンプルな背景
            • 手足がはっきり見える
            
            **避けるべき画像:**
            • 複数人が写っている
            • 横向きや後ろ向き
            • 座っている・寝ている
            • 暗い・ぼやけた画像
            • 複雑な背景
            • 手足が隠れている
            • 極端に小さい・大きい画像
            """)
        
        st.success("画像データの準備が完了しました。")
        
        # リクエストデータの構築
        if model_version == "tryon-v1.6":
            inputs = {
                "model_image": model_image_b64,
                "garment_image": garment_image_b64,
                "category": category,
                "mode": mode,
                "garment_photo_type": garment_photo_type,
                "seed": seed,
                "num_samples": num_samples
            }
        else:  # tryon-v1.5 の正しいパラメータセット
            inputs = {
                "model_image": model_image_b64,
                "garment_image": garment_image_b64,
                "category": category,
                "mode": mode,  # v1.5でもmodeパラメータは使用可能
                "garment_photo_type": garment_photo_type,
                "moderation_level": kwargs.get('moderation_level', 'permissive'),
                "seed": seed,
                "num_samples": num_samples,
                "segmentation_free": kwargs.get('segmentation_free', True)  # v1.5の重要なパラメータ
            }
        
        run_data = {
            "model_name": model_version,
            "inputs": inputs
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # デバッグ用：リクエストデータをログ出力（画像データは除外）
        debug_data = run_data.copy()
        debug_inputs = debug_data['inputs'].copy()
        debug_inputs['model_image'] = f"[BASE64 DATA - Length: {len(model_image_b64)}]"
        debug_inputs['garment_image'] = f"[BASE64 DATA - Length: {len(garment_image_b64)}]"
        debug_data['inputs'] = debug_inputs
        
        st.info(f"リクエスト送信中... モデル: {model_version}")
        with st.expander("🔍 デバッグ情報"):
            st.json(debug_data)
        
        try:
            # JSONシリアライゼーションのテスト
            try:
                json_data = json.dumps(run_data)
                st.success(f"JSONシリアライゼーション成功: {len(json_data)} bytes")
            except Exception as json_error:
                st.error(f"JSONシリアライゼーションエラー: {json_error}")
                return None
            
            # 処理を開始
            with st.spinner("FASHN APIで処理を開始中..."):
                response = requests.post(
                    self.run_url, 
                    json=run_data, 
                    headers=headers, 
                    timeout=30
                )
            
            # レスポンスの詳細をログ出力
            st.info(f"レスポンス受信: ステータスコード {response.status_code}")
            
            # レスポンス内容をデバッグ表示
            with st.expander("🔍 APIレスポンス詳細"):
                st.text(f"Status Code: {response.status_code}")
                st.text(f"Headers: {dict(response.headers)}")
                try:
                    response_json = response.json()
                    st.json(response_json)
                except:
                    st.text(f"Response Text: {response.text}")
            
            if response.status_code != 200:
                error_msg = f"FASHN API 実行エラー: {response.status_code}"
                try:
                    error_detail = response.json()
                    st.error(f"エラー詳細: {error_detail}")
                    if 'error' in error_detail:
                        error_msg += f" - {error_detail['error']}"
                    elif 'message' in error_detail:
                        error_msg += f" - {error_detail['message']}"
                    elif 'detail' in error_detail:
                        error_msg += f" - {error_detail['detail']}"
                except:
                    st.error(f"レスポンステキスト: {response.text}")
                    error_msg += f" - {response.text}"
                
                st.error(error_msg)
                return None
            
            # 処理IDを取得
            run_result = response.json()
            if 'id' not in run_result:
                st.error("処理IDが取得できませんでした。")
                st.error(f"レスポンス内容: {run_result}")
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
            st.error(f"エラーの詳細: {type(e).__name__}: {str(e)}")
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
                        st.warning(f"ステータス取得エラー: {status_response.status_code}")
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
                            st.error(f"ステータス結果: {status_result}")
                            return None
                    
                    elif status == 'failed':
                        error_detail = status_result.get('error', '不明なエラー')
                        st.error(f"FASHN API 処理エラー: {error_detail}")
                        st.error(f"詳細: {status_result}")
                        return None
                    
                    elif status in ['starting', 'in_queue', 'processing']:
                        # 処理継続中
                        continue
                    
                except requests.exceptions.RequestException as e:
                    st.warning(f"ポーリング中のネットワークエラー: {str(e)}")
                    continue
                except Exception as e:
                    st.warning(f"ポーリング中に警告: {str(e)}")
                    continue
        
        # タイムアウト
        st.error("FASHN API 処理がタイムアウトしました。処理に時間がかかりすぎています。")
        return None