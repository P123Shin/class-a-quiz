import streamlit as st
import pandas as pd
import random
import time
import os
from PIL import Image, ImageOps
import streamlit.components.v1 as components

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

# --- 2. 이미지 리사이징 (200x200) ---
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

# --- 4. 타이머 JS 코드 ---
def get_timer_html():
    return """
    <div id="countdown-text" style="text-align: right; font-size: 20px; font-weight: bold; color: #FF4B4B; line-height: 1.2;">
        ⏰ 10
    </div>
    <script>
        let timeLeft = 10;
        const timerElement = document.getElementById("countdown-text");
        const countdown = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(countdown);
                timerElement.innerHTML = "⏰ 0";
            } else {
                timerElement.innerHTML = "⏰ " + timeLeft;
            }
            timeLeft -= 1;
        }, 1000);
    </script>
    """

# --- 스타일 설정 ---
st.markdown("""
    <style>
        /* 버튼 스타일: 가로 4개 배치를 위해 패딩과 폰트 크기 조절 */
        div.stButton > button {
            margin: 0 auto;
            display: block;
            width: 100%;
            padding: 0.4rem 0.1rem; /* 패딩을 줄여서 좁은 공간에 맞춤 */
            font-size: 14px;        /* 폰트 크기를 약간 줄임 */
        }
        /* 앱 상단 여백 줄이기 */
        .block-container {
            padding-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    # [공통] 제목
    if st.session_state.step == 0 or st.session_state.step == 2:
        st.markdown("<h3 style='text-align: center; margin-top: 10px;'>🧐 Guess Who?</h3>", unsafe_allow_html=True)

    # [Step 0] 시작 화면
    if st.session_state.step == 0:
        pool, male_names, female_names = load_data()
        if pool is None: st.error("데이터 오류"); return

        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <p>총 {len(pool)}명 중 10문제 출제</p>
            <p style='color: #FF4B4B; font-weight: bold;'>답을 빨리 맞출수록 점수가 올라갑니다🎶</p>
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
        # --- 상단 레이아웃 (질문 + 타이머) ---
        # 왼쪽: "Q1 이 사람은 누구일까요?" / 오른쪽: 타이머
        col_text, col_timer = st.columns([3, 1])
        
        with col_text:
            current_idx = st.session_state.q_idx + 1
            # H3 태그와 span 태그를 섞어서 한 줄로 표현
            st.markdown(f"""
                <div style='display: flex; align-items: center; height: 40px;'>
                    <h3 style='margin: 0; margin-right: 10px;'>Q{current_idx}</h3>
                    <span style='font-weight: bold; font-size: 16px;'>이 사람은 누구일까요?</span>
                </div>
                """, unsafe_allow_html=True)
        
        with col_timer:
            # 타이머가 잘리지 않도록 높이를 충분히 줌 (height=50)
            components.html(get_timer_html(), height=50, scrolling=False)

        # 시간 체크 로직
        elapsed = time.time() - st.session_state.start_time
        remaining = 10 - elapsed
        if remaining < -0.5:
            st.error("시간 초과!")
            time.sleep(0.5)
            next_question()
            return

        current_q = st.session_state.quiz_set[st.session_state.q_idx]
        
        # --- 이미지 (중앙 정렬) ---
        if os.path.exists(current_q['img']):
            resized_img = load_and_resize_image(current_q['img'])
            if resized_img:
                # 이미지를 중앙에 배치하기 위한 컬럼 비율
                c1, c2, c3 = st.columns([1, 4, 1])
                with c2:
                    st.image(resized_img, use_container_width=True)
        
        # --- 보기 버튼 (가로 4개 배열) ---
        # st.columns(4)로 4개의 칸을 만듭니다.
        c1, c2, c3, c4 = st.columns(4)
        opts = current_q['options']
        ans = current_q['answer']

        # 각 칸에 버튼 하나씩 배치 (use_container_width=True로 꽉 차게)
        with c1:
            if st.button(opts[0], key="opt0", use_container_width=True): check_answer(opts[0], ans)
        with c2:
            if st.button(opts[1], key="opt1", use_container_width=True): check_answer(opts[1], ans)
        with c3:
            if st.button(opts[2], key="opt2", use_container_width=True): check_answer(opts[2], ans)
        with c4:
            if st.button(opts[3], key="opt3", use_container_width=True): check_answer(opts[3], ans)

    # [Step 2] 종료 화면
    elif st.session_state.step == 2:
        st.balloons()
        st.markdown(f"""
        <div style="text-align: center; margin: 30px 0;">
            <h2>🏆 최종 점수</h2>
            <h1 style="color: #FF4B4B; font-size: 40px;">{int(st.session_state.score)} 점</h1>
            <p style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-top: 20px;">
                📸 스크린샷을 찍어 결과를 공유하세요
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 다시 풀기", use_container_width=True):
            st.session_state.step = 0
            st.rerun()

# --- 기능 함수 ---
def check_answer(user, answer):
    elapsed = time.time() - st.session_state.start_time
    remaining = 10 - elapsed
    
    if remaining < 0:
        st.toast(f"⏰ 시간 초과! (정답: {answer})", icon="⚠️")
        time.sleep(1)
        next_question()
        return

    if user == answer:
        score = 100 + (remaining * 10)
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