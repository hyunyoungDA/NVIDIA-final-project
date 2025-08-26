from utils.deepface_webcam import get_predicted_age


def get_age_from_webcam(camera_index: int = 0):
    """
    로컬 웹캠에서 얼굴을 캡처하고 예측된 나이만 반환합니다.
    얼굴이 감지되지 않거나 분석 실패 시 None 반환.
    """
    return get_predicted_age(camera_index=camera_index)


def classify_age_from_webcam(camera_index: int = 0):
    """
    60세 이상/미만 분류 문자열을 반환합니다. (None 가능)
    """
    age = get_age_from_webcam(camera_index=camera_index)
    if age is None:
        return None
    return "60세 이상" if age >= 60 else "60세 미만"


def main():
    """메인 함수 - 나이 감지 기능"""
    print("=== DeepFace 나이 감지 시스템 ===")
    print("웹캠을 통해 얼굴을 감지하고 나이를 예측합니다.")
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 40)
    
    try:
        while True:
            print("\n나이 감지를 시작합니다...")
            age = get_age_from_webcam()
            
            if age is not None:
                print(f"감지된 나이: {age}세")
                category = "60세 이상" if age >= 60 else "60세 미만"
                print(f"분류: {category}")
            else:
                print("얼굴을 감지할 수 없습니다. 다시 시도해주세요.")
            
            # 사용자에게 계속할지 묻기
            try:
                choice = input("\n다시 시도하시겠습니까? (y/n): ").strip().lower()
                if choice not in ['y', 'yes', '예']:
                    print("프로그램을 종료합니다.")
                    break
            except KeyboardInterrupt:
                print("\n프로그램을 종료합니다.")
                break
                
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")


if __name__ == "__main__":
    main()