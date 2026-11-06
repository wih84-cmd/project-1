import os
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build

# ----------------------------------------------------
# 1. API 키 로드 (Streamlit Secrets 우선 사용)
# ----------------------------------------------------
if "YOUTUBE_API_KEY" in st.secrets:
    API_KEY = st.secrets["YOUTUBE_API_KEY"]
else:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("YOUTUBE_API_KEY")

# YouTube API 클라이언트 생성
youtube = build('youtube', 'v3', developerKey=API_KEY)

# ----------------------------------------------------
# 2. UI 레이아웃 구성
# ----------------------------------------------------
st.title("🎬 유튜브 전세계 동영상 검색 & 분석 시스템")

# 검색 방식 선택
search_option = st.radio("검색 방식을 선택하세요:", ["전체 유튜브 검색", "특정 동영상 URL/ID로 검색"])

# ----------------------------------------------------
# 3. 검색 로직 처리
# ----------------------------------------------------
if search_option == "전체 유튜브 검색":
    keyword = st.text_input("검색할 키워드나 질문을 입력하세요:", placeholder="예: 아이폰 16 리뷰, 우주 과학 등")
    
    if st.button("검색 실행"):
        if keyword.strip():
            res = youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                maxResults=5,  # 상위 5개 결과 가져오기
                order="relevance"
            ).execute()
            
            items = res.get('items', [])
            if items:
                st.subheader(f"🔍 '{keyword}' 검색 결과")
                for item in items:
                    v_id = item['id']['videoId']
                    title = item['snippet']['title']
                    channel_title = item['snippet']['channelTitle']
                    
                    st.markdown(f"### {title}")
                    st.caption(f"채널명: {channel_title}")
                    st.video(f"https://www.youtube.com/watch?v={v_id}")
                    st.divider()
            else:
                st.error("검색 결과가 없습니다.")
        else:
            st.warning("검색어를 입력해 주세요.")

elif search_option == "특정 동영상 URL/ID로 검색":
    video_input = st.text_input("유튜브 동영상 링크 또는 ID를 입력하세요:")
    
    if st.button("영상 데이터 가져오기"):
        # URL에서 Video ID 추출
        v_id = video_input.split("v=")[-1].split("&")[0] if "v=" in video_input else video_input.strip()
        
        if v_id:
            res = youtube.videos().list(part="snippet,statistics", id=v_id).execute()
            if res.get('items'):
                item = res['items'][0]
                snippet = item['snippet']
                stats = item['statistics']

                st.subheader(snippet['title'])
                st.caption(f"채널명: {snippet['channelTitle']}")
                st.video(f"https://www.youtube.com/watch?v={v_id}")

                # 통계 데이터 출력
                col1, col2, col3 = st.columns(3)
                col1.metric("조회수", f"{int(stats.get('viewCount', 0)):,} 회")
                col2.metric("좋아요", f"{int(stats.get('likeCount', 0)):,} 개")
                col3.metric("댓글 수", f"{int(stats.get('commentCount', 0)):,} 개")
            else:
                st.error("올바른 동영상 ID 또는 URL을 입력해 주세요.")    
