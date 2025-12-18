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
    st.session_state.feedback = None # 정답/오답 판정 상태 저장용

# --- 스타일 설정 ---
st.markdown("""
    <style>
        /* 카톡 상단바 가림 방지 */
        .block-container {
            padding-top: 3rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* 버튼 스타일 최적화 */
        div.stButton > button {
            width: 100%;
            padding: 0.3rem 0.1rem !important;
            font-size: 13px !important;
            margin: 0px !important;
            height: auto !important;
            white-space: nowrap; 
        }
        div[data-testid="column"] {
            padding: 0rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    # [Step 0] 시작 화면
    if st.session_state.step == 0:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>🧐 Guess Who?</h3>", unsafe_allow_html=True)
        
        pool, male_names, female_names = load_data()
        if pool is None: st.error("데이터 오류"); return

        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 30px;'>
            <p>총 {len(pool)}명 중 10문제 출제</p>
            <p style='color: #FF4B4B; font-weight: bold;'>빨리 맞출수록 점수가 올라갑니다🎶</p>
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
        
        # 🟢 [중요] 피드백 화면 (O / X 표시)
        # feedback 상태가 있으면 문제 화면 대신 이걸 보여줌
        if st.session_state.feedback:
            st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True) # 중앙 정렬용 여백
            
            if st.session_state.feedback['is_correct']:
                # 정답 화면 (O)
                st.markdown("""
                <div style='text-align: center;'>
                    <h1 style='color: #4CAF50; font-size: 150px; margin: 0;'>⭕</h1>
                    <h2 style='color: #4CAF50;'>정답!</h2>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 오답 화면 (X)
                correct_name = st.session_state.feedback['correct_answer']
                st.markdown(f"""
                <div style='text-align: center;'>
                    <h1 style='color: #FF4B4B; font-size: 150px; margin: 0;'>❌</h1>
                    <h3 style='color: #333;'>정답은...</h3>
                    <h2 style='color: #FF4B4B; font-size: 40px;'>{correct_name}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # 1.5초 보여주고 다음 문제로 넘어감
            time.sleep(1.5)
            next_question() # 여기서 인덱스 증가하고 step 유지
            st.rerun() # 화면 갱신
            return # 아래 코드 실행 방지

        # ⚪ [일반] 문제 화면 (피드백이 없을 때)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        current_q = st.session_state.quiz_set[st.session_state.q_idx]
        current_idx = st.session_state.q_idx + 1

        # 질문 헤더
        st.markdown(f"""
            <div style='display: flex; align-items: center; margin-bottom: 5px;'>
                <h3 style='margin: 0; margin-right: 8px; color: #31333F;'>Q{current_idx}</h3>
                <span style='font-size: 16px; font-weight: bold;'>이 사람은 누구일까요?</span>
            </div>
            """, unsafe_allow_html=True)

        # 이미지(7) : 타이머(3)
        col_img, col_timer = st.columns([7, 3])
        
        with col_img:
            if os.path.exists(current_q['img']):
                resized_img = load_and_resize_image(current_q['img'])
                if resized_img:
                    st.image(resized_img, use_container_width=True)
            else:
                st.error("이미지 없음")

        timer_placeholder = col_timer.empty()

        # 보기 버튼 (1줄 4개)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4, gap="small")
        opts = current_q['options']
        ans = current_q['answer']

        # 버튼 클릭 콜백
        def handle_click(choice):
            elapsed = time.time() - st.session_state.start_time
            # 시간 초과인지 확인 (약간의 오차 허용)
            if elapsed > 10.5:
                # 시간 초과로 처리
                st.session_state.feedback = {'is_correct': False, 'correct_answer': ans}
            else:
                score_gain = 100 + (max(0, 10 - elapsed) * 10)
                if choice == ans:
                    st.session_state.score += score_gain
                    st.session_state.feedback = {'is_correct': True}
                else:
                    st.session_state.feedback = {'is_correct': False, 'correct_answer': ans}
            
            # 여기서 rerun하면 위쪽의 `if st.session_state.feedback:` 블록이 실행됨
            
        with c1: st.button(opts[0], key="btn0", on_click=handle_click, args=(opts[0],), use_container_width=True)
        with c2: st.button(opts[1], key="btn1", on_click=handle_click, args=(opts[1],), use_container_width=True)
        with c3: st.button(opts[2], key="btn2", on_click=handle_click, args=(opts[2],), use_container_width=True)
        with c4: st.button(opts[3], key="btn3", on_click=handle_click, args=(opts[3],), use_container_width=True)

        # 타이머 루프
        for i in range(10, -1, -1):
            timer_html = f"""
            <div style='text-align: center; font-size: 24px; font-weight: bold; color: #FF4B4B; margin-top: 20px;'>
                ⏰ {i}
            </div>
            """
            timer_placeholder.markdown(timer_html, unsafe_allow_html=True)
            
            # 0초가 되면 시간초과 처리
            if i == 0:
                st.session_state.feedback = {'is_correct': False, 'correct_answer': ans}
                st.rerun() # 피드백 화면을 보여주기 위해 리런
            
            time.sleep(1)

    # [Step 2] 종료 화면
    elif st.session_state.step == 2:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        st.balloons()
        
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <h2>🏆 최종 점수</h2>
            <h1 style="color: #FF4B4B; font-size: 50px;">{int(st.session_state.score)} 점</h1>
            <p style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-top: 30px; font-weight: bold;">
                📸 스크린샷을 찍어 결과를 공유하세요
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 다시 풀기", use_container_width=True):
            st.session_state.step = 0
            st.rerun()

# --- 내부 함수 ---
def next_question():
    # 다음 문제 인덱스로 이동, 피드백 초기화
    st.session_state.feedback = None
    if st.session_state.q_idx + 1 < len(st.session_state.quiz_set):
        st.session_state.q_idx += 1
        st.session_state.start_time = time.time()
    else:
        st.session_state.step = 2

if __name__ == "__main__":
    main()