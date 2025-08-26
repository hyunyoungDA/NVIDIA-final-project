# 통합 키오스크 프로젝트

이 프로젝트는 AI 얼굴 인식, 일반 키오스크, 음성 주문 키오스크를 통합한 완전한 키오스크 시스템입니다.

## 📁 프로젝트 구조

```
integrated_kiosk_project/
├── 01_face_recognition_app.py    # 얼굴 인식 앱 (포트 8501)
├── 02_normal_kiosk_app.py        # 일반 키오스크 앱 (포트 8502)
├── 03_voice_kiosk_app.py         # 음성 주문 키오스크 앱 (포트 8503)
├── menu_data.py                  # 메뉴 데이터
├── requirements.txt              # 필요한 패키지 목록
├── public/                       # 메뉴 이미지 파일들
└── README.md                     # 이 파일
```

## 🚀 실행 방법

### 1. 환경 설정

먼저 필요한 패키지들을 설치합니다:

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가합니다:

```env
# Face++ API (얼굴 인식용)
FACE_API_KEY=your_face_api_key_here
FACE_API_SECRET=your_face_api_secret_here

# OpenAI API (음성 주문용)
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 앱 실행 (권장 방법)

**Windows에서 한 번에 모든 앱 실행:**
```bash
run_all.bat
```

이 명령어를 실행하면:
- **얼굴 인식 앱 (포트 8501)**: 포어그라운드에서 실행되며 브라우저가 자동으로 열림
- **일반 키오스크 (포트 8502)**: 백그라운드에서 실행 (브라우저 자동 열림 없음)
- **음성 주문 키오스크 (포트 8503)**: 백그라운드에서 실행 (브라우저 자동 열림 없음)

### 4. 수동 실행 (개별 앱 테스트용)

개별 앱을 테스트하고 싶다면 각각 터미널에서 실행할 수 있습니다:

**얼굴 인식 앱:**
```bash
streamlit run 01_face_recognition_app.py --server.port 8501
```

**일반 키오스크:**
```bash
streamlit run 02_normal_kiosk_app.py --server.port 8502
```

**음성 주문 키오스크:**
```bash
streamlit run 03_voice_kiosk_app.py --server.port 8503
```

## 🔄 워크플로우

1. **시작**: `run_all.bat` 실행으로 모든 앱이 자동으로 시작됨
2. **얼굴 인식 (포트 8501)**: 사용자의 얼굴을 인식하여 나이를 추정
3. **자동 라우팅**: 
   - 65세 미만 → 일반 키오스크 (포트 8502)로 자동 이동
   - 65세 이상 → 음성 주문 키오스크 (포트 8503)로 자동 이동
4. **주문 및 결제**: 각 키오스크에서 메뉴 선택 및 결제 진행
5. **자동 복귀**: 결제 완료 후 5초 뒤 자동으로 얼굴 인식 페이지로 돌아감

## 🛠️ 주요 기능

### 얼굴 인식 앱 (01_face_recognition_app.py)
- 실시간 카메라를 통한 얼굴 인식
- Face++ API를 사용한 나이 추정
- 자동 라우팅 기능

### 일반 키오스크 (02_normal_kiosk_app.py)
- 터치 기반 메뉴 선택
- 알레르기 및 식단 필터링
- 장바구니 관리
- 결제 처리

### 음성 주문 키오스크 (03_voice_kiosk_app.py)
- 음성 인식 (STT) 및 음성 합성 (TTS)
- AI 챗봇을 통한 자연어 주문
- LangChain 기반 대화 처리
- 시각적 메뉴와 음성 주문 병행

## 📋 메뉴 정보

- **메인**: 버거, 랩, 보울, 샐러디
- **사이드**: 감자튀김, 치즈스틱
- **음료**: 콜라, 사이다
- **디저트**: 아이스크림, 팥빙수

각 메뉴에는 알레르기 정보, 식단 정보, 가격, 조리시간 등이 포함되어 있습니다.

## 🔧 문제 해결

### run_all.bat 실행 문제
- Windows 환경에서만 실행 가능
- PowerShell이나 명령 프롬프트에서 실행
- 권한 문제 시 관리자 권한으로 실행

### 음성 인식 문제
- 마이크 권한 확인
- PyAudio 설치 문제 시: `pip install pipwin` 후 `pipwin install pyaudio`

### 얼굴 인식 문제
- 카메라 권한 확인
- Face++ API 키 설정 확인

### 포트 충돌
- 다른 포트 사용: `--server.port 8504` 등으로 변경
- 백그라운드 앱 접속: 브라우저에서 `http://localhost:8502` 또는 `http://localhost:8503` 직접 접속

## 📝 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.
