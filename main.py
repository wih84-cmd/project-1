import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

# 환경 변수(.env) 로드
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UCp94pzrtA5wPyZazbDq0CXA"  # 긱블 채널 ID

# YouTube API 클라이언트
youtube = build('youtube', 'v3', developerKey=API_KEY)

st.title("🎬 유튜브 질의응답 시스템")

# 질문 목록 정의
QUESTION_MAP = {
    "1. 긱블에서 가장 조회수가 높은 인기 영상은?": "FkdFDYM_1GM",
    "2. 우주로 간 침팬지 이야기 영상은?": "FkdFDYM_1GM",
    "3. 직접 키워드로 영상 검색": "SEARCH_MODE"
}

# UI 요소 (드롭박스)
selected_q = st.selectbox("질문을 선택하세요:", list(QUESTION_MAP.keys()))

search_query = ""
if selected_q == "3. 직접 키워드로 영상 검색":
    search_query = st.text_input("검색할 키워드를 입력하세요:")

# 검색 기능 함수
def search_video(keyword):
    res = youtube.search().list(
        part="snippet",
        channelId=CHANNEL_ID,
        q=keyword,
        type="video",
        maxResults=1
    ).execute()
    items = res.get('items', [])
    return items[0]['id']['videoId'] if items else None

# 결과 보기 버튼
if st.button("결과 보기"):
    video_id = None
    if selected_q == "3. 직접 키워드로 영상 검색":
        if search_query.strip():
            video_id = search_video(search_query)
        else:
            st.warning("키워드를 입력해 주세요.")
    else:
        video_id = QUESTION_MAP[selected_q]

    if video_id:
        # 동영상 정보 가져오기
        res = youtube.videos().list(part="snippet,statistics", id=video_id).execute()
        if res.get('items'):
            item = res['items'][0]
            snippet = item['snippet']
            stats = item['statistics']

            st.subheader(snippet['title'])
            
            # 영상 재생기 (Embed)
            st.video(f"https://www.youtube.com/watch?v={video_id}")

            # 통계 데이터 출력
            col1, col2, col3 = st.columns(3)
            col1.metric("조회수", f"{int(stats.get('viewCount', 0)):,} 회")
            col2.metric("좋아요", f"{int(stats.get('likeCount', 0)):,} 개")
            col3.metric("댓글 수", f"{int(stats.get('commentCount', 0)):,} 개")
        else:
            st.error("영상을 찾을 수 없습니다.")
