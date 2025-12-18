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

# --- 2. 이미지 리사이징 (250x250) ---
# 폰 화면에서 적당히 2/3 정도 차지하도록 크기 지정
def load_and_resize_image(image_path, size=(250, 250)):
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

# --- [핵심] 스타일 설정 (강제 가로 정렬) ---
st.markdown("""
    <style>
        /* 1. 모바일 자동 세로 정렬 방지 (가장 중요) */
        /* 화면이 좁아도 컬럼의 너비를 강제로 25%로 고정합니다. */
        [data-testid="column"] {
            width: 25% !important;
            flex: 1 1 25% !important;
            min-width: 0 !important;
        }
        
        /* 2. 상단바 여백 */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* 3. 버튼 스타일: 아주 작고 타이트하게 */
        div.stButton > button {
            width: 100% !important;
            padding: 0.5rem 0.1rem !important;
            font-size: 12px !important;
            margin: 0px !important;
            height: auto !important;
            white-space: nowrap; /* 줄바꿈 방지 */
            border-radius: 5px;
        }
        
        /* 4. 이미지 중앙 정렬을 위한 컨테이너 */
        .img-container {
            display: flex;
            justify-content: center;
            margin-bottom: 10px;
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
            <p>총 {len(pool)}명 중 10문제</p>
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
            st.session_state.feedback = None
            st.session_state.start_time = time.time()
            st.rerun()

    # [Step 1] 문제 풀이 화면
    elif st.session_state.step == 1:
        
        # 🟢 [피드백 화면] 정답/오답 시 전체 화면 덮어씌움 (놓칠 일 없음)
        if st.session_state.feedback:
            st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
            
            if st.session_state.feedback['is_correct']:
                # 정답 (O)
                st.markdown("""
                <div style='text-align: center;'>
                    <h1 style='color: #4CAF50; font-size: 100px; margin: 0;'>⭕</h1>
                    <h2 style='color: #4CAF50;'>정답!</h2>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 오답 (X)
                correct_name = st.session_state.feedback['correct_answer']
                st.markdown(f"""
                <div style='text-align: center;'>
                    <h1 style='color: #FF4B4B; font-size: 100px; margin: 0;'>❌</h1>
                    <h3 style='color: #333; margin-top: 10px;'>정답은 <b>{correct_name}</b></h3>
                </div>
                """, unsafe_allow_html=True)
            
            time.sleep(1.5)
            next_question()
            st.rerun()
            return

        # ⚪ [문제 화면]
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        current_q = st.session_state.quiz_set[st.session_state.q_idx]
        current_idx = st.session_state.q_idx + 1

        # 1. 질문 헤더
        st.markdown(f"""
            <div style='display: flex; align-items: center; justify-content: center; margin-bottom: 5px;'>
                <h3 style='margin: 0; margin-right: 8px; color: #31333F;'>Q{current_idx}</h3>
                <span style='font-size: 15px; font-weight: bold;'>이 사람은 누구일까요?</span>
            </div>
            """, unsafe_allow_html=True)

        # 2. 이미지 (중앙 정렬 + 크기 고정)
        # use_container_width=True를 빼고, width=220 픽셀 고정으로 넣습니다.
        if os.path.exists(current_q['img']):
            resized_img = load_and_resize_image(current_q['img'])
            if resized_img:
                # 스트림릿 컬럼을 안 쓰고 HTML div로 중앙 정렬 유도할 수도 있지만,
                # 가장 확실한 건 컬럼 3개 중 가운데에 넣는 것입니다.
                c_left, c_center, c_right = st.columns([1, 10, 1]) 
                with c_center:
                    # 여기서 width를 지정하면 화면 꽉 차는 걸 막을 수 있습니다.
                    st.image(resized_img, width=220) 
        else:
            st.error("이미지 없음")

        # 3. 보기 버튼 (1줄 4개 수평 나열)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # CSS로 강제했으므로 이제 columns(4)가 세로로 안 쌓입니다.
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

        for i in range(10, -1, -1):
            timer_html = f"""
            <div style='text-align: center; font-size: 20px; font-weight: bold; color: #FF4B4B; margin-top: 10px;'>
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