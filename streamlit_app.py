import streamlit as st
import requests
import base64
import time
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import webbrowser
import threading

API_ENDPOINT = "http://localhost:3001/api/face"  # 포트를 3001로 변경
TARGET_URL = "https://www.naver.com"

# 페이지 설정
st.set_page_config(
    page_title="AI 얼굴 나이 인식 키오스크",
    page_icon="👴",
    layout="wide"
)

# 세션 상태 초기화
if 'age_detected' not in st.session_state:
    st.session_state.age_detected = None
if 'detection_complete' not in st.session_state:
    st.session_state.detection_complete = False
if 'detection_started' not in st.session_state:
    st.session_state.detection_started = False
if 'show_result' not in st.session_state:
    st.session_state.show_result = False
if 'video_frames' not in st.session_state:
    st.session_state.video_frames = []

def capture_video_frames():
    """3초 동안 카메라로 5장의 사진을 캡처하는 함수"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("카메라를 열 수 없습니다.")
        return []
    
    frames = []
    start_time = time.time()
    capture_duration = 3  # 3초
    target_frames = 5  # 5장의 사진
    
    # 진행률 표시
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        while time.time() - start_time < capture_duration and len(frames) < target_frames:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # OpenCV BGR을 RGB로 변환
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 프레임을 PIL Image로 변환하여 저장
            pil_image = Image.fromarray(frame_rgb)
            frames.append(pil_image)
            
            # 진행률 업데이트
            elapsed = time.time() - start_time
            progress = min(elapsed / capture_duration, 1.0)
            progress_placeholder.progress(progress)
            status_placeholder.text(f"📸 사진 촬영 중... {len(frames)}/5장 ({elapsed:.1f}초)")
            
            # 0.6초 대기 (5장을 3초에 걸쳐 촬영)
            time.sleep(0.6)
            
    finally:
        cap.release()
        progress_placeholder.progress(1.0)
        status_placeholder.text(f"✅ 사진 촬영 완료!")
    
    return frames

def detect_age_from_frames(frames):
    """여러 프레임에서 나이를 감지하는 함수"""
    if not frames:
        return None
    
    ages = []
    successful_detections = 0
    
    # 5장의 사진을 모두 분석
    with st.spinner("🔍 AI가 사진에서 나이를 분석하고 있습니다..."):
        for i, frame in enumerate(frames):
            try:
                # 이미지 base64 변환
                buffered = BytesIO()
                frame.save(buffered, format="JPEG", quality=85)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # API 요청
                res = requests.post(API_ENDPOINT, json={"imageBase64": img_str, "frameCount": i}, timeout=10)
                
                if res.status_code == 200:
                    data = res.json()
                    
                    if data.get("face_detected") and data.get("age") is not None:
                        age = data.get("age")
                        ages.append(age)
                        successful_detections += 1
                else:
                    continue
                    
            except:
                continue
    
    # 결과 반환
    if successful_detections > 0:
        average_age = int(sum(ages) / len(ages))
        return average_age
    else:
        return None

def main():
    st.title("👴 AI 얼굴 나이 인식 키오스크")
    st.markdown("---")
    
    # API 서버 상태 확인
    try:
        test_response = requests.get(API_ENDPOINT.replace("/api/face", ""), timeout=5)
        if test_response.status_code == 200:
            pass  # 성공 시 아무것도 하지 않음
        else:
            st.warning(f"⚠️ API 서버 응답: {test_response.status_code}")
    except:
        st.error("❌ Next.js API 서버에 연결할 수 없습니다. 'npm run dev'를 실행하세요.")
        st.stop()
    
    # 자동으로 얼굴 인식 시작
    if not st.session_state.detection_started:
        st.session_state.detection_started = True
    
    # 나이 인식 진행 중
    if not st.session_state.detection_complete:
        st.subheader("🔍 실시간 얼굴 인식")
        st.info("카메라가 나이 인식을 위해 사진을 촬영합니다.")
        
        # 바로 촬영 시작
        frames = capture_video_frames()
        st.session_state.video_frames = frames
        
        if frames:
            # 5장의 사진 중 첫 번째 사진만 표시
            st.success(f"✅ 사진 촬영 완료!")
            st.image(frames[2], caption="촬영된 사진", use_column_width=True)
            
            # 나이 인식
            age = detect_age_from_frames(frames)
            
            if age is not None:
                st.session_state.age_detected = age
                st.session_state.detection_complete = True
                st.session_state.show_result = True
                st.rerun()
            else:
                st.error("얼굴이 감지되지 않았습니다.")
                st.button("🔄 다시 시도", on_click=lambda: st.rerun())
        else:
            st.error("사진 촬영에 실패했습니다.")
            st.button("🔄 다시 시도", on_click=lambda: st.rerun())
    
    # 나이 인식 완료 후 결과 표시
    elif st.session_state.detection_complete and st.session_state.age_detected is not None and st.session_state.show_result:
        age = st.session_state.age_detected
        
        st.success(f"✅ 나이 인식 완료: {age}세")
        st.markdown("---")
        
        # 결과 표시
        if age < 65:
            st.subheader("🎯 65세 미만")
            st.info(f"추정 나이: {age}세 -> 자동으로 다음 페이지로 이동합니다.")
            
            # 자동 URL 이동
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # 3초 후 자동으로 웹사이트 열기
                time.sleep(3)
                webbrowser.open(TARGET_URL)
                
        else:
            st.subheader("🍽 65세 이상")
            st.info(f"추정 나이: {age}세 -> 원하시는 옵션을 선택해주세요.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🍽 먹고 가기", use_container_width=True, type="primary"):
                    st.success("먹고 가기를 선택하셨습니다!")
                    st.balloons()
                    
            with col2:
                if st.button("🥡 포장", use_container_width=True, type="primary"):
                    st.success("포장을 선택하셨습니다!")
                    st.balloons()
        
        # 다시 시작하기 버튼 (자동 재시작 제거)
        st.markdown("---")
        if st.button("🔄 다시 시작", use_container_width=True):
            st.session_state.age_detected = None
            st.session_state.detection_complete = False
            st.session_state.detection_started = False
            st.session_state.show_result = False
            st.rerun()

if __name__ == "__main__":
    main()
