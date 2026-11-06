import os
import re
from collections import Counter
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from konlpy.tag import Okt
from wordcloud import WordCloud

# ----------------------------------------------------
# 1. API 키 로드 (Streamlit Secrets 우선 사용)
# ----------------------------------------------------
if "YOUTUBE_API_KEY" in st.secrets:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("YOUTUBE_API_KEY")

youtube = build('youtube', 'v3', developerKey=API_KEY)

st.title("🎬 유튜브 동영상 분석 & 워드클라우드 시스템")

# ----------------------------------------------------
# 헬퍼 함수: 동영상 상세 통계 및 댓글 수집
# ----------------------------------------------------
def get_video_stats(video_id):
    """동영상 조회수, 좋아요, 댓글 수 가져오기"""
    res = youtube.videos().list(part="statistics,snippet", id=video_id).execute()
    if res.get('items'):
        item = res['items'][0]
        return item['snippet'], item['statistics']
    return None, None

def generate_wordcloud(video_id):
    """댓글 수집 후 워드클라우드 생성"""
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="relevance",
            maxResults=100,
            textFormat="plainText"
        )
        response = request.execute()
        for item in response.get('items', []):
            comments.append(item['snippet']['topLevelComment']['snippet']['textDisplay'])
    except Exception as e:
        st.error("댓글을 가져올 수 없거나 댓글이 비활성화된 영상입니다.")
        return

    if not comments:
        st.warning("수집된 댓글이 없습니다.")
        return

    # 텍스트 전처리 & 명사 추출
    okt = Okt()
    all_text = " ".join(comments)
    cleaned_text = re.sub(r'[^가-힣\s]', '', all_text)
    nouns = okt.nouns(cleaned_text)
    words = [w for w in nouns if len(w) >= 2]
    
    stopwords = ['진짜', '정말', '영상', '생각', '보고', '정도', '때문', '하나', '유튜브']
    words = [w for w in words if w not in stopwords]

    if not words:
        st.warning("분석할 수 있는 단어가 부족합니다.")
        return

    word_counts = Counter(words)

    # 워드클라우드 폰트 설정
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    if not os.path.exists(font_path):
        font_path = None

    wc = WordCloud(
        font_path=font_path,
        background_color="white",
        width=800,
        height=400,
        colormap="viridis"
    ).generate_from_frequencies(word_counts)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

# ----------------------------------------------------
# 2. 메인 UI 및 검색 로직
# ----------------------------------------------------
search_option = st.radio("검색 방식을 선택하세요:", ["전체 유튜브 검색", "특정 동영상 URL/ID로 검색"])

if search_option == "전체 유튜브 검색":
    keyword = st.text_input("검색할 키워드를 입력하세요:", placeholder="예: 긱블, 우주 과학 등")
    
    if st.button("검색 실행"):
        if keyword.strip():
            res = youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                maxResults=3,
                order="relevance"
            ).execute()
            
            items = res.get('items', [])
            if
