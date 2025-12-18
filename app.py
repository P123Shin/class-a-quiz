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
        
        # 데이터 전처리 (성별 대문자 변환, 공백 제거)
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

# --- 2. 이미지 리사이징 (300x300 고정) ---
def load_and_resize_image(image_path, size=(300, 300)):
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

def main():
    # [공통] 제목 표시 (중앙 정렬)
    # 시작 화면과 종료 화면에만 타이틀을 띄우기 위해 step 체크
    if st.session_state.step == 0 or st.session_state.step == 2:
        st.markdown("""
            <h1 style='text-align: center;'>🎓 A반 동기 맞추기 퀴즈 🎓</h1>
        """, unsafe_allow_html=True)

    # [Step 0] 시작 화면
    if st.session_state.step == 0:
        pool, male_names, female_names = load_data()
        
        if pool is None:
            st.error("❌ 데이터 파일 오류 (quiz_data.xlsx 확인 필요)")
            return

        # 안내 문구 (중앙 정렬)
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 30px;'>
            <h3>총 {len(pool)}명 중 10문제가 출제됩니다</h3>
            <p style='font-size: 18px; color: #FF4B4B; font-weight: bold;'>
                답을 빨리 맞출수록 점수가 올라갑니다🎶
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 버튼을 중앙 느낌으로 배치하기 위해 컬럼 사용 (모바일 꽉 찬 버튼 선호시 그대로 둠)
        # 여기서는 use_container_width=True로 꽉 차게 만듭니다.
        if st.button("게임 시작", use_container_width=True):
            # 문제 출제 로직
            sample_count = min(10, len(pool))
            selected_questions = random.sample(pool, sample_count)
            
            for q in selected_questions:
                correct = q['answer']
                q_gender = q['gender']
                
                # 성별 필터링
                if q_gender == 'M':
                    wrong_pool = [name for name in male_names if name != correct]
                else:
                    wrong_pool = [name for name in female_names if name != correct]
                
                if len(wrong_pool) < 3:
                    all_names = male_names + female_names
                    wrong_pool = [name for name in all_names if name != correct]
                
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
        # 문제 화면은 중앙 정렬보다 기능 위주 배치
        current_q = st.session_state.quiz_set[st.session_state.q_idx]
        total = len(st.session_state.quiz_set)
        idx = st.session_state.q_idx + 1
        
        st.caption(f"Question {idx} / {total}")
        st.progress(idx / total)

        elapsed = time.time() - st.session_state.start_time
        remaining = 10 - elapsed
        
        if remaining <= 0:
            st.error("⏰ 시간 초과!")
            time.sleep(0.5)
            next_question()
            return

        # 이미지 (300x300)
        if os.path.exists(current_q['img']):
            resized_img = load_and_resize_image(current_q['img'])
            if resized_img:
                # 이미지를 가운데 정렬하는 트릭
                col1, col2, col3 = st.columns([1, 6, 1])
                with col2:
                    st.image(resized_img, use_container_width=True)
        
        st.markdown("<h3 style='text-align: center;'>이 사람은 누구일까요?</h3>", unsafe_allow_html=True)
        
        # 보기 버튼
        cols = st.columns(2)
        for i, opt in enumerate(current_q['options']):
            if cols[i % 2].button(opt, use_container_width=True):
                check_answer(opt, current_q['answer'], remaining)

    # [Step 2] 종료 화면
    elif st.session_state.step == 2:
        st.balloons()
        
        # 점수 및 안내 문구 중앙 정렬
        st.markdown(f"""
        <div style="text-align: center; margin-top: 20px; margin-bottom: 20px;">
            <h2>🏆 최종 점수</h2>
            <h1 style="color: #FF4B4B; font-size: 50px;">{int(st.session_state.score)} 점</h1>
            <br>
            <p style="font-size: 16px; font-weight: bold; background-color: #f0f2f6; padding: 10px; border-radius: 10px;">
                📸 스크린 샷을 찍어 결과를 공유하세요
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