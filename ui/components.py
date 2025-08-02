import streamlit as st
from PIL import Image
from config.api_settings import API_HELP_TEXTS, API_TIPS, ENV_SETUP_GUIDE, API_KEY_HELP, UPLOAD_HELP

def render_api_sidebar(api_config):
    """APIキー設定サイドバーをレンダリング"""
    with st.sidebar:
        st.header("⚙️ API設定")
        
        # 環境変数からの読み込み状況を表示
        env_keys = {
            "segmind": api_config["segmind_api_key"],
            "pixelcut": api_config["pixelcut_api_key"], 
            "fashn": api_config["fashn_api_key"],
            "fitroom": api_config["fitroom_api_key"]
        }
        
        # 手動でAPIキーを入力するオプション
        st.subheader("手動APIキー入力")
        manual_keys = {}
        
        manual_keys["segmind"] = st.text_input(
            "Segmind API Key", 
            value=env_keys["segmind"] if env_keys["segmind"] else "",
            type="password",
            help=API_KEY_HELP
        )
        
        manual_keys["pixelcut"] = st.text_input(
            "PixelCut API Key", 
            value=env_keys["pixelcut"] if env_keys["pixelcut"] else "",
            type="password",
            help=API_KEY_HELP
        )
        
        manual_keys["fashn"] = st.text_input(
            "FASHN API Key", 
            value=env_keys["fashn"] if env_keys["fashn"] else "",
            type="password",
            help=API_KEY_HELP
        )
        
        manual_keys["fitroom"] = st.text_input(
            "Fitroom API Key", 
            value=env_keys["fitroom"] if env_keys["fitroom"] else "",
            type="password",
            help=API_KEY_HELP
        )
        
        # 手動入力を反映
        updated_config = api_config.copy()
        for key in manual_keys:
            if manual_keys[key]:
                updated_config[f"{key}_api_key"] = manual_keys[key]
        
        # API選択
        selected_api = st.selectbox(
            "使用するAPI",
            ["Try-On Diffusion", "PixelCut", "FASHN", "Fitroom"],
            help="使用したいAI試着APIを選択してください"
        )
        
        st.divider()
        
        # API キー確認状態
        current_keys = {
            "segmind": updated_config["segmind_api_key"],
            "pixelcut": updated_config["pixelcut_api_key"],
            "fashn": updated_config["fashn_api_key"],
            "fitroom": updated_config["fitroom_api_key"]
        }
        
        status_map = {k: "✅ 設定済み" if v else "❌ 未設定" for k, v in current_keys.items()}
        
        st.write(f"**Segmind API Key:** {status_map['segmind']}")
        st.write(f"**PixelCut API Key:** {status_map['pixelcut']}")
        st.write(f"**FASHN API Key:** {status_map['fashn']}")
        st.write(f"**Fitroom API Key:** {status_map['fitroom']}")
        
        if not all(current_keys.values()):
            st.warning("APIキーを設定してください")
            
            with st.expander("設定方法"):
                st.markdown(ENV_SETUP_GUIDE)
        
        return selected_api, updated_config

def render_image_upload():
    """画像アップロード部分をレンダリング"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("👤 人物画像")
        person_image = st.file_uploader(
            "人物画像をアップロード",
            type=['png', 'jpg', 'jpeg'],
            key="person_upload",
            help=UPLOAD_HELP["person"]
        )
        
        person_img = None
        if person_image:
            person_img = Image.open(person_image)
            st.image(person_img, caption="アップロードされた人物画像", use_container_width=True)
    
    with col2:
        st.header("👕 服装画像")
        garment_image = st.file_uploader(
            "服装画像をアップロード",
            type=['png', 'jpg', 'jpeg'],
            key="garment_upload",
            help=UPLOAD_HELP["garment"]
        )
        
        garment_img = None
        if garment_image:
            garment_img = Image.open(garment_image)
            st.image(garment_img, caption="アップロードされた服装画像", use_container_width=True)
    
    return person_img, garment_img

def render_tryon_diffusion_settings():
    """Try-On Diffusion設定を表示"""
    st.header("🔧 Try-On Diffusion 設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category = st.selectbox(
            "服装カテゴリ",
            ["Upper body", "Lower body", "Dress"],
            help=API_HELP_TEXTS["tryon_diffusion"]["category"]
        )
    
    with col2:
        num_inference_steps = st.slider(
            "推論ステップ数",
            min_value=20,
            max_value=100,
            value=35,
            help=API_HELP_TEXTS["tryon_diffusion"]["num_inference_steps"]
        )
    
    with col3:
        guidance_scale = st.slider(
            "ガイダンススケール",
            min_value=1.0,
            max_value=25.0,
            value=2.0,
            step=0.1,
            help=API_HELP_TEXTS["tryon_diffusion"]["guidance_scale"]
        )
    
    seed = st.number_input(
        "シード値",
        min_value=-1,
        max_value=999999999999999,
        value=12467,
        help=API_HELP_TEXTS["tryon_diffusion"]["seed"]
    )
    
    return {
        'category': category,
        'num_inference_steps': num_inference_steps,
        'guidance_scale': guidance_scale,
        'seed': seed
    }

def render_pixelcut_settings():
    """PixelCut設定を表示"""
    st.header("🔧 PixelCut 詳細設定")
    
    # 基本設定
    st.subheader("基本設定")
    col1, col2 = st.columns(2)
    
    with col1:
        garment_mode = st.selectbox(
            "服装モード",
            ["auto", "full", "upper", "lower"],
            help=API_HELP_TEXTS["pixelcut"]["garment_mode"]
        )
    
    with col2:
        wait_for_result = st.selectbox(
            "処理方式",
            [True, False],
            format_func=lambda x: "同期処理（結果を待つ）" if x else "非同期処理（ジョブID返却）",
            help=API_HELP_TEXTS["pixelcut"]["wait_for_result"]
        )
    
    # 前処理設定
    st.subheader("前処理・後処理設定")
    col1, col2 = st.columns(2)
    
    with col1:
        preprocess_garment = st.checkbox(
            "服装画像の前処理",
            value=True,
            help=API_HELP_TEXTS["pixelcut"]["preprocess_garment"]
        )
    
    with col2:
        remove_background = st.checkbox(
            "結果の背景除去",
            value=False,
            help=API_HELP_TEXTS["pixelcut"]["remove_background"]
        )
    
    # 使用のヒント
    with st.expander("💡 PixelCut API使用のヒント"):
        st.markdown(API_TIPS["pixelcut"])
    
    return {
        'garment_mode': garment_mode,
        'wait_for_result': wait_for_result,
        'preprocess_garment': preprocess_garment,
        'remove_background': remove_background
    }

def render_fashn_settings():
    """FASHN設定を表示"""
    st.header("🔧 FASHN 詳細設定")
    
    # モデルバージョン選択
    st.subheader("モデル設定")
    col1, col2 = st.columns(2)
    
    with col1:
        model_version = st.selectbox(
            "モデルバージョン",
            ["tryon-v1.6", "tryon-v1.5"],
            help=API_HELP_TEXTS["fashn"]["model_version"]
        )
    
    with col2:
        num_samples = st.slider(
            "生成サンプル数",
            min_value=1,
            max_value=4,
            value=1,
            help=API_HELP_TEXTS["fashn"]["num_samples"]
        )
    
    # 基本設定
    st.subheader("基本設定")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category = st.selectbox(
            "服装カテゴリ",
            ["auto", "tops", "bottoms", "one-pieces"],
            help=API_HELP_TEXTS["fashn"]["category"]
        )
    
    with col2:
        garment_photo_type = st.selectbox(
            "服装写真タイプ",
            ["auto", "model", "flat-lay"],
            help=API_HELP_TEXTS["fashn"]["garment_photo_type"]
        )
    
    with col3:
        if model_version == "tryon-v1.6":
            mode = st.selectbox(
                "品質モード",
                ["performance", "balanced", "quality"],
                index=1,
                help=API_HELP_TEXTS["fashn"]["mode"]
            )
        else:
            mode = "balanced"  # v1.5では固定
    
    params = {
        'model_version': model_version,
        'num_samples': num_samples,
        'category': category,
        'garment_photo_type': garment_photo_type,
        'mode': mode
    }
    
    # v1.5専用の詳細設定
    if model_version == "tryon-v1.5":
        st.subheader("詳細制御設定（v1.5専用）")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            params['cover_feet'] = st.checkbox(
                "足元カバー",
                value=False,
                help=API_HELP_TEXTS["fashn"]["cover_feet"]
            )
            
            params['adjust_hands'] = st.checkbox(
                "手の調整",
                value=False,
                help=API_HELP_TEXTS["fashn"]["adjust_hands"]
            )
        
        with col2:
            params['restore_background'] = st.checkbox(
                "背景復元",
                value=False,
                help=API_HELP_TEXTS["fashn"]["restore_background"]
            )
            
            params['restore_clothes'] = st.checkbox(
                "非交換部位の保持",
                value=False,
                help=API_HELP_TEXTS["fashn"]["restore_clothes"]
            )
        
        with col3:
            params['long_top'] = st.checkbox(
                "ロングトップ最適化",
                value=False,
                help=API_HELP_TEXTS["fashn"]["long_top"]
            )
            
            params['nsfw_filter'] = st.checkbox(
                "NSFWフィルター",
                value=True,
                help=API_HELP_TEXTS["fashn"]["nsfw_filter"]
            )
        
        # 高度な設定
        st.subheader("高度な設定（v1.5専用）")
        col1, col2 = st.columns(2)
        
        with col1:
            params['guidance_scale'] = st.slider(
                "ガイダンススケール",
                min_value=1.0,
                max_value=20.0,
                value=2.0,
                step=0.5,
                help=API_HELP_TEXTS["fashn"]["guidance_scale"]
            )
        
        with col2:
            params['timesteps'] = st.slider(
                "拡散ステップ数",
                min_value=20,
                max_value=100,
                value=50,
                help=API_HELP_TEXTS["fashn"]["timesteps"]
            )
    
    # 共通設定
    st.subheader("共通設定")
    params['seed'] = st.number_input(
        "シード値",
        min_value=0,
        max_value=999999999,
        value=42,
        help=API_HELP_TEXTS["fashn"]["seed"]
    )
    
    # 使用のヒント
    with st.expander("💡 FASHN API使用のヒント"):
        st.markdown(API_TIPS["fashn"])
    
    return params

def render_fitroom_settings():
    """Fitroom設定を表示"""
    st.header("🔧 Fitroom 詳細設定")
    
    # 基本設定
    st.subheader("基本設定")
    col1, col2 = st.columns(2)
    
    with col1:
        cloth_type = st.selectbox(
            "服装タイプ",
            ["upper", "lower", "full_set", "combo"],
            help=API_HELP_TEXTS["fitroom"]["cloth_type"]
        )
    
    with col2:
        check_images = st.checkbox(
            "画像適性チェック",
            value=True,
            help=API_HELP_TEXTS["fitroom"]["check_images"]
        )
    
    params = {
        'cloth_type': cloth_type,
        'check_images': check_images
    }
    
    # コンボ試着の場合の追加設定
    if cloth_type == "combo":
        st.subheader("コンボ試着設定")
        st.info("コンボ試着では、上半身と下半身の服装を同時に試着できます。")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**上半身服装画像**: メインの服装画像アップロード欄を使用")
        with col2:
            lower_garment_image = st.file_uploader(
                "下半身服装画像をアップロード",
                type=['png', 'jpg', 'jpeg'],
                key="lower_garment_upload",
                help=UPLOAD_HELP["lower_garment"]
            )
            
            if lower_garment_image:
                lower_garment_img = Image.open(lower_garment_image)
                st.image(lower_garment_img, caption="下半身服装画像", use_container_width=True)
                params['lower_cloth_image'] = lower_garment_img
            else:
                params['lower_cloth_image'] = None
    
    # パフォーマンス情報
    with st.expander("📊 Fitroom API 仕様・制限"):
        st.markdown(API_TIPS["fitroom_specs"])
    
    # 使用のヒント
    with st.expander("💡 Fitroom API使用のヒント"):
        st.markdown(API_TIPS["fitroom_tips"])
    
    return params