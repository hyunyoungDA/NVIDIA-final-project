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
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 Face++ API 설정 가져오기
FACE_API_KEY = os.getenv("FACE_API_KEY")
FACE_API_SECRET = os.getenv("FACE_API_SECRET")
TARGET_URL1 = os.getenv("TARGET_URL", "http://localhost:8507")
TARGET_URL2 = os.getenv("TARGET_URL2","http://localhost:8505")

# Face++ API 설정 확인
if not FACE_API_KEY or not FACE_API_SECRET:
    st.error("❌ Face++ API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
    st.stop()

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

def call_face_api(image_base64):
    """Face++ API를 직접 호출하여 나이를 감지하는 함수"""
    try:
        # Face++ API URL
        api_url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
        
        # Base64 이미지 데이터 준비 (data:image/jpeg;base64, 부분 제거)
        image_data = image_base64 if ',' not in image_base64 else image_base64.split(',')[1]
        
        # FormData 생성
        form_data = {
            'api_key': FACE_API_KEY,
            'api_secret': FACE_API_SECRET,
            'image_base64': image_data,
            'return_attributes': 'age'
        }
        
        # Face++ API 호출
        response = requests.post(api_url, data=form_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Face++ 응답 처리
            if data.get("error_message"):
                st.error(f"Face++ API 오류: {data.get('error_message')}")
                return None
            
            if data.get("faces") and len(data.get("faces", [])) > 0:
                face = data["faces"][0]
                attributes = face.get("attributes", {})
                
                # 나이 추정
                age = attributes.get("age", {}).get("value") if attributes.get("age") else None
                
                if age is not None:
                    st.success(f"✅ Face++ API 성공: {age}세 감지됨")
                    return age
                else:
                    st.warning("⚠️ 얼굴은 감지되었지만 나이를 추정할 수 없습니다.")
                    return None
            else:
                st.warning("⚠️ 얼굴이 감지되지 않았습니다.")
                return None
        else:
            st.error(f"Face++ API 요청 실패: {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Face++ API 요청 시간 초과")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Face++ API 요청 오류: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류: {e}")
        return None

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
                
                # Face++ API 직접 호출
                age = call_face_api(img_str)
                
                if age is not None:
                    ages.append(age)
                    successful_detections += 1
                    
            except Exception as e:
                st.error(f"프레임 {i+1} 처리 오류: {e}")
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
    
    # 자동으로 얼굴 인식 시작
    if not st.session_state.detection_started:
        st.session_state.detection_started = True
    
    # 나이 인식 진행 중
    if not st.session_state.detection_complete:
        st.subheader("🔍 실시간 얼굴 인식")
        
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
                webbrowser.open(TARGET_URL1)
                
        else:
            st.subheader("🍽 65세 이상")
            st.info(f"추정 나이: {age}세 -> 자동으로 다음 페이지로 이동합니다.")
            
            # 자동 URL 이동
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # 3초 후 자동으로 웹사이트 열기
                time.sleep(3)
                webbrowser.open(TARGET_URL2)
        
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
