import streamlit as st
from PIL import Image
import io
from datetime import datetime
from dotenv import load_dotenv
import os

from models.tryon_diffusion import TryOnDiffusionClient
from models.pixelcut import PixelCutClient
from models.fashn import FASHNClient
from models.fitroom import FitroomClient
from utils.image_processing import preprocess_image

from ui.components import (
    render_api_sidebar, render_image_upload, 
    render_tryon_diffusion_settings, render_pixelcut_settings,
    render_fashn_settings, render_fitroom_settings
)

load_dotenv()

# ページ設定
st.set_page_config(
    page_title="AI服装試着アプリ",
    page_icon="👔",
    layout="wide"
)

def load_api_config():
    """環境変数からAPI設定を読み込み"""
    return {
        "segmind_api_key": os.getenv("SEGMIND_API_KEY"),
        "pixelcut_api_key": os.getenv("PIXELCUT_API_KEY"),
        "fashn_api_key": os.getenv("FASHN_API_KEY"),
        "fitroom_api_key": os.getenv("FITROOM_API_KEY")
    }

def execute_tryon(selected_api, person_img, garment_img, api_params, api_config):
    """選択されたAPIで試着を実行"""
    if selected_api == "Try-On Diffusion":
        client = TryOnDiffusionClient(api_config["segmind_api_key"])
        return client.generate(
            person_img, garment_img,
            category=api_params['category'],
            num_inference_steps=api_params['num_inference_steps'],
            guidance_scale=api_params['guidance_scale'],
            seed=api_params['seed']
        )
    
    elif selected_api == "PixelCut":
        client = PixelCutClient(api_config["pixelcut_api_key"])
        return client.generate(
            person_img, garment_img,
            garment_mode=api_params['garment_mode'],
            preprocess_garment=api_params['preprocess_garment'],
            remove_background=api_params['remove_background'],
            wait_for_result=api_params['wait_for_result']
        )
    
    elif selected_api == "FASHN":
        client = FASHNClient(api_config["fashn_api_key"])
        return client.generate(person_img, garment_img, **api_params)
    
    elif selected_api == "Fitroom":
        client = FitroomClient(api_config["fitroom_api_key"])
        return client.generate(person_img, garment_img, **api_params)
    
    return None

def display_results(person_img, garment_img, result_image, selected_api, api_params):
    """結果を表示"""
    if result_image:
        st.success("✨ 試着が完了しました！")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("元の人物画像")
            st.image(person_img, use_container_width=True)
        
        with col2:
            st.subheader("服装画像")
            st.image(garment_img, use_container_width=True)
        
        with col3:
            st.subheader("試着結果")
            st.image(result_image, use_container_width=True)
            
            # ダウンロードボタン
            buf = io.BytesIO()
            result_image.save(buf, format="JPEG", quality=95)
            st.download_button(
                label="📥 結果をダウンロード",
                data=buf.getvalue(),
                file_name=f"tryon_result_{selected_api.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                mime="image/jpeg"
            )
            
            # 使用したAPI情報を表示
            with st.expander("🔍 使用したAPI設定"):
                st.write(f"**API:** {selected_api}")
                if selected_api == "FASHN":
                    st.write(f"**モデルバージョン:** {api_params['model_version']}")
                    st.write(f"**カテゴリ:** {api_params['category']}")
                    if api_params['model_version'] == "tryon-v1.6":
                        st.write(f"**品質モード:** {api_params['mode']}")
                    st.write(f"**シード値:** {api_params['seed']}")
                elif selected_api == "Fitroom":
                    st.write(f"**服装タイプ:** {api_params['cloth_type']}")
                    st.write(f"**画像チェック:** {'有効' if api_params['check_images'] else '無効'}")
                    if api_params['cloth_type'] == "combo":
                        st.write("**試着モード:** コンボ試着（上下同時）")

def main():
    # API設定を初期化
    if 'api_config' not in st.session_state:
        st.session_state.api_config = load_api_config()
    
    st.title("🎨 AI服装試着アプリ")
    st.markdown("複数のAI APIを使用して、様々な服装の試着を体験できます")
    
    # サイドバーでAPI設定
    selected_api, updated_config = render_api_sidebar(st.session_state.api_config)
    st.session_state.api_config = updated_config
    
    # メイン画面：画像アップロード
    person_img, garment_img = render_image_upload()
    
    # API別設定
    if selected_api == "Try-On Diffusion":
        api_params = render_tryon_diffusion_settings()
    elif selected_api == "PixelCut":
        api_params = render_pixelcut_settings()
    elif selected_api == "FASHN":
        api_params = render_fashn_settings()
    elif selected_api == "Fitroom":
        api_params = render_fitroom_settings()
    
    # 実行ボタン
    st.divider()
    
    if st.button("🚀 試着を実行", type="primary", use_container_width=True):
        if not person_img or not garment_img:
            st.error("人物画像と服装画像の両方をアップロードしてください。")
            return
        
        # 選択されたAPIに対応するAPIキーがあるかチェック
        api_key_map = {
            "Try-On Diffusion": "segmind_api_key",
            "PixelCut": "pixelcut_api_key",
            "FASHN": "fashn_api_key",
            "Fitroom": "fitroom_api_key"
        }
        
        required_key = api_key_map[selected_api]
        if not st.session_state.api_config[required_key]:
            st.error(f"{selected_api} APIを使用するには対応するAPI Keyが必要です。")
            return
        
        # Fitroomのコンボ試着の場合、下半身画像が必要
        if selected_api == "Fitroom" and api_params.get('cloth_type') == "combo":
            if not api_params.get('lower_cloth_image'):
                st.error("コンボ試着を選択した場合、下半身服装画像をアップロードしてください。")
                return
        
        # 画像の前処理
        with st.spinner("画像を前処理中..."):
            person_img = preprocess_image(person_img)
            garment_img = preprocess_image(garment_img)
            
            # Fitroomのコンボ試着の場合、下半身画像も前処理
            if selected_api == "Fitroom" and api_params.get('lower_cloth_image'):
                api_params['lower_cloth_image'] = preprocess_image(api_params['lower_cloth_image'])
        
        # APIを呼び出し
        result_image = execute_tryon(selected_api, person_img, garment_img, api_params, st.session_state.api_config)
        
        # 結果表示
        display_results(person_img, garment_img, result_image, selected_api, api_params)

if __name__ == "__main__":
    main()