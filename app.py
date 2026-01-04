# メインのStreamlitアプリimport streamlit as st
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="UI Layout Analyzer", layout="wide")
st.title("🛠 UI配置・数値解析プロトタイプ")
st.write("画面のスクリーンショットを解析し、各要素の正確な座標を抽出します。")

# Azure設定
client = ImageAnalysisClient(
    endpoint=st.secrets["AZURE_ENDPOINT"],
    credential=AzureKeyCredential(st.secrets["AZURE_KEY"])
)

# 画像の入力（アップロードまたはカメラ）
uploaded_file = st.file_uploader("解析したい画面のスクリーンショットを選択してください", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 画像を開く
    image = Image.open(uploaded_file)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    
    st.info("レイアウト解析中...")

    try:
        # OCR (Read) 機能を使ってテキストと座標を抽出
        result = client.analyze(
            image_data=img_byte_arr.getvalue(),
            visual_features=[VisualFeatures.READ]
        )

        # 解析データの整理
        detected_elements = []
        draw = ImageDraw.Draw(image)

        if result.read:
            for line in result.read.blocks[0].lines:
                # 座標（4点の角）を取得
                pts = line.bounding_polygon # [x1, y1, x2, y2, x3, y3, x4, y4]
                text = line.text
                
                # 四角形を描画 (左上x, y, 右下x, y)
                draw.rectangle([pts[0].x, pts[0].y, pts[4].x, pts[4].y], outline="red", width=3)
                
                detected_elements.append({
                    "text": text,
                    "x": pts[0].x,
                    "y": pts[0].y,
                    "width": pts[4].x - pts[0].x,
                    "height": pts[4].y - pts[0].y
                })

        # 画面を2分割して表示
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("視覚的確認（バウンディングボックス）")
            st.image(image, use_container_width=True)

        with col2:
            st.subheader("抽出された座標データ (JSON)")
            st.write("この数値を比較することで、GUIのズレを自動検知できます。")
            st.dataframe(detected_elements)

    except Exception as e:
        st.error(f"解析エラー: {e}")