import os
import re
from collections import Counter
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from wordcloud import WordCloud

# ----------------------------------------------------
# 1. API 키 로드 (Streamlit Secrets / .env 호환)
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
# 2. 헬퍼 함수 정의 (통계 가져오기 & 워드클라우드 생성)
# ----------------------------------------------------
def get_video_stats(video_id):
    """동영상 조회수, 좋아요, 댓글 수 데이터 추출"""
    res = youtube.videos().list(part="statistics,snippet", id=video_id).execute()
    if res.get('items'):
        item = res['items'][0]
        return item['snippet'], item['statistics']
    return None, None

def extract_words(text):
    """댓글 텍스트에서 명사/단어 추출 (KoNLPy 예외 안전 처리)"""
    cleaned = re.sub(r'[^가-힣\s]', ' ', text)
    try:
        from konlpy.tag import Okt
        okt = Okt()
        nouns = okt.nouns(cleaned)
        words = [w for w in nouns if len(w) >= 2]
    except Exception:
        # KoNLPy/자바 미설치 환경 대비 fallback
        words = [w for w in cleaned.split() if len(w) >= 2]
    
    stopwords = {'진짜', '정말', '영상', '생각', '보고', '정도', '때문', '하나', '유튜브', '이거', '너무'}
    return [w for w in words if w not in stopwords]

def generate_wordcloud(video_id):
    """댓글 수집 및 워드클라우드 시각화"""
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
    except Exception:
        st.error("댓글을 가져올 수 없거나 댓글 기능이 비활성화된 영상입니다.")
        return

    if not comments:
        st.warning("수집된 댓글이 없습니다.")
        return

    all_text = " ".join(comments)
    words = extract_words(all_text)

    if not words:
        st.warning("분석 가능한 유의미한 단어가 부족합니다.")
        return

    word_counts = Counter(words)

    # 폰트 경로 확인
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
# 3. 메인 UI 및 검색 실행
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
            if items:
                for item in items:
                    v_id = item['id']['videoId']
                    snippet, stats = get_video_stats(v_id)
                    
                    if snippet and stats:
                        st.markdown(f"### {snippet['title']}")
                        st.caption(f"채널명: {snippet['channelTitle']}")
                        st.video(f"https://www.youtube.com/watch?v={v_id}")

                        # 통계 수치 출력
                        c1, c2, c3 = st.columns(3)
                        c1.metric("조회수", f"{int(stats.get('viewCount', 0)):,} 회")
                        c2.metric("좋아요", f"{int(stats.get('likeCount', 0)):,} 개")
                        c3.metric("댓글 수", f"{int(stats.get('commentCount', 0)):,} 개")

                        # 워드클라우드 분석 버튼 (키 고유화 적용)
                        if st.button(f"☁️ 댓글 워드클라우드 보기", key=f"btn_{v_id}"):
                            with st.spinner("댓글 분석 중..."):
                                generate_wordcloud(v_id)

                        st.divider()
            else:
                st.error("검색 결과가 없습니다.")
        else:
            st.warning("검색어를 입력해 주세요.")

elif search_option == "특정 동영상 URL/ID로 검색":
    video_input = st.text_input("유튜브 동영상 링크 또는 ID를 입력하세요:")
    
    if st.button("영상 분석하기"):
        v_id = video_input.split("v=")[-1].split("&")[0] if "v=" in video_input else video_input.strip()
        
        if v_id:
            snippet, stats = get_video_stats(v_id)
            if snippet and stats:
                st.subheader(snippet['title'])
                st.caption(f"채널명: {snippet['channelTitle']}")
                st.video(f"https://www.youtube.com/watch?v={v_id}")

                c1, c2, c3 = st.columns(3)
                c1.metric("조회수", f"{int(stats.get('viewCount', 0)):,} 회")
                c2.metric("좋아요", f"{int(stats.get('likeCount', 0)):,} 개")
                c3.metric("댓글 수", f"{int(stats.get('commentCount', 0)):,} 개")

                st.markdown("### ☁️ 댓글 워드클라우드 분석")
                with st.spinner("댓글 분석 중..."):
                    generate_wordcloud(v_id)
            else:
                st.error("영상을 찾을 수 없습니다.")
