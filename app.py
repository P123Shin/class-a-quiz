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
    st.session_state.feedback = None

# --- 스타일 설정 (모바일 1줄 4버튼 강제) ---
st.markdown("""
    <style>
        /* 카톡 상단바 가림 방지 여백 */
        .block-container {
            padding-top: 3rem !important;
            padding-left: 0.5rem !important; /* 좌우 여백도 최소화 */
            padding-right: 0.5rem !important;
        }
        /* 버튼 스타일: 1줄 4개를 위해 극단적 축소 */
        div.stButton > button {
            width: 100% !important;
            padding: 0.4rem 0.1rem !important; /* 위아래 패딩 약간 확보, 좌우는 최소 */
            font-size: 12px !important; /* 폰트 크기 축소 */
            margin: 0px !important;
            min-height: 0px !important;
            height: auto !important;
            white-space: nowrap; /* 줄바꿈 절대 방지 */
        }
        /* 컬럼 사이 간격 거의 없앰 */
        div[data-testid="column"] {
            gap: 0.1rem !important;
            min-width: 0px !important; /* 좁아져도 버티도록 */
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    # [Step 0] 시작 화면
    if st.session_state.step == 0:
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>🧐 Guess Who?</h3>", unsafe_allow_html=True)
        
        pool, male_names, female_names = load_data()
        if pool is None: st.error("데이터 오류"); return

        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <p style='font-size: 14px;'>총 {len(pool)}명 중 10문제</p>
            <p style='color: #FF4B4B; font-weight: bold; font-size: 14px;'>빨리 맞출수록 고득점!🎶</p>
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
            st.session_state.feedback = None
            st.session_state.start_time = time.time()
            st.rerun()

    # [Step 1] 문제 풀이 화면
    elif st.session_state.step == 1:
        
        # 🟢 [피드백 화면] (O / X 표시)
        if st.session_state.feedback:
            st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
            
            if st.session_state.feedback['is_correct']:
                # 정답 화면 (O)
                st.markdown("""
                <div style='text-align: center;'>
                    <h1 style='color: #4CAF50; font-size: 120px; margin: 0;'>⭕</h1>
                    <h2 style='color: #4CAF50; margin-top: 10px;'>정답!</h2>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 오답 화면 (X) - 요청하신 대로 수정 (빨간 이름 제거, 한 줄 표시)
                correct_name = st.session_state.feedback['correct_answer']
                st.markdown(f"""
                <div style='text-align: center;'>
                    <h1 style='color: #FF4B4B; font-size: 120px; margin: 0;'>❌</h1>
                    <h3 style='color: #333; margin-top: 20px;'>정답은 <b>{correct_name}</b></h3>
                </div>
                """, unsafe_allow_html=True)
            
            time.sleep(1.5)
            next_question()
            st.rerun()
            return

        # ⚪ [문제 화면] 레이아웃 순서 변경
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        current_q = st.session_state.quiz_set[st.session_state.q_idx]
        current_idx = st.session_state.q_idx + 1

        # 1. 질문 헤더
        st.markdown(f"""
            <div style='display: flex; align-items: center; margin-bottom: 10px; justify-content: center;'>
                <h3 style='margin: 0; margin-right: 8px; color: #31333F;'>Q{current_idx}</h3>
                <span style='font-size: 16px; font-weight: bold;'>이 사람은 누구일까요?</span>
            </div>
            """, unsafe_allow_html=True)

        # 2. 이미지 (화면 꽉 차게)
        if os.path.exists(current_q['img']):
            resized_img = load_and_resize_image(current_q['img'])
            if resized_img:
                st.image(resized_img, use_container_width=True)
        else:
            st.error("이미지 없음")

        # 3. 보기 버튼 (1줄 4개 수평 나열)
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) # 간격
        # columns 사이에 갭을 아예 없애기 위해 gap 지정 안 함
        c1, c2, c3, c4 = st.columns(4)
        opts = current_q['options']
        ans = current_q['answer']

        def handle_click(choice):
            elapsed = time.time() - st.session_state.start_time
            if elapsed > 10.5:
                st.session_state.feedback = {'is_correct': False, 'correct_answer': ans}
            else:
                score_gain = 100 + (max(0, 10 - elapsed) * 10)
                if choice == ans:
                    st.session_state.score += score_gain
                    st.session_state.feedback = {'is_correct': True}
                else:
                    st.session_state.feedback = {'is_correct': False, 'correct_answer': ans}
            
        with c1: st.button(opts[0], key="btn0", on_click=handle_click, args=(opts[0],), use_container_width=True)
        with c2: st.button(opts[1], key="btn1", on_click=handle_click, args=(opts[1],), use_container_width=True)
        with c3: st.button(opts[2], key="btn2", on_click=handle_click, args=(opts[2],), use_container_width=True)
        with c4: st.button(opts[3], key="btn3", on_click=handle_click, args=(opts[3],), use_container_width=True)

        # 4. 타이머 (보기 밑에 중앙 정렬)
        timer_placeholder = st.empty()

        # 타이머 루프
        for i in range(10, -1, -1):
            timer_html = f"""
            <div style='text-align: center; font-size: 20px; font-weight: bold; color: #FF4B4B; margin-top: 15px;'>
                ⏰ {i}
            </div>
            """
            timer_placeholder.markdown(timer_html, unsafe_allow_html=True)
            
            if i == 0:
                st.session_state.feedback = {'is_correct': False, 'correct_answer': ans}
                st.rerun()
            
            time.sleep(1)

    # [Step 2] 종료 화면
    elif st.session_state.step == 2:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        st.balloons()
        
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <h2>🏆 최종 점수</h2>
            <h1 style="color: #FF4B4B; font-size: 50px;">{int(st.session_state.score)} 점</h1>
            <p style="background-color: #f0f2f6; padding: 12px; border-radius: 10px; margin-top: 30px; font-weight: bold; font-size: 14px;">
                📸 스크린샷을 찍어 결과를 공유하세요
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 다시 풀기", use_container_width=True):
            st.session_state.step = 0
            st.rerun()

# --- 내부 함수 ---
def next_question():
    st.session_state.feedback = None
    if st.session_state.q_idx + 1 < len(st.session_state.quiz_set):
        st.session_state.q_idx += 1
        st.session_state.start_time = time.time()
    else:
        st.session_state.step = 2

if __name__ == "__main__":
    main()