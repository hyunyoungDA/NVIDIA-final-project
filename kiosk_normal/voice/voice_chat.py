from __future__ import annotations

import os
import sys
import time
import threading
import queue
import json
# import io
import wave
# import asyncio
import select
from typing import Optional, Generator, AsyncGenerator
from collections import deque

from dotenv import load_dotenv
from pathlib import Path

load_dotenv("../.env")

# openai 설치 확인 
def _has_openai() -> bool:
    try:
        from openai import OpenAI  # noqa: F401
        return True
    except Exception:
        return False

class VoiceChat:
    def __init__(self):
        self.base = Path(__file__).resolve().parent.parent # faceapi 디렉터리
        # 시스템 임시 디렉터리 사용
        import tempfile
        self.tmp_dir = Path(tempfile.gettempdir()) / "streamlit_kiosk_tmp"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # 메뉴 데이터 로드
        self.menu_data = self._load_menu_data()
        
        # 실시간 오디오 스트림 관련
        self.audio_queue = queue.Queue() # thread -> STT
        self.tts_queue = queue.Queue() # llm response -> tts -> playing
        self.is_recording = False
        self.is_playing = False
        self.is_processing = False
        
        # 버퍼링을 위한 큐 -> 최신 n개의 데이터 유지해서 맥락 구성에 활용 
        self.text_buffer = deque(maxlen=10)
        self.audio_buffer = deque(maxlen=5)
        
        # 오디오 시스템 초기화
        self._init_audio_system()
        
        # OpenAI 클라이언트
        if _has_openai() and os.getenv("OPENAI_API_KEY"):
            from openai import OpenAI
            self.client = OpenAI()
        else:
            self.client = None
            print("OpenAI API 키가 설정되지 않았습니다.")
    
    def _load_menu_data(self) -> dict:
        """메뉴 데이터 로드"""
        try:
            menu_path = self.base / "menu.json"
            if menu_path.exists():
                with open(menu_path, 'r', encoding='utf-8') as f:
                    menu_data = json.load(f)
                print(f"[메뉴 데이터] {len(menu_data.get('items', []))}개 메뉴 항목 로드 완료")
                return menu_data
            else:
                print(f"[메뉴 데이터] menu.json 파일을 찾을 수 없습니다: {menu_path}")
                return {}
        except Exception as e:
            print(f"[메뉴 데이터 로드 실패] {e}")
            return {}
    
    def _get_menu_context(self) -> str:
        """메뉴 데이터를 LLM 컨텍스트로 변환"""
        if not self.menu_data:
            return ""
        
        try:
            context_parts = []
            
            # 매장 정보
            store_name = self.menu_data.get('store', '키오스크')
            context_parts.append(f"매장명: {store_name}")
            
            # 메뉴 카테고리별 정리
            items = self.menu_data.get('items', [])
            categories = {}
            
            for item in items:
                category = item.get('category', '기타')
                if category not in categories:
                    categories[category] = []
                
                # 메뉴 정보 요약
                menu_info = f"- {item.get('name', '')} ({item.get('price', 0):,}원)"
                
                # 알레르기 정보 추가
                allergens = item.get('allergens', [])
                if allergens:
                    menu_info += f" [알레르기: {', '.join(allergens)}]"
                
                # 영양 정보 추가
                nutrition = item.get('nutrition', {})
                if nutrition.get('calorie_kcal'):
                    menu_info += f" [칼로리: {nutrition['calorie_kcal']}kcal]"
                
                categories[category].append(menu_info)
            
            # 카테고리별 메뉴 정보 추가
            for category, menu_list in categories.items():
                context_parts.append(f"\n{category}:")
                context_parts.extend(menu_list)
            
            # 알레르기 정보
            allergen_vocab = self.menu_data.get('allergen_vocab', [])
            if allergen_vocab:
                context_parts.append(f"\n알레르기 정보: {', '.join(allergen_vocab)}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"[메뉴 컨텍스트 생성 실패] {e}")
            return ""
    
    def _search_menu_items(self, query: str) -> list:
        """메뉴 검색 기능"""
        if not self.menu_data:
            return []
        
        try:
            items = self.menu_data.get('items', [])
            results = []
            query_lower = query.lower()
            
            for item in items:
                name = item.get('name', '').lower()
                category = item.get('category', '').lower()
                notes = item.get('notes', '').lower()
                
                # 이름, 카테고리, 메모에서 검색
                if (query_lower in name or 
                    query_lower in category or 
                    query_lower in notes):
                    results.append(item)
            
            return results
            
        except Exception as e:
            print(f"[메뉴 검색 실패] {e}")
            return []
    
    def _init_audio_system(self):
        """오디오 시스템 초기화"""
        try:
            import sounddevice as sd # PortAudio 기반 
            import numpy as np
            
            # 현재 PC에서의 모든 오디오 장치 정보 확인
            devices = sd.query_devices()
            print(f"[오디오 시스템] 사용 가능한 장치: {len(devices)}개")
            
            # 기본 출력/재생 장치 설정
            default_output = sd.query_devices(kind='output')
            print(f"[오디오 시스템] 기본 출력: {default_output['name']}")
            
            # 오디오 시스템 테스트 (무음 재생)
            # test_audio = np.zeros(1000, dtype=np.int16)
            # sd.play(test_audio, samplerate=24000)
            # sd.wait()
            
            print("[오디오 시스템] 초기화 완료")
            
        except Exception as e:
            print(f"[오디오 시스템 초기화 실패] {e}")
    
    def _create_tts_stream(self, text: str) -> bytes:
        """
        TTS 스트림 생성 (PCM 형식)
        PCM(Pulse-code Modulation): 디지털 오디오 데이터 형식 
        """
        if not self.client:
            return b""
            
        try:
            print(f"[TTS 요청] 텍스트: {text}")
            
            response = self.client.audio.speech.create(
                model="tts-1", # 올바른 TTS 모델명 
                voice="nova", # 음성 -> 나긋하고 친절한 목소리 
                input=text,
                response_format="mp3",  # MP3 형식으로 변경 (더 안정적)
                speed=1.0
            )
            
            # 응답 데이터 검증
            if response.content and len(response.content) > 0:
                print(f"[TTS 응답] 데이터 크기: {len(response.content)} bytes")
                return response.content
            else:
                print(f"[TTS 스트림 생성 실패] 빈 응답")
                return b""
                
        except Exception as e:
            print(f"[TTS 스트림 생성 실패] {e}")
            return b""
    
    def _play_audio_stream(self, audio_data: bytes, sample_rate: int = 22050) -> None:
        """MP3 오디오 스트림 재생"""
        try:
            import tempfile
            import pygame
            import io
            
            # pygame 오디오 시스템 초기화
            if not pygame.get_init():
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
            
            # MP3 데이터를 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # MP3 파일 재생
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # 재생 완료까지 대기
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # 임시 파일 삭제
            os.unlink(temp_file_path)
            
            print("[오디오 재생 완료]")
            
        except ImportError:
            print("[오디오 재생 실패] pygame이 설치되지 않았습니다.")
            print("다음 명령으로 설치하세요: pip install pygame")
        except Exception as e:
            print(f"[오디오 스트림 재생 실패] {e}")
    
    def _play_beep(self, frequency: int = 800, duration: float = 0.3) -> None:
        """비프음 재생 (녹음 시작 알림)"""
        try:
            import sounddevice as sd
            import numpy as np
            
            # 비프음 생성
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            beep = np.sin(2 * np.pi * frequency * t) * 0.3  # 볼륨 조절
            
            # 16-bit 정수로 변환
            beep_int16 = (beep * 32767).astype(np.int16)
            
            # 재생
            sd.play(beep_int16, sample_rate)
            sd.wait()
            
        except Exception as e:
            print(f"[비프음 재생 실패] {e}")
    
    def _stream_tts_realtime(self, text: str) -> None:
        """실시간 TTS 스트리밍"""
        if not self.client:
            print(f"[TTS 대체] {text}")
            return
            
        try:
            print(f"[TTS 스트리밍 시작] {text}")
            self.is_playing = True # 재생 중 표시 
            
            # TTS 재생 전 안정화를 위한 지연 (0.4초)
            time.sleep(0.4)
            
            # TTS 스트림 생성 및 재생
            audio_data = self._create_tts_stream(text)
            if audio_data:
                self._play_audio_stream(audio_data)
                print(f"[TTS 스트리밍 완료] {text}")
            else:
                print(f"[TTS 스트림 생성 실패] {text}")
            
        except Exception as e:
            print(f"[TTS 스트리밍 실패] {e}")
        finally:
            self.is_playing = False
    
    def _record_audio_stream(self, duration: float = 5.0) -> Optional[bytes]:
        """실시간 오디오 녹음 스트림"""
        try:
            import sounddevice as sd
            import numpy as np
            
            print("말씀해주세요 (비프음 후 녹음 시작)...")
            
            sample_rate = 16000
            
            # 1. 먼저 비프음 재생 (녹음 시작 전)
            self._play_beep()
            
            # 2. 비프음 완료 후 짧은 지연
            time.sleep(0.2)
            
            # 3. 녹음 시작
            recording = sd.rec(int(duration * sample_rate), 
                             samplerate=sample_rate, 
                             channels=1, 
                             dtype=np.int16)
            
            # 4. 녹음 완료 대기
            sd.wait()
            
            return recording.tobytes()
            
        except Exception as e:
            print(f"[오디오 녹음 실패] {e}")
            return None
    
    # speach-to-text
    def _transcribe_audio_stream(self, audio_data: bytes) -> Optional[str]:
        """오디오 스트림을 텍스트로 변환"""
        if not self.client:
            return input("사용자 입력 > ").strip()
            
        try:
            # 임시 WAV 파일 생성
            wav_path = self.tmp_dir / "temp_stream.wav"
            
            # OpenAI 모델은 wav,mp3 파일을 지원하므로 pcm을 wave 라이브러리로 래핑 
            with wave.open(str(wav_path), 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
            
            # STT 처리
            with open(wav_path, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", # 올바른 STT 모델명 
                    file=f,
                )
            
            # 임시 파일 삭제
            wav_path.unlink(missing_ok=True)
            
            return transcript.text.strip() if hasattr(transcript, 'text') else None
            
        except Exception as e:
            print(f"[STT 스트림 처리 실패] {e}")
            return None
    
    def _stream_llm_response(self, user_text: str) -> Generator[str, None, None]:
        """실시간 LLM 응답 스트리밍"""
        if not self.client:
            yield f"요청하신 내용에 대한 안내입니다: {user_text}"
            return
            
        try:
            # 메뉴 컨텍스트 가져오기
            menu_context = self._get_menu_context()
            
            # 시스템 프롬프트 구성
            system_prompt = """당신은 친절하고 자연스러운 AI 키오스크입니다. 자연스럽고 명확하고 이해하기 쉽게 답변하세요. 
너무 형식적이지 말고 친근한 톤으로 대화하세요. 
주문을 도와주거나 메뉴를 추천해주세요.

다음은 현재 매장의 메뉴 정보입니다. 이 정보를 바탕으로 정확한 메뉴 추천, 가격 안내, 알레르기 정보 등을 제공해주세요:

{menu_context}

메뉴 관련 질문에 답할 때는 위의 메뉴 정보를 정확히 참고하여 답변해주세요. 
- 가격, 알레르기 정보, 영양 정보 등을 포함하여 친절하게 안내해주세요
- 특정 메뉴에 대해 질문받으면 해당 메뉴의 상세 정보를 제공해주세요
- 메뉴 추천 요청 시 사용자의 선호도나 제약사항(알레르기, 식단 등)을 고려해주세요
- 비건, 채식주의자, 돼지고기 금기 등의 식단 제약사항이 있으면 해당 조건에 맞는 메뉴를 추천해주세요
- 칼로리나 영양 정보에 대한 질문에도 정확히 답변해주세요""".format(menu_context=menu_context)
            
            # 스트리밍 응답 생성
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                temperature=0,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
            
        except Exception as e:
            print(f"[LLM 스트리밍 실패] {e}")
            yield f"요청하신 내용에 대한 안내입니다: {user_text}"
    
    def _process_streaming_response(self, response_stream: Generator[str, None, None]) -> None:
        """스트리밍 응답을 실시간으로 처리하고 TTS로 변환"""
        if not self.client:
            return
            
        try:
            buffer = ""
            sentence_end_chars = ['.', '!', '?', '\n'] # 문장 끝 기준 
            current_tts_thread = None  # 현재 TTS 스레드만 추적
            
            for chunk in response_stream:
                buffer += chunk
                print(chunk, end="", flush=True)
                
                # 문장이 완성되면 즉시 TTS 재생
                if any(char in buffer for char in sentence_end_chars):
                    if buffer.strip():
                        # 이전 TTS가 완료될 때까지 대기
                        if current_tts_thread and current_tts_thread.is_alive():
                            current_tts_thread.join()
                        
                        # 문장 간 자연스러운 지연 추가 (0.8초)
                        time.sleep(0.8)
                        
                        # 별도 스레드에서 TTS 재생 (비동기)
                        current_tts_thread = threading.Thread(
                            target=self._stream_tts_realtime,
                            args=(buffer.strip(),),
                            daemon=True
                        )
                        current_tts_thread.start()
                    buffer = ""
            
            # 남은 텍스트 처리
            if buffer.strip():
                # 이전 TTS가 완료될 때까지 대기
                if current_tts_thread and current_tts_thread.is_alive():
                    current_tts_thread.join()
                
                # 마지막 문장도 지연 추가
                time.sleep(0.8)
                
                current_tts_thread = threading.Thread(
                    target=self._stream_tts_realtime,
                    args=(buffer.strip(),),
                    daemon=True
                )
                current_tts_thread.start()
            
            # 마지막 TTS 스레드가 완료될 때까지 대기
            if current_tts_thread and current_tts_thread.is_alive():
                current_tts_thread.join()
                
        except Exception as e:
            print(f"[스트리밍 응답 처리 실패] {e}")
    
    def _continuous_listening(self) -> Optional[str]:
        """연속 음성 인식 (더 자연스러운 대화)"""
        try:
            import sounddevice as sd
            import numpy as np
            
            # WebRTC VAD는 선택사항
            try:
                import webrtcvad
                vad = webrtcvad.Vad(2)  # 적당한 민감도
                use_vad = True
            except ImportError:
                print("webrtcvad가 설치되지 않아 기본 음성 인식 모드를 사용합니다.")
                use_vad = False
            
            print("연속 음성 인식 모드 (종료하려면 '그만'이라고 말씀하세요)...")
            sample_rate = 16000
            frame_duration = 30  # ms
            
            # 실시간 오디오 스트림
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"오디오 스트림 상태: {status}")
                
                # VAD로 음성 감지 (선택사항)
                audio_data = indata.tobytes()
                if use_vad:
                    is_speech = vad.is_speech(audio_data, sample_rate)
                else:
                    # 기본적으로 모든 오디오를 음성으로 간주
                    is_speech = True
                
                if is_speech:
                    # 음성 데이터 수집
                    self.audio_buffer.append(audio_data)
            
            # 오디오 스트림 시작
            with sd.InputStream(callback=audio_callback,
                              channels=1,
                              samplerate=sample_rate,
                              dtype=np.int16,
                              blocksize=int(sample_rate * frame_duration / 1000)):
                
                while True:
                    time.sleep(0.1)
                    
                    # 충분한 음성 데이터가 수집되면 STT 처리
                    if len(self.audio_buffer) >= 10:  # 약 3초
                        audio_data = b''.join(self.audio_buffer)
                        self.audio_buffer.clear()
                        
                        text = self._transcribe_audio_stream(audio_data)
                        if text:
                            return text
                    
                    # 종료 조건 확인 (키보드 입력)
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        return input().strip()
                        
        except Exception as e:
            print(f"[연속 음성 인식 실패] {e}")
            return None
    
    def run(self) -> None:
        """메인 실행 루프"""
        # 초기 프롬프트 (한 번만 재생)
        menu_count = len(self.menu_data.get('items', [])) if self.menu_data else 0
        initial_prompt = f"안녕하세요! 저는 {self.menu_data.get('store', '키오스크')}의 AI 어시스턴트입니다. {menu_count}개의 메뉴를 준비했어요. 메뉴 추천이나 주문을 도와드릴까요?"
        print(f"[초기 프롬프트] {initial_prompt}")
        
        # 초기 프롬프트 재생 전 시스템 안정화를 위한 지연
        print("[시스템] 초기 프롬프트 재생을 준비하고 있습니다...")
        time.sleep(1.5)  # 1.5초 대기로 오디오 시스템 완전 초기화
        
        # 초기 프롬프트 재생 (한 번만)
        self._stream_tts_realtime(initial_prompt)
        
        # 초기 프롬프트 재생 완료 후 대기
        while self.is_playing:
            time.sleep(0.05)
        time.sleep(0.8)  # 추가 안정화 시간
        
        while True:
            try:
                # TTS 재생 중에는 사용자 입력을 받지 않음
                while self.is_playing:
                    time.sleep(0.05)
                
                # TTS 완전 종료 후 추가 안정화 시간 (1.5초)
                time.sleep(1.5)
                
                # 사용자 음성 입력 (스트리밍 방식)
                audio_data = self._record_audio_stream(duration=5.0)
                if audio_data:
                    user_text = self._transcribe_audio_stream(audio_data)
                else:
                    user_text = input("사용자 입력 > ").strip()
                
                # STT 결과 검증 및 필터링
                if not user_text or len(user_text.strip()) < 2:
                    print("(아무 말도 인식하지 못했습니다. 다시 시도합니다.)")
                    continue
                
                # 비프음이나 시스템음이 포함된 경우 필터링
                user_text = user_text.strip()
                if any(keyword in user_text.lower() for keyword in ['beep', '비프', '시스템', 'system']):
                    print("(시스템음이 감지되었습니다. 다시 시도합니다.)")
                    continue
                
                print(f"USER: {user_text}")
                
                # 종료 조건 확인
                if any(kw in user_text for kw in ["종료", "그만", "quit", "exit"]):
                    self._stream_tts_realtime("대화를 종료합니다.")
                    break
                
                # LLM 스트리밍 응답 및 실시간 TTS
                print("ASSISTANT: ", end="", flush=True)
                response_stream = self._stream_llm_response(user_text)
                
                # 실시간 처리 및 TTS 재생
                self._process_streaming_response(response_stream)
                
                # TTS 재생이 완전히 끝날 때까지 대기
                while self.is_playing:
                    time.sleep(0.05)
                
                # TTS 완전 종료 후 추가 안정화 시간 (2초)
                time.sleep(2.0)
                
            except KeyboardInterrupt:
                print("\n대화를 종료합니다.")
                break

def main() -> None:
    """메인 함수"""
    chat = VoiceChat()
    chat.run()

if __name__ == "__main__":
    main()
