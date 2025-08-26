# AI 얼굴 나이 인식 키오스크

스트림릿을 사용한 실시간 얼굴 나이 인식 키오스크 애플리케이션입니다.

## 🚀 주요 기능

- **3초 실시간 얼굴 인식**: 카메라로 3초간 5장의 사진을 촬영하여 나이를 자동 인식
- **자동 나이 판단**: 65세 기준으로 자동 분류
- **스마트 라우팅**: 
  - 65세 미만: 지정된 웹사이트로 자동 이동
  - 65세 이상: "먹고 가기" 또는 "포장" 선택 화면
- **실시간 진행률 표시**: 인식 과정을 시각적으로 확인
- **직접 Face++ API 호출**: 별도 API 서버 없이 스트림릿에서 직접 실행

## 📋 사용 방법

1. **환경 변수 설정** (아래 설정 섹션 참조)
2. **의존성 설치**
3. **스트림릿 앱 실행**
4. **카메라 앞에서 3초간 얼굴을 보여주기**
5. **AI가 자동으로 나이를 인식**
6. **나이에 따라 자동으로 다음 단계로 이동**

## 🛠️ 설치 및 실행

### 1. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# Face++ API 설정
FACE_API_KEY=your_actual_api_key_here
FACE_API_SECRET=your_actual_api_secret_here

# 타겟 URL
TARGET_URL=https://www.naver.com
```

**⚠️ 보안 주의사항:**
- `.env` 파일은 절대 Git에 커밋하지 마세요
- API 키는 안전하게 보관하고 공개하지 마세요
- `.env.example` 파일을 참고하여 필요한 환경 변수를 설정하세요

### 2. 의존성 설치

```bash
# Python 의존성만 설치 (Node.js 불필요)
pip install -r requirements.txt
```

### 3. 스트림릿 앱 실행
```bash
streamlit run streamlit_app.py
```

## 🔧 설정

- **FACE_API_KEY**: Face++ API 키 (필수)
- **FACE_API_SECRET**: Face++ API 시크릿 (필수)
- **TARGET_URL**: 65세 미만 사용자가 이동할 웹사이트 URL

## 📱 화면 구성

### 메인 화면
- Face++ API 연결 상태 확인
- 자동 시작

### 인식 화면
- 실시간 카메라 스트리밍
- 3초 카운트다운
- 진행률 바
- 인식 상태 표시

### 결과 화면
- **65세 미만**: 웹사이트 이동
- **65세 이상**: 먹고 가기/포장 선택 버튼
- 다시 시작 버튼

## 🎯 기술 스택

- **Frontend**: Streamlit
- **Computer Vision**: OpenCV
- **Face Recognition**: Face++ API (직접 호출)
- **Image Processing**: PIL, NumPy
- **Environment**: python-dotenv

## 📝 주의사항

- 카메라 권한이 필요합니다
- 인터넷 연결이 필요합니다 (Face++ API 사용)
- Face++ API 사용량 제한이 있을 수 있습니다
- **API 키는 절대 공개 저장소에 업로드하지 마세요**
- **별도의 API 서버가 필요하지 않습니다**

## 🔄 업데이트 내역

- v1.0: 기본 얼굴 인식 기능
- v2.0: 3초 실시간 인식 및 자동 라우팅 기능 추가
- v3.0: 환경 변수 기반 설정 및 보안 강화
- v4.0: API 서버 제거, 스트림릿에서 직접 Face++ API 호출