#!/bin/bash

echo "🚀 통합 키오스크 시스템을 시작합니다..."

# 현재 디렉토리 확인
if [ ! -f "01_face_recognition_app.py" ]; then
    echo "❌ 오류: 이 스크립트는 integrated_kiosk_project 폴더에서 실행해야 합니다."
    exit 1
fi

# 포트 사용 중인지 확인
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ 포트 $1이 이미 사용 중입니다. 다른 프로세스를 종료하고 다시 시도해주세요."
        exit 1
    fi
}

echo "🔍 포트 상태를 확인합니다..."
check_port 8501
check_port 8502
check_port 8503

echo "✅ 포트가 사용 가능합니다."

# 백그라운드에서 일반 키오스크 실행 (포트 8502)
echo "📱 일반 키오스크를 백그라운드에서 시작합니다 (포트 8502)..."
nohup streamlit run 02_normal_kiosk_app.py --server.port 8502 --server.headless true > /dev/null 2>&1 &
NORMAL_PID=$!

# 백그라운드에서 음성 키오스크 실행 (포트 8503)
echo "🎤 음성 키오스크를 백그라운드에서 시작합니다 (포트 8503)..."
nohup streamlit run 03_voice_kiosk_app.py --server.port 8503 --server.headless true > /dev/null 2>&1 &
VOICE_PID=$!

# 잠시 대기
sleep 3

# 포어그라운드에서 얼굴 인식 앱 실행 (포트 8501)
echo "📷 얼굴 인식 앱을 시작합니다 (포트 8501)..."
echo "🌐 브라우저가 자동으로 열립니다."
echo ""
echo "📋 실행 중인 앱들:"
echo "   - 얼굴 인식: http://localhost:8501 (포어그라운드)"
echo "   - 일반 키오스크: http://localhost:8502 (백그라운드)"
echo "   - 음성 키오스크: http://localhost:8503 (백그라운드)"
echo ""
echo "🛑 종료하려면 Ctrl+C를 누르세요."

# 프로세스 종료 함수
cleanup() {
    echo ""
    echo "🔄 앱들을 종료합니다..."
    kill $NORMAL_PID 2>/dev/null
    kill $VOICE_PID 2>/dev/null
    echo "✅ 모든 앱이 종료되었습니다."
    exit 0
}

# Ctrl+C 시그널 처리
trap cleanup SIGINT

# 얼굴 인식 앱 실행
streamlit run 01_face_recognition_app.py --server.port 8501
