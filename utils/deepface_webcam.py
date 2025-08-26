import cv2
import requests
import base64
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def capture_frame(camera_index=0):
	"""
	Capture a single frame from the local webcam.
	"""
	cap = cv2.VideoCapture(camera_index)
	if not cap.isOpened():
		raise RuntimeError("웹캠을 열 수 없습니다.")
	
	# 카메라 워밍업을 위해 몇 프레임 건너뛰기
	for _ in range(5):
		ret, frame = cap.read()
		if not ret:
			break
	
	# 최종 프레임 캡처
	ret, frame = cap.read()
	cap.release()
	
	if not ret or frame is None:
		raise RuntimeError("웹캠 프레임을 캡처하지 못했습니다.")
	
	return frame


def detect_main_face_bgr(frame_bgr):
	"""
	Detect faces using Haar cascade and return the largest face ROI and bbox.
	"""
	try:
		gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
		face_cascade = cv2.CascadeClassifier(
			cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
		)
		
		# 다양한 파라미터로 얼굴 검출 시도
		faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
		print(f"First attempt found {len(faces)} faces")
		
		if len(faces) == 0:
			# 더 민감한 설정으로 재시도
			faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=2, minSize=(20, 20))
			print(f"Second attempt found {len(faces)} faces")
		
		if len(faces) == 0:
			# 매우 민감한 설정으로 마지막 시도
			faces = face_cascade.detectMultiScale(gray, scaleFactor=1.02, minNeighbors=1, minSize=(15, 15))
			print(f"Third attempt found {len(faces)} faces")
		
		if len(faces) == 0:
			return None
			
		# pick the largest face
		x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
		print(f"Selected face: x={x}, y={y}, w={w}, h={h}")
		return frame_bgr[y : y + h, x : x + w], (x, y, w, h)
		
	except Exception as e:
		print(f"Error in detect_main_face_bgr: {e}")
		return None


def analyze_face_with_facepp(face_bgr):
	"""
	Run Face++ age/gender analysis on a face ROI (BGR ndarray).
	"""
	try:
		# Face++ API 키 설정
		api_key = os.getenv('FACEPP_API_KEY')
		api_secret = os.getenv('FACEPP_API_SECRET')
		
		if not api_key or not api_secret:
			print("Face++ API 키가 설정되지 않았습니다. .env 파일에 FACEPP_API_KEY와 FACEPP_API_SECRET를 설정해주세요.")
			return None, None, None
		
		# 이미지를 base64로 인코딩
		_, buffer = cv2.imencode('.jpg', face_bgr)
		image_base64 = base64.b64encode(buffer).decode()
		
		# Face++ API 요청
		url = "https://api-us.faceplusplus.com/facepp/v3/detect"
		
		data = {
			'api_key': api_key,
			'api_secret': api_secret,
			'image_base64': image_base64,
			'return_attributes': 'age,gender'
		}
		
		response = requests.post(url, data=data, timeout=10)
		
		if response.status_code == 200:
			result = response.json()
			
			if 'faces' in result and len(result['faces']) > 0:
				face_data = result['faces'][0]
				attributes = face_data.get('attributes', {})
				
				age = attributes.get('age', {}).get('value')
				gender = attributes.get('gender', {}).get('value')
				
				print(f"Face++ API 결과 - 나이: {age}, 성별: {gender}")
				return age, gender, result
			else:
				print("Face++ API: 얼굴을 감지하지 못했습니다.")
				return None, None, None
		else:
			print(f"Face++ API 오류: {response.status_code} - {response.text}")
			return None, None, None
			
	except requests.exceptions.Timeout:
		print("Face++ API 요청 시간 초과")
		return None, None, None
	except Exception as e:
		print(f"Face++ API 오류: {e}")
		return None, None, None


def get_predicted_age(camera_index=0, output_face_path=None):
	"""
	Capture from local webcam and return only the predicted age using Face++ API.
	If output_face_path is provided, save detected face ROI.
	Returns age (int/float) or None if not found.
	"""
	try:
		frame = capture_frame(camera_index)
		print(f"Frame captured: {frame.shape}")
		
		# Face++ API는 전체 이미지를 받아서 처리하므로 얼굴 검출 단계를 생략하고 직접 API 호출
		# 하지만 더 나은 성능을 위해 로컬에서 먼저 얼굴 영역을 검출
		detection = detect_main_face_bgr(frame)
		
		if detection is not None:
			face_roi, bbox = detection
			print(f"Face detected at: {bbox}, face_roi shape: {face_roi.shape}")
			
			if output_face_path:
				cv2.imwrite(output_face_path, face_roi)
			
			# Face++ API로 나이 분석
			age, _gender, _allres = analyze_face_with_facepp(face_roi)
			print(f"Face++ analyzed age: {age}")
			
			if age is not None:
				return age
		
		# 로컬 얼굴 검출이 실패했을 경우 전체 프레임으로 Face++ API 시도
		print("Local face detection failed, trying Face++ API with full frame")
		age, _gender, _allres = analyze_face_with_facepp(frame)
		print(f"Face++ full frame analyzed age: {age}")
		return age
		
	except Exception as e:
		print(f"Error in get_predicted_age: {e}")
		return None


def main(camera_index=0):
	"""
	Entry point that returns only the predicted age (prints nothing else).
	"""
	return get_predicted_age(camera_index=camera_index, output_face_path=None)


if __name__ == "__main__":
	try:
		age = main()
		print(f"예측된 나이: {age}")
	except Exception as e:
		print(f"오류: {e}")
		print("Face++ API 키가 .env 파일에 설정되어 있는지 확인해주세요:")
		print("FACEPP_API_KEY=your_api_key")
		print("FACEPP_API_SECRET=your_api_secret")


