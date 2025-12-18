import streamlit as st
import pandas as pd
import random
import time
import os
from PIL import Image, ImageOps

# --- 1. 엑셀 데이터 불러오기 ---
@st.cache_data(show_spinner=False)
def load_data():
    try:
        df = pd.read_excel("quiz_data.xlsx")
        df['gender'] = df['gender'].astype(str).str.upper().str.strip()
        df['answer'] = df['answer'].astype(str).str.strip()
        
        pool = []
        for index, row in df.iterrows():
            pool.append({
                "img": f"images/{row['filename']}", 
                "answer": row['answer'],
                "gender": row['gender']
            })
            
        male_names = df[df['gender'] == 'M']['answer'].unique().tolist()
        female_names = df[df['gender'] == 'F']['answer'].unique().tolist()
        
        return pool, male_names, female_names
        
    except Exception as e:
        return None, None, None

# --- 2. 이미지 리사이징 (200x200 고정) ---
# 모바일 최적화를 위해 크기를 줄였습니다.
def load_and_resize_image(image_path, size=(200, 200)):
    try:
        img = Image.open(image_path)
        img_fixed = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
        return img_fixed
    except Exception:
        return None

# --- 3. 세션 초기화 ---
if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.score = 0
    st.session_state.quiz_set = []

# --- 스타일 설정 (여백 최소화) ---
st.markdown("""
    <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                }
               h3 {
                   margin-bottom: 0.5rem;
               }
    </style>
    """, unsafe_allow_html=True)

def main():
    # [공통] 제목 (Guess Who?) - 크기 줄임
    if st.session_state.step == 0 or st.session_state.step == 2:
        st.markdown("<h3 style='text-align: center;'>🧐 Guess Who?</h3>", unsafe_allow_html=True)

    # [Step 0] 시작 화면
    if st.session_state.step == 0:
        pool, male_names, female_names = load_data()
        if pool is None: st.error("데이터 오류"); return

        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <p>총 {len(pool)}명 중 10문제 출제</p>
            <p style='color: #FF4B4B; font-weight: bold;'>빨리 맞출수록 고득점!🎶</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("게임 시작", use_container_width=True):
            sample_count = min(10, len(pool))
            selected_questions = random.sample(pool, sample_count)
            
            for q in selected_questions:
                correct = q['answer']
                q_gender = q['gender']
                if q_gender == 'M': wrong_pool = [n for n in male_names if n != correct]
                else: wrong_pool = [n for n in female_names if n != correct]
                if len(wrong_pool) < 3: wrong_pool = [n for n in male_names + female_names if n != correct]
                
                wrong_options = random.sample(wrong_pool, 3)
                options = wrong_options + [correct]
                random.shuffle(options)
                q['options'] = options
            
            st.session_state.quiz_set = selected_questions
            st.session_state.step = 1
            st.session_state.q_idx = 0
            st.session_state.score = 0
            st.session_state.start_time = time.time()
            st.rerun()

    # [Step 1] 문제 풀이 화면
    elif st.session_state.step == 1:
        # --- 타이머 및 진행바 (최상단 배치) ---
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0.0, 10 - elapsed)
        
        # 남은 시간 표시용 진행바 (줄어드는 효과)
        st.progress(remaining / 10, text=f"⏰ 남은 시간: {remaining:.1f}초")

        if remaining <= 0:
            st.error("시간 초과!")
            time.sleep(0.5)
            next_question()
            return

        current_q = st.session_state.quiz_set[st.session_state.q_idx]
        
        # 이미지 (200x200) - 가운데 정렬
        if os.path.exists(current_q['img']):
            resized_img = load_and_resize_image(current_q['img'])
            if resized_img:
                col1, col2, col3 = st.columns([1, 2, 1]) # 중앙 배치 비율 조정
                with col2:
                    st.image(resized_img, use_container_width=True)
        
        st.markdown("<p style='text-align: center; font-weight: bold; margin: 10px 0;'>이 사람은 누구일까요?</p>", unsafe_allow_html=True)
        
        # 보기 버튼 (2x2)
        cols = st.columns(2)
        for i, opt in enumerate(current_q['options']):
            # 버튼 높이를 줄여서 타이트하게 배치
            if cols[i % 2].button(opt, use_container_width=True, key=f"btn_{i}"):
                check_answer(opt, current_q['answer'], remaining)
                
        # 문제 수 표시 (하단으로 이동)
        total = len(st.session_state.quiz_set)
        idx = st.session_state.q_idx + 1
        st.caption(f"Question {idx} / {total}")

    # [Step 2] 종료 화면
    elif st.session_state.step == 2:
        st.balloons()
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <h2>🏆 최종 점수</h2>
            <h1 style="color: #FF4B4B; font-size: 40px;">{int(st.session_state.score)} 점</h1>
            <p style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-top: 20px;">
                📸 스크린샷으로 공유하세요!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 다시 풀기", use_container_width=True):
            st.session_state.step = 0
            st.rerun()

# --- 기능 함수 ---
def check_answer(user, answer, time_left):
    if user == answer:
        score = 100 + (time_left * 10)
        st.session_state.score += score
        st.toast("⭕ 정답!", icon="✅")
    else:
        st.toast(f"❌ 땡! 정답: {answer}", icon="❗")
    time.sleep(0.5)
    next_question()

def next_question():
    if st.session_state.q_idx + 1 < len(st.session_state.quiz_set):
        st.session_state.q_idx += 1
        st.session_state.start_time = time.time()
        st.rerun()
    else:
        st.session_state.step = 2
        st.rerun()

if __name__ == "__main__":
    main()