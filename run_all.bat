@echo off
echo Starting Integrated Kiosk System...
echo.

echo Starting Normal Kiosk App (Port 8502) in background...
start /b "Normal Kiosk" cmd /c "streamlit run 02_normal_kiosk_app.py --server.port 8502 --server.headless true"

echo Starting Voice Kiosk App (Port 8503) in background...
start /b "Voice Kiosk" cmd /c "streamlit run 03_voice_kiosk_app.py --server.port 8503 --server.headless true"

echo.
echo Starting Face Recognition App (Port 8501) in foreground...
echo Face Recognition: http://localhost:8501 (Main window - will open browser)
echo Normal Kiosk: http://localhost:8502 (Background - no browser)
echo Voice Kiosk: http://localhost:8503 (Background - no browser)
echo.
echo The system will automatically route to the appropriate kiosk based on age detection.
echo.
start "Face Recognition" cmd /k "streamlit run 01_face_recognition_app.py --server.port 8501"
