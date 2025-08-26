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

# 환경변수 로드
load_dotenv()

class VoiceOrdering:
    """60세 이상 어르신을 위한 OpenAI 음성 주문 시스템"""
    
    def __init__(self):
        # OpenAI 클라이언트 초기화
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        
        self.client = OpenAI(api_key=api_key)
        
        # 임시 디렉터리 설정
        self.tmp_dir = Path(tempfile.gettempdir()) / "voice_ordering"
        self.tmp_dir.mkdir(exist_ok=True)
        
        # pygame 초기화 (음성 재생용)
        if not pygame.get_init():
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
        
        print("[음성 주문] 초기화 완료")
    
    def text_to_speech(self, text: str) -> None:
        """OpenAI TTS API를 사용하여 텍스트를 음성으로 변환 및 재생"""
        try:
            print(f"[TTS] 텍스트: {text}")
            
            # 화면에 TTS 내용 표시
            st.markdown("### 🔊 AI 안내")
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
            
            # 재생 완료 후 잠시 대기 (사용자가 음성을 듣고 이해할 시간)
            time.sleep(1)
            
        except Exception as e:
            print(f"[TTS] 오류: {e}")
            st.error(f"음성 출력 오류: {e}")
    
    def detect_silence(self, audio_data, sample_rate, threshold=0.01, min_silence_duration=4.0):
        """음성 데이터에서 침묵 구간 감지"""
        # 오디오 데이터 정규화
        audio_data = audio_data.astype(np.float32) / 32768.0
        
        # RMS 에너지 계산 (0.1초 단위)
        frame_size = int(sample_rate * 0.1)
        energy_levels = []
        
        for i in range(0, len(audio_data), frame_size):
            frame = audio_data[i:i+frame_size]
            if len(frame) > 0:
                rms = np.sqrt(np.mean(frame**2))
                energy_levels.append(rms)
        
        # 침묵 구간 찾기
        silence_frames = 0
        speech_detected = False
        
        for energy in energy_levels:
            if energy > threshold:
                silence_frames = 0
                speech_detected = True
            else:
                if speech_detected:  # 음성이 감지된 후에만 침묵 카운트
                    silence_frames += 1
                    # 4초 이상 침묵이면 중단
                    if silence_frames * 0.1 >= min_silence_duration:
                        end_frame = len(energy_levels) - silence_frames
                        return int(end_frame * frame_size)
        
        return len(audio_data)

    def speech_to_text(self, max_duration: float = 20.0, silence_threshold: float = 4.0) -> str:
        """마이크로 음성을 녹음하고 OpenAI STT API로 텍스트 변환 (VAD 적용)"""
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
            
            # 녹음 시작 전 사용자에게 준비 시간 제공
            st.info("🎙️ 마이크 앞에서 편안하게 앉아주세요. 준비가 되시면 말씀해 주세요.")
            time.sleep(1)  # 1초 대기
            
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
                        if rms > 0.01:  # 임계값보다 큰 경우 음성으로 간주
                            last_speech_time = current_time
                            speech_detected = True
                        
                        # 음성 감지 후 5초 침묵 시 중단 (4초에서 5초로 연장)
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
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(recording.tobytes())
            
            # OpenAI STT API 호출
            with open(temp_wav, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ko"  # 한국어 명시
                )
            
            # 임시 파일 삭제
            os.unlink(temp_wav)
            
            result = transcript.text.strip()
            print(f"[STT] 인식 결과: {result}")
            
            # 인식 결과 화면에 표시
            if result:
                st.markdown("### 💬 고객님이 말씀하신 내용")
                st.success(f'🎤 인식된 음성: "{result}"')
                
                # 디버깅 정보 추가
                st.info(f"📝 음성 인식 완료! 길이: {len(result)}자")
                
                # 자동 스크롤을 위한 JavaScript 실행
                st.markdown("""
                <script>
                setTimeout(function() {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 100);
                </script>
                """, unsafe_allow_html=True)
            else:
                st.warning("음성이 인식되지 않았습니다.")
            
            return result if result else ""
            
        except Exception as e:
            print(f"[STT] 오류: {e}")
            st.error(f"음성 인식 오류: {e}")
            return ""
    
    def extract_allergens_from_voice(self, user_voice_text: str) -> list:
        """사용자 음성에서 알레르기 재료 추출하여 JSON 형식으로 반환"""
        try:
            # 사용 가능한 알레르기 재료 목록
            available_allergens = ["달걀", "토마토", "새우", "조개류", "닭고기", "땅콩", "쇠고기", "돼지고기", "호두"]
            
            # OpenAI GPT API를 사용하여 알레르기 재료 추출
            system_prompt = f"""
            사용자의 음성에서 알레르기가 있는 음식 재료를 추출해주세요.
            
            사용 가능한 알레르기 재료 목록:
            {', '.join(available_allergens)}
            
            규칙:
            1. 사용자가 언급한 재료 중 위 목록에 있는 것만 추출
            2. "없음", "없어요", "안 있어요" 등이 포함되면 빈 배열 반환
            3. JSON 배열 형식으로만 반환 (예: ["달걀", "토마토"])
            4. 목록에 없는 재료는 무시
            5. 굴, 가리비는 "조개류"로 통합
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"사용자 음성 내용: {user_voice_text}"}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            # JSON 응답 파싱
            result_text = response.choices[0].message.content.strip()
            print(f"[알레르기 추출] GPT 응답: {result_text}")
            
            # JSON 파싱
            try:
                allergens = json.loads(result_text)
                if isinstance(allergens, list):
                    # 유효한 알레르기 재료만 필터링
                    valid_allergens = [item for item in allergens if item in available_allergens]
                    print(f"[알레르기 추출] 추출된 알레르기: {valid_allergens}")
                    return valid_allergens
                else:
                    print(f"[알레르기 추출] 잘못된 응답 형식: {allergens}")
                    return []
            except json.JSONDecodeError:
                print(f"[알레르기 추출] JSON 파싱 실패: {result_text}")
                return []
            
        except Exception as e:
            print(f"[알레르기 추출] 오류: {e}")
            st.error(f"알레르기 추출 오류: {e}")
            return []
    
    def extract_diet_from_voice(self, user_voice_text: str) -> str:
        """사용자 음성에서 식단 유형 추출"""
        try:
            # OpenAI GPT API를 사용하여 식단 유형 추출
            system_prompt = """
            사용자의 음성에서 식단 유형을 추출해주세요.
            
            가능한 식단 유형:
            - "비건" (완전 채식주의자)
            - "채식" 또는 "베지테리언" (채식주의자)
            - "일반" (특별한 식단 없음)
            
            규칙:
            1. 사용자가 "비건", "비건식", "완전채식" 등을 언급하면 "비건" 반환
            2. 사용자가 "채식", "베지테리언", "채식주의" 등을 언급하면 "채식" 반환
            3. 위에 해당하지 않거나 "아니다", "일반", "없다" 등이면 "일반" 반환
            4. 반드시 "비건", "채식", "일반" 중 하나만 반환
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"사용자 음성 내용: {user_voice_text}"}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            print(f"[식단 추출] GPT 응답: {result}")
            
            # 결과 검증
            if "비건" in result:
                return "비건"
            elif "채식" in result:
                return "채식"
            else:
                return "일반"
            
        except Exception as e:
            print(f"[식단 추출] 오류: {e}")
            return "일반"

    def extract_category_from_voice(self, user_voice_text: str) -> str:
        """사용자 음성에서 메뉴 카테고리 추출"""
        try:
            system_prompt = """
            사용자의 음성에서 원하는 메뉴 카테고리를 추출해주세요.
            
            가능한 카테고리:
            - "메인" (배고프다, 든든하게, 식사, 햄버거, 치킨, 밥 등)
            - "사이드" (간식, 가볍게, 사이드메뉴, 감자튀김, 치킨너겟 등)
            - "음료" (갈증, 목마르다, 음료수, 콜라, 주스, 커피 등)
            - "디저트" (달다, 달콤하다, 디저트, 아이스크림, 케이크 등)
            
            규칙:
            1. 배고픔이나 든든한 식사를 원하면 "메인"
            2. 가벼운 간식이나 사이드를 원하면 "사이드"  
            3. 갈증이나 음료를 원하면 "음료"
            4. 달콤한 것이나 디저트를 원하면 "디저트"
            5. 명확하지 않으면 "메인" 반환
            6. 반드시 "메인", "사이드", "음료", "디저트" 중 하나만 반환
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"사용자 음성 내용: {user_voice_text}"}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            print(f"[카테고리 추출] GPT 응답: {result}")
            
            # 결과 검증
            valid_categories = ["메인", "사이드", "음료", "디저트"]
            for category in valid_categories:
                if category in result:
                    return category
            
            return "메인"  # 기본값
            
        except Exception as e:
            print(f"[카테고리 추출] 오류: {e}")
            return "메인"

    def start_complete_voice_ordering(self) -> dict:
        """음성 주문 시작 - 알레르기, 식단, 카테고리 확인"""
        try:
            # 1단계: 알레르기 확인
            allergy_question = """안녕하세요! 주문을 받겠습니다. 
            달걀, 토마토, 새우, 조개류 (굴, 가리비), 닭고기, 땅콩, 쇠고기, 돼지고기, 호두 중 알레르기 있는 재료가 있으신가요?
            알레르기가 없으시면 '없음'이라고 말씀해 주세요."""
            
            # 음성 안내 시작
            st.info("🔊 음성 안내를 시작합니다. 잠시만 기다려주세요...")
            time.sleep(1)
            
            self.text_to_speech(allergy_question)
            
            # 사용자가 응답할 준비를 할 수 있도록 잠시 대기
            st.info("🎙️ 이제 말씀해 주세요. 충분히 생각하신 후 답변해 주시면 됩니다.")
            st.info("🎯 예시: '달걀 알레르기 있어요' 또는 '없음'")
            time.sleep(3)  # 3초 대기
            
            # 알레르기 응답 받기
            user_allergy_response = self.speech_to_text(duration=15.0)  # 15초로 연장
            if not user_allergy_response:
                st.warning("음성이 인식되지 않았습니다. 다시 시도해 주세요.")
                return {"allergens": [], "diet": "일반", "category": "메인"}
            
            # 알레르기 재료 추출
            allergens = self.extract_allergens_from_voice(user_allergy_response)
            
            # 알레르기 확인 메시지
            if allergens:
                allergy_confirmation = f"네, {', '.join(allergens)} 알레르기를 확인했습니다."
            else:
                allergy_confirmation = "네, 알레르기가 없으시군요."
            
            st.markdown("---")
            self.text_to_speech(allergy_confirmation)
            
            # 2단계: 식단 확인
            diet_question = """이제 식단에 대해 여쭤보겠습니다.
            비건 (완전 채식주의)이시거나 베지테리언 (채식주의)이신가요?
            해당되시면 말씀해 주시고, 아니시면 '아니다' 또는 '일반'이라고 말씀해 주세요."""
            
            st.markdown("---")
            self.text_to_speech(diet_question)
            
            # 사용자가 응답할 준비를 할 수 있도록 잠시 대기
            st.info("🎙️ 이제 말씀해 주세요. 충분히 생각하신 후 답변해 주시면 됩니다.")
            st.info("🎯 예시: '비건이에요' 또는 '채식' 또는 '일반'")
            time.sleep(3)  # 3초 대기
            
            # 식단 응답 받기
            user_diet_response = self.speech_to_text(duration=15.0)  # 15초로 연장
            if not user_diet_response:
                st.warning("음성이 인식되지 않아 일반 식단으로 설정합니다.")
                diet_type = "일반"
            else:
                diet_type = self.extract_diet_from_voice(user_diet_response)
            
            # 식단 확인 메시지
            if diet_type == "비건":
                diet_confirmation = "네, 비건 식단으로 설정하겠습니다. 동물성 재료가 포함된 메뉴는 제외하겠습니다."
            elif diet_type == "채식":
                diet_confirmation = "네, 채식 식단으로 설정하겠습니다. 고기류가 포함된 메뉴는 제외하겠습니다."
            else:
                diet_confirmation = "네, 일반 식단으로 설정하겠습니다."
            
            st.markdown("---")
            self.text_to_speech(diet_confirmation)
            
            # 3단계: 카테고리 확인
            category_question = """마지막으로 어떤 종류의 음식을 원하시는지 여쭤보겠습니다.
            많이 배고프시다면 든든한 메인 요리, 가볍게 드시고 싶다면 사이드 메뉴, 
            갈증이 나신다면 음료, 달콤한 것이 드시고 싶다면 디저트 중에서 말씀해 주세요.
            또는 '배고프다', '갈증난다', '달달한게 먹고싶다' 등으로 말씀해 주셔도 됩니다."""
            
            st.markdown("---")
            self.text_to_speech(category_question)
            
            # 사용자가 응답할 준비를 할 수 있도록 잠시 대기
            st.info("🎙️ 이제 말씀해 주세요. 충분히 생각하신 후 답변해 주시면 됩니다.")
            st.info("🎯 예시: '배고파요' 또는 '갈증나요' 또는 '달달한게 좋아요'")
            time.sleep(3)  # 3초 대기
            
            # 카테고리 응답 받기
            user_category_response = self.speech_to_text(duration=15.0)  # 15초로 연장
            if not user_category_response:
                st.warning("음성이 인식되지 않아 메인 메뉴로 설정합니다.")
                category_type = "메인"
            else:
                category_type = self.extract_category_from_voice(user_category_response)
            
            # 카테고리 확인 메시지
            category_messages = {
                "메인": "네, 든든한 메인 요리로 준비하겠습니다.",
                "사이드": "네, 가벼운 사이드 메뉴로 준비하겠습니다.",
                "음료": "네, 시원한 음료로 준비하겠습니다.",
                "디저트": "네, 달콤한 디저트로 준비하겠습니다."
            }
            
            category_confirmation = category_messages.get(category_type, "네, 메인 요리로 준비하겠습니다.")
            
            st.markdown("---")
            self.text_to_speech(category_confirmation)
            
            # 최종 완료 메시지
            final_message = "모든 설정이 완료되었습니다. 조건에 맞는 메뉴를 자동으로 선택해서 보여드리겠습니다."
            st.markdown("---")
            self.text_to_speech(final_message)
            
            return {"allergens": allergens, "diet": diet_type, "category": category_type}
            
        except Exception as e:
            print(f"[음성 주문] 오류: {e}")
            st.error(f"음성 주문 중 오류가 발생했습니다: {e}")
            return {"allergens": [], "diet": "일반", "category": "메인"}
    
    def start_allergy_voice_ordering(self) -> list:
        """기존 호환성을 위한 함수 (deprecated)"""
        result = self.start_complete_voice_ordering()
        return result["allergens"]

# 전역 인스턴스
voice_ordering = None

def get_voice_ordering_instance():
    """VoiceOrdering 인스턴스 반환 (싱글톤 패턴)"""
    global voice_ordering
    if voice_ordering is None:
        try:
            voice_ordering = VoiceOrdering()
        except Exception as e:
            st.error(f"음성 주문 시스템 초기화 실패: {e}")
            return None
    return voice_ordering

def start_voice_allergy_check():
    """음성 알레르기 확인 시작 (호환성용 - deprecated)"""
    voice_system = get_voice_ordering_instance()
    if voice_system:
        return voice_system.start_allergy_voice_ordering()
    return []

def start_complete_voice_ordering():
    """완전한 음성 주문 시작 - 알레르기 및 식단 확인"""
    voice_system = get_voice_ordering_instance()
    if voice_system:
        return voice_system.start_complete_voice_ordering()
    return {"allergens": [], "diet": "일반"}