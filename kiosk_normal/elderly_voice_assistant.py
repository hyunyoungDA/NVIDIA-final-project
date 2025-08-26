import os
import time
import json
import tempfile
import wave
import pygame
import streamlit as st
import sounddevice as sd
import numpy as np
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from menu_data import menu_items, categories, allergen_map, diet_lists

# 환경변수 로드
load_dotenv()

class ElderlyVoiceAssistant:
    """어르신 모드용 음성 챗봇 - 메뉴 추천 및 장바구니 관리"""
    
    def __init__(self):
        # OpenAI 클라이언트 초기화 (GPT-5 nano)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        
        self.client = OpenAI(api_key=api_key)
        
        # 임시 디렉터리 설정
        self.tmp_dir = Path(tempfile.gettempdir()) / "elderly_voice_assistant"
        self.tmp_dir.mkdir(exist_ok=True)
        
        # pygame 초기화 (음성 재생용)
        if not pygame.get_init():
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
        
        # 대화 컨텍스트 초기화
        self.conversation_context = []
        self.current_filters = {
            "allergens": [],
            "diet": "일반",
            "category": "메인",
            "price_range": "보통",
            "spice_level": "보통"
        }
        
        print("[어르신 음성 어시스턴트] 초기화 완료")
    
    def text_to_speech(self, text: str) -> None:
        """OpenAI TTS API를 사용하여 텍스트를 음성으로 변환 및 재생"""
        try:
            print(f"[TTS] 텍스트: {text}")
            
            # 화면에 TTS 내용 표시
            st.markdown("### 🤖 AI 어시스턴트")
            st.info(text)
            
            # OpenAI TTS API 호출
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=text,
                response_format="mp3"
            )
            
            # MP3 데이터를 임시 파일로 저장
            temp_file = self.tmp_dir / f"tts_{int(time.time())}.mp3"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            # pygame으로 재생
            pygame.mixer.music.load(str(temp_file))
            pygame.mixer.music.play()
            
            # 재생 상태 표시
            with st.spinner("🔊 음성 재생 중..."):
                # 재생 완료까지 대기
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            
            # 임시 파일 삭제
            os.unlink(temp_file)
            print(f"[TTS] 재생 완료")
            
            # 재생 완료 후 잠시 대기
            time.sleep(1)
            
        except Exception as e:
            print(f"[TTS] 오류: {e}")
            st.error(f"음성 출력 오류: {e}")
    
    def speech_to_text(self, max_duration: float = 20.0) -> str:
        """마이크로 음성을 녹음하고 OpenAI STT API로 텍스트 변환"""
        try:
            print("[STT] 음성 녹음 시작...")
            
            # 녹음 상태 표시
            st.markdown("### 🎙️ 음성 녹음 중...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 음성 녹음 설정
            sample_rate = 16000
            channels = 1
            
            # 실시간 녹음을 위한 큐
            import queue
            audio_queue = queue.Queue()
            
            def audio_callback(indata, frames, time, status):
                audio_queue.put(indata.copy())
            
            # 녹음 시작 전 안내
            st.info("🎙️ 마이크 앞에서 편안하게 말씀해 주세요.")
            time.sleep(1)
            
            # 녹음 시작
            with sd.InputStream(samplerate=sample_rate, channels=channels, 
                              callback=audio_callback, dtype=np.int16):
                
                recorded_data = []
                start_time = time.time()
                last_speech_time = start_time
                speech_detected = False
                
                while True:
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    
                    # 최대 시간 초과
                    if elapsed_time >= max_duration:
                        break
                    
                    # 큐에서 오디오 데이터 가져오기
                    try:
                        data = audio_queue.get_nowait()
                        recorded_data.append(data)
                        
                        # 음성 활동 감지
                        rms = np.sqrt(np.mean(data.astype(np.float32)**2)) / 32768.0
                        if rms > 0.01:
                            last_speech_time = current_time
                            speech_detected = True
                        
                        # 음성 감지 후 5초 침묵 시 중단
                        if speech_detected and (current_time - last_speech_time) >= 5.0:
                            print(f"[STT] 5초 침묵 감지, 녹음 중단")
                            break
                            
                    except queue.Empty:
                        time.sleep(0.01)
                    
                    # UI 업데이트
                    progress = elapsed_time / max_duration
                    progress_bar.progress(progress)
                    
                    if speech_detected:
                        silence_time = current_time - last_speech_time
                        if silence_time < 5.0:
                            status_text.text(f"🎙️ 음성 인식 중... (침묵: {silence_time:.1f}초)")
                        else:
                            status_text.text("🎙️ 음성 입력 완료!")
                    else:
                        remaining_time = max_duration - elapsed_time
                        status_text.text(f"🎙️ 말씀해 주세요... (남은 시간: {remaining_time:.1f}초)")
            
            if not recorded_data:
                st.warning("음성이 녹음되지 않았습니다.")
                return ""
            
            # 녹음된 데이터 결합
            recording = np.concatenate(recorded_data, axis=0)
            
            # 음성 인식 처리 중 표시
            status_text.text("🔄 음성을 분석하고 있습니다...")
            
            # WAV 파일로 저장
            temp_wav = self.tmp_dir / f"recording_{int(time.time())}.wav"
            with wave.open(str(temp_wav), 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(recording.tobytes())
            
            # OpenAI STT API 호출
            with open(temp_wav, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ko"
                )
            
            # 임시 파일 삭제
            os.unlink(temp_wav)
            
            result = transcript.text.strip()
            print(f"[STT] 인식 결과: {result}")
            
            # 인식 결과 화면에 표시
            if result:
                st.markdown("### 💬 고객님이 말씀하신 내용")
                st.success(f'🎤 인식된 음성: "{result}"')
                st.info(f"📝 음성 인식 완료! 길이: {len(result)}자")
            else:
                st.warning("음성이 인식되지 않았습니다.")
            
            return result if result else ""
            
        except Exception as e:
            print(f"[STT] 오류: {e}")
            st.error(f"음성 인식 오류: {e}")
            return ""
    
    def get_menu_recommendations(self, user_request: str) -> list:
        """사용자 요청에 따른 메뉴 추천"""
        try:
            # GPT-5 nano를 사용하여 메뉴 추천
            system_prompt = f"""
            당신은 어르신을 위한 친절한 메뉴 추천 어시스턴트입니다.
            
            사용 가능한 메뉴 정보:
            {json.dumps(menu_items, ensure_ascii=False, indent=2)}
            
            알레르기 정보:
            {json.dumps(allergen_map, ensure_ascii=False, indent=2)}
            
            현재 설정된 필터:
            - 알레르기: {self.current_filters['allergens']}
            - 식단: {self.current_filters['diet']}
            - 카테고리: {self.current_filters['category']}
            - 가격대: {self.current_filters['price_range']}
            - 매운 정도: {self.current_filters['spice_level']}
            
            사용자의 요청에 따라 최적의 메뉴 3-5개를 추천해주세요.
            JSON 배열 형태로 메뉴 ID만 반환하세요.
            예시: [1, 5, 12]
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # GPT-5 nano 대신 사용 가능한 모델
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"사용자 요청: {user_request}"}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"[메뉴 추천] GPT 응답: {result_text}")
            
            # JSON 파싱
            try:
                recommended_ids = json.loads(result_text)
                if isinstance(recommended_ids, list):
                    # 추천된 메뉴 정보 가져오기
                    recommended_menus = []
                    for menu_id in recommended_ids:
                        menu_item = next((item for item in menu_items if item['id'] == menu_id), None)
                        if menu_item:
                            recommended_menus.append(menu_item)
                    
                    return recommended_menus
                else:
                    return []
            except json.JSONDecodeError:
                print(f"[메뉴 추천] JSON 파싱 실패: {result_text}")
                return []
            
        except Exception as e:
            print(f"[메뉴 추천] 오류: {e}")
            return []
    
    def add_to_cart(self, menu_name: str) -> bool:
        """장바구니에 메뉴 추가"""
        try:
            # 메뉴 이름으로 메뉴 찾기
            menu_item = next((item for item in menu_items if item['name'] == menu_name), None)
            
            if menu_item:
                # 세션 상태의 장바구니에 추가
                if 'cart' not in st.session_state:
                    st.session_state.cart = []
                
                # 이미 장바구니에 있는지 확인
                for cart_item in st.session_state.cart:
                    if cart_item['id'] == menu_item['id']:
                        cart_item['quantity'] += 1
                        return True
                
                # 새로 추가
                item_copy = menu_item.copy()
                item_copy['quantity'] = 1
                st.session_state.cart.append(item_copy)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[장바구니 추가] 오류: {e}")
            return False
    
    def process_user_request(self, user_input: str) -> str:
        """사용자 요청을 처리하고 적절한 응답 생성"""
        try:
            # 사용자 입력 분석
            user_input_lower = user_input.lower()
            
            # 메뉴 추천 요청 감지
            if any(keyword in user_input_lower for keyword in ["추천", "추천해", "뭐 먹을까", "맛있는", "인기"]):
                recommended_menus = self.get_menu_recommendations(user_input)
                if recommended_menus:
                    menu_names = [menu['name'] for menu in recommended_menus]
                    response = f"추천 메뉴는 {', '.join(menu_names)}입니다. 어떤 메뉴를 장바구니에 담을까요?"
                    
                    # 추천 메뉴를 화면에 표시
                    st.markdown("### 🌟 추천 메뉴")
                    for menu in recommended_menus:
                        st.info(f"🍽️ {menu['name']} - ₩{menu['price']:,} ({menu['cooking_time']}분)")
                    
                    return response
                else:
                    return "죄송합니다. 현재 조건에 맞는 추천 메뉴를 찾을 수 없습니다."
            
            # 장바구니 추가 요청 감지
            elif any(keyword in user_input_lower for keyword in ["담아", "추가", "장바구니", "담기"]):
                # 메뉴 이름 추출 시도
                for menu in menu_items:
                    if menu['name'] in user_input:
                        if self.add_to_cart(menu['name']):
                            return f"{menu['name']}을(를) 장바구니에 추가했습니다! 현재 장바구니에는 {len(st.session_state.cart)}개 메뉴가 있습니다."
                        else:
                            return f"죄송합니다. {menu['name']}을(를) 장바구니에 추가할 수 없습니다."
                
                return "어떤 메뉴를 장바구니에 담을까요? 메뉴 이름을 말씀해 주세요."
            
            # 도움 요청 감지
            elif any(keyword in user_input_lower for keyword in ["도움", "어떻게", "사용법", "기능"]):
                help_message = """제가 도와드릴 수 있는 기능은 다음과 같습니다:
                
                1. 🍽️ 메뉴 추천: "맛있는 메뉴 추천해줘", "인기 메뉴 알려줘"
                2. 🛒 장바구니 추가: "햄버거 담아줘", "치킨 추가해줘"
                3. 📋 메뉴 정보: "햄버거 가격이 얼마야?", "치킨 조리시간은?"
                4. 🚫 알레르기 확인: "이 메뉴에 달걀 들어있어?"
                
                 무엇을 도와드릴까요?"""
                return help_message
            
            # 일반적인 질문에 대한 GPT 응답
            else:
                system_prompt = f"""
                당신은 어르신을 위한 친절하고 도움이 되는 음식 주문 어시스턴트입니다.
                
                현재 설정된 필터:
                - 알레르기: {self.current_filters['allergens']}
                - 식단: {self.current_filters['diet']}
                - 카테고리: {self.current_filters['category']}
                
                사용자의 질문에 친근하고 이해하기 쉽게 한국어로 답변해주세요.
                음식과 관련된 질문이라면 더 자세히 설명해주세요.
                """
                
                # 대화 컨텍스트에 사용자 입력 추가
                self.conversation_context.append({"role": "user", "content": user_input})
                
                # GPT 응답 생성
                messages = [{"role": "system", "content": system_prompt}] + self.conversation_context[-6:]
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=300
                )
                
                ai_response = response.choices[0].message.content.strip()
                
                # 대화 컨텍스트에 AI 응답 추가
                self.conversation_context.append({"role": "assistant", "content": ai_response})
                
                return ai_response
            
        except Exception as e:
            print(f"[요청 처리] 오류: {e}")
            return "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다. 다시 시도해 주세요."
    
    def start_voice_assistant(self) -> None:
        """음성 어시스턴트 시작"""
        try:
            # 시작 메시지
            welcome_message = """안녕하세요! 저는 어르신을 위한 메뉴 추천 어시스턴트입니다. 
            음성으로 말씀해 주시면 맛있는 메뉴를 추천해드리고, 장바구니에 담아드릴 수 있습니다.
            무엇을 도와드릴까요?"""
            
            self.text_to_speech(welcome_message)
            
            # 대화 루프 (Streamlit 환경에 맞게 수정)
            conversation_ended = False
            max_conversations = 10  # 최대 대화 횟수 제한
            
            for i in range(max_conversations):
                if conversation_ended:
                    break
                
                # 사용자 음성 입력 받기
                user_input = self.speech_to_text(max_duration=15.0)
                
                if not user_input:
                    st.warning("음성이 인식되지 않았습니다. 다시 시도해 주세요.")
                    continue
                
                # 종료 조건 확인
                if any(keyword in user_input for keyword in ["종료", "끝", "그만", "나가기", "그만해"]):
                    goodbye_message = "음성 어시스턴트를 종료합니다. 즐거운 식사 되세요!"
                    self.text_to_speech(goodbye_message)
                    conversation_ended = True
                    break
                
                # 사용자 요청 처리
                ai_response = self.process_user_request(user_input)
                
                # AI 응답을 음성으로 출력
                self.text_to_speech(ai_response)
                
                # 잠시 대기
                time.sleep(1)
                
                # 대화 완료 확인
                if i < max_conversations - 1:
                    st.info(f"🎤 대화 {i+1}/{max_conversations} 완료. 계속하시겠습니까?")
                    time.sleep(2)
                
        except Exception as e:
            print(f"[음성 어시스턴트] 오류: {e}")
            st.error(f"음성 어시스턴트 오류: {e}")
    
    def start_single_conversation(self) -> str:
        """단일 대화 수행 (Streamlit 버튼용)"""
        try:
            # 사용자 음성 입력 받기
            user_input = self.speech_to_text(max_duration=15.0)
            
            if not user_input:
                return "음성이 인식되지 않았습니다. 다시 시도해 주세요."
            
            # 사용자 요청 처리
            ai_response = self.process_user_request(user_input)
            
            # AI 응답을 음성으로 출력
            self.text_to_speech(ai_response)
            
            return f"사용자: {user_input}\nAI: {ai_response}"
            
        except Exception as e:
            print(f"[단일 대화] 오류: {e}")
            return f"오류가 발생했습니다: {e}"

# 전역 인스턴스
elderly_assistant = None

def get_elderly_assistant_instance():
    """ElderlyVoiceAssistant 인스턴스 반환 (싱글톤 패턴)"""
    global elderly_assistant
    if elderly_assistant is None:
        try:
            elderly_assistant = ElderlyVoiceAssistant()
        except Exception as e:
            st.error(f"어르신 음성 어시스턴트 초기화 실패: {e}")
            return None
    return elderly_assistant

def start_elderly_voice_assistant():
    """어르신 음성 어시스턴트 시작"""
    assistant = get_elderly_assistant_instance()
    if assistant:
        return assistant.start_voice_assistant()
    else:
        st.error("음성 어시스턴트를 시작할 수 없습니다.")
