from __future__ import annotations

import os
import time
import threading
import json
import streamlit as st
import tempfile
import wave
import pygame
from typing import Optional, Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import sounddevice as sd
import numpy as np

# 환경변수 로드
load_dotenv()

class StreamlitVoiceChat:
    """Streamlit 통합을 위한 음성 기반 챗봇 클래스"""
    
    def __init__(self):
        # OpenAI 클라이언트 초기화
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        
        self.client = OpenAI(api_key=api_key)
        
        # 상태 변수들
        self.is_active = False
        self.current_step = "start"  # start, allergy, diet, category, ordering, payment
        self.conversation_state = {
            "allergens": [],
            "diet_type": "일반",
            "category": None,
            "cart_items": [],
            "payment_method": None
        }
        
        # 음성 관련 변수들
        self.current_message = ""
        self.voice_thread = None
        self.listening = False
        
        # 임시 디렉터리 설정
        self.tmp_dir = Path(tempfile.gettempdir()) / "streamlit_voice_chat"
        self.tmp_dir.mkdir(exist_ok=True)
        
        # pygame 초기화 (음성 재생용)
        if not pygame.get_init():
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
        
        print("[음성 챗봇] 초기화 완료")
    
    def start_voice_ordering(self) -> None:
        """음성 기반 주문 시작"""
        self.is_active = True
        self.current_step = "allergy"
        
        # 첫 번째 음성 메시지 설정
        self.current_message = "안녕하세요! 음성 주문을 도와드리겠습니다. 먼저 알레르기가 있으시다면 말씀해 주세요. 달걀, 토마토, 새우, 조개류, 닭고기, 땅콩, 쇠고기, 돼지고기, 호두 중에 알레르기가 있으시나요? 없으시면 '없음'이라고 말씀해주세요."
        
        # 음성 상호작용 스레드 시작
        if self.voice_thread is None or not self.voice_thread.is_alive():
            self.voice_thread = threading.Thread(target=self._voice_interaction_loop, daemon=True)
            self.voice_thread.start()
            print("[음성 챗봇] 음성 상호작용 스레드 시작됨")
    
    def _text_to_speech(self, text: str) -> None:
        """OpenAI TTS API를 사용하여 텍스트를 음성으로 변환 및 재생"""
        try:
            print(f"[TTS] 텍스트: {text}")
            
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
            
            # 재생 완료까지 대기
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # 임시 파일 삭제
            os.unlink(temp_file)
            print(f"[TTS] 재생 완료")
            
        except Exception as e:
            print(f"[TTS] 오류: {e}")
    
    def _speech_to_text(self, duration: float = 5.0) -> Optional[str]:
        """마이크로 음성을 녹음하고 OpenAI STT API로 텍스트 변환"""
        try:
            print("[STT] 음성 녹음 시작...")
            
            # 음성 녹음 설정
            sample_rate = 16000
            channels = 1
            
            # sounddevice로 음성 녹음
            recording = sd.rec(
                int(duration * sample_rate), 
                samplerate=sample_rate, 
                channels=channels,
                dtype=np.int16
            )
            
            # 녹음 완료까지 대기
            sd.wait()
            
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
            return result if result else None
            
        except Exception as e:
            print(f"[STT] 오류: {e}")
            return None
    
    def _voice_interaction_loop(self):
        """음성 상호작용 메인 루프"""
        print("[음성 챗봇] 상호작용 루프 시작")
        
        while self.is_active:
            try:
                # 현재 메시지가 있으면 TTS로 재생
                if self.current_message and not self.listening:
                    self._text_to_speech(self.current_message)
                    self.current_message = ""  # 메시지 클리어
                    
                    # 사용자 음성 입력 대기
                    self.listening = True
                    user_text = self._speech_to_text(duration=7.0)
                    self.listening = False
                    
                    if user_text:
                        self._process_voice_input(user_text)
                
                time.sleep(0.5)  # CPU 사용량 조절
                
            except Exception as e:
                print(f"[음성 챗봇] 상호작용 오류: {e}")
                time.sleep(1)
        
        print("[음성 챗봇] 상호작용 루프 종료")
    
    def _process_voice_input(self, user_input: str):
        """사용자 음성 입력 처리"""
        user_input = user_input.lower().strip()
        print(f"[음성 처리] 단계: {self.current_step}, 입력: {user_input}")
        
        if self.current_step == "allergy":
            self._handle_allergy_voice(user_input)
        elif self.current_step == "diet":
            self._handle_diet_voice(user_input)
        elif self.current_step == "category":
            self._handle_category_voice(user_input)
        elif self.current_step == "ordering":
            self._handle_ordering_voice(user_input)
        elif self.current_step == "continue_ordering":
            self._handle_continue_ordering_voice(user_input)
        elif self.current_step == "payment":
            self._handle_payment_voice(user_input)
    
    def _handle_allergy_voice(self, user_input: str):
        """알레르기 음성 입력 처리"""
        allergens = []
        available_allergens = ["달걀", "토마토", "새우", "조개류", "닭고기", "땅콩", "쇠고기", "돼지고기", "호두"]
        
        if "없음" in user_input or "없어" in user_input or "없습니다" in user_input:
            allergens = []
            self.current_message = "알겠습니다. 알레르기가 없으시군요. 이제 식단 유형을 선택해주세요. 일반, 비건, 할랄 중에서 선택해주세요."
        else:
            # 언급된 알레르기 찾기
            for allergen in available_allergens:
                if allergen in user_input:
                    allergens.append(allergen)
            
            if allergens:
                allergen_str = ", ".join(allergens)
                self.current_message = f"{allergen_str} 알레르기를 확인했습니다. 이제 식단 유형을 선택해주세요. 일반, 비건, 할랄 중에서 선택해주세요."
            else:
                self.current_message = "알레르기 정보를 다시 말씀해 주세요. 달걀, 토마토, 새우, 조개류, 닭고기, 땅콩, 쇠고기, 돼지고기, 호두 중에 있으시면 말씀해주시고, 없으시면 '없음'이라고 말씀해주세요."
                return
        
        # 알레르기 정보 저장 및 필터 적용
        self.conversation_state["allergens"] = allergens
        if 'allergy_filter' in st.session_state:
            st.session_state.allergy_filter = allergens
        
        # 다음 단계로
        self.current_step = "diet"
    
    def _handle_diet_voice(self, user_input: str):
        """식단 음성 입력 처리"""
        diet_type = "일반"
        
        if "비건" in user_input or "비건식" in user_input:
            diet_type = "비건"
        elif "할랄" in user_input or "할랄식" in user_input:
            diet_type = "할랄"
        elif "일반" in user_input or "일반식" in user_input:
            diet_type = "일반"
        else:
            self.current_message = "식단 유형을 다시 선택해주세요. 일반, 비건, 할랄 중에서 말씀해주세요."
            return
        
        # 식단 정보 저장 및 필터 적용
        self.conversation_state["diet_type"] = diet_type
        if 'diet_filter' in st.session_state:
            st.session_state.diet_filter = diet_type
        
        self.current_message = f"{diet_type} 식단이 선택되었습니다. 이제 카테고리를 선택해주세요. 든든한 한 끼, 가벼운 간식, 건강한 음료 중에서 선택해주세요."
        
        # 다음 단계로
        self.current_step = "category"
    
    def _handle_category_voice(self, user_input: str):
        """카테고리 음성 입력 처리"""
        category = None
        
        if "든든" in user_input or "한끼" in user_input or "한 끼" in user_input:
            category = "든든한 한 끼"
        elif "가벼운" in user_input or "간식" in user_input:
            category = "가벼운 간식"
        elif "건강한" in user_input or "음료" in user_input:
            category = "건강한 음료"
        else:
            self.current_message = "카테고리를 다시 선택해주세요. 든든한 한 끼, 가벼운 간식, 건강한 음료 중에서 말씀해주세요."
            return
        
        # 카테고리 정보 저장 및 필터 적용
        self.conversation_state["category"] = category
        if 'selected_category' in st.session_state:
            st.session_state.selected_category = category
        
        self.current_message = f"{category} 카테고리가 선택되었습니다. 이제 메뉴를 주문해주세요. 원하시는 메뉴 이름을 말씀해주시거나 '메뉴 보여줘'라고 말씀해주세요."
        
        # 다음 단계로
        self.current_step = "ordering"
    
    def _handle_ordering_voice(self, user_input: str):
        """주문 음성 입력 처리"""
        from menu_data import menu_items
        
        if "메뉴" in user_input and ("보여" in user_input or "알려" in user_input):
            # 현재 필터링된 메뉴 목록 제공
            filtered_items = self._get_filtered_menu_items()
            menu_names = [item["name"] for item in filtered_items[:5]]  # 상위 5개만
            menu_list = ", ".join(menu_names)
            self.current_message = f"현재 추천 메뉴는 {menu_list} 입니다. 원하시는 메뉴 이름을 말씀해주세요."
            return
        elif "주문" in user_input and "완료" in user_input:
            if self.conversation_state["cart_items"]:
                self.current_message = "주문이 완료되었습니다. 결제 방법을 선택해주세요. 카드 결제 또는 현금 결제 중에서 선택해주세요."
                self.current_step = "payment"
            else:
                self.current_message = "장바구니가 비어있습니다. 메뉴를 먼저 선택해주세요."
            return
        else:
            # 메뉴 이름 매칭 시도
            found_item = None
            for item in menu_items:
                if item["name"] in user_input:
                    found_item = item
                    break
            
            if found_item:
                # 수량 추출 (기본값: 1)
                quantity = 1
                numbers = ["한", "두", "세", "네", "다섯", "1", "2", "3", "4", "5"]
                number_map = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5}
                
                for num_word in numbers:
                    if num_word in user_input:
                        quantity = number_map[num_word]
                        break
                
                # 장바구니에 추가
                for _ in range(quantity):
                    if 'cart' not in st.session_state:
                        st.session_state.cart = []
                    st.session_state.cart.append(found_item)
                
                self.conversation_state["cart_items"].append({
                    "name": found_item["name"],
                    "quantity": quantity,
                    "price": found_item["price"]
                })
                
                self.current_message = f"{found_item['name']} {quantity}개가 장바구니에 추가되었습니다. 추가로 주문하시겠습니까? 다른 메뉴 이름을 말씀하시거나 '주문 완료'라고 말씀해주세요."
            else:
                self.current_message = "메뉴를 찾을 수 없습니다. 정확한 메뉴 이름을 말씀해주시거나 '메뉴 보여줘'라고 말씀해주세요."
    
    def _handle_continue_ordering_voice(self, user_input: str):
        """추가 주문 음성 입력 처리"""
        if "아니" in user_input or "없어" in user_input or "완료" in user_input:
            self.current_message = "주문이 완료되었습니다. 결제 방법을 선택해주세요. 카드 결제 또는 현금 결제 중에서 선택해주세요."
            self.current_step = "payment"
        else:
            self.current_step = "ordering"
            self._handle_ordering_voice(user_input)
    
    def _handle_payment_voice(self, user_input: str):
        """결제 음성 입력 처리"""
        payment_method = None
        
        if "카드" in user_input:
            payment_method = "카드"
        elif "현금" in user_input:
            payment_method = "현금"
        else:
            self.current_message = "결제 방법을 다시 선택해주세요. 카드 결제 또는 현금 결제 중에서 말씀해주세요."
            return
        
        # 결제 정보 저장
        self.conversation_state["payment_method"] = payment_method
        if 'selected_payment_method' in st.session_state:
            st.session_state.selected_payment_method = payment_method
        
        self.current_message = f"{payment_method} 결제가 선택되었습니다. 결제를 진행하겠습니다. 감사합니다!"
        
        # 결제 화면으로 이동
        if 'current_view' in st.session_state:
            st.session_state.current_view = "payment"
        self.is_active = False
    
    def _get_filtered_menu_items(self):
        """현재 필터링 조건에 맞는 메뉴 아이템 반환"""
        from menu_data import menu_items
        
        filtered_items = []
        allergens = self.conversation_state.get("allergens", [])
        diet_type = self.conversation_state.get("diet_type", "일반")
        category = self.conversation_state.get("category", None)
        
        for item in menu_items:
            # 알레르기 필터링
            item_allergens = item.get("allergens", [])
            if any(allergen in item_allergens for allergen in allergens):
                continue
            
            # 식단 필터링
            if diet_type == "비건" and not item.get("is_vegan", False):
                continue
            if diet_type == "할랄" and not item.get("is_halal", False):
                continue
            
            # 카테고리 필터링
            if category and item.get("category") != category:
                continue
            
            filtered_items.append(item)
        
        return filtered_items
    
    def handle_allergy_response(self, selected_allergens: List[str]) -> str:
        """알레르기 응답 처리"""
        if "없음" in selected_allergens or not selected_allergens:
            self.conversation_state["allergens"] = []
            st.session_state.allergy_filter = []
        else:
            self.conversation_state["allergens"] = selected_allergens
            st.session_state.allergy_filter = selected_allergens
        
        # 다음 단계로
        self.current_step = "diet"
        self.current_question = """✅ 알레르기 정보가 설정되었습니다.

**2단계: 식단 확인**
식단 유형을 선택해주세요:"""
        return self.current_question
    
    def handle_diet_response(self, diet_type: str) -> str:
        """식단 응답 처리"""
        self.conversation_state["diet_type"] = diet_type
        st.session_state.diet_filter = diet_type
        
        # 다음 단계로
        self.current_step = "category"
        self.current_question = """✅ 식단 정보가 설정되었습니다.

**3단계: 카테고리 선택**
지금 기분은 어떠신가요?"""
        return self.current_question
    
    def handle_category_response(self, category: str) -> str:
        """카테고리 응답 처리"""
        self.conversation_state["category"] = category
        st.session_state.selected_category = category
        
        # 다음 단계로
        self.current_step = "ordering"
        self.current_question = f"""✅ {category} 카테고리가 선택되었습니다.

**4단계: 메뉴 주문**
이제 원하시는 메뉴를 선택해주세요. 아래 메뉴 목록에서 선택하시면 됩니다."""
        return self.current_question
    
    def add_item_to_cart(self, item_name: str, quantity: int = 1) -> str:
        """아이템을 장바구니에 추가"""
        from menu_data import menu_items
        
        # 메뉴 찾기
        for item in menu_items:
            if item["name"] == item_name:
                # 장바구니에 추가
                for _ in range(quantity):
                    st.session_state.cart.append(item)
                
                self.conversation_state["cart_items"].append({
                    "name": item["name"],
                    "quantity": quantity,
                    "price": item["price"]
                })
                
                return f"✅ {item_name} {quantity}개가 장바구니에 추가되었습니다."
        
        return f"❌ {item_name}을 찾을 수 없습니다."
    
    def finish_ordering(self) -> str:
        """주문 완료"""
        self.current_step = "payment"
        self.current_question = """✅ 주문이 완료되었습니다!

**5단계: 결제 방법 선택**
결제 방법을 선택해 주세요:"""
        return self.current_question
    
    def handle_payment_response(self, payment_method: str) -> None:
        """결제 응답 처리"""
        self.conversation_state["payment_method"] = payment_method
        st.session_state.selected_payment_method = payment_method
        
        # 결제 화면으로 이동
        st.session_state.current_view = "payment"
        self.is_active = False
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """현재 대화 상태 반환"""
        return self.conversation_state.copy()
    
    def is_chatbot_active(self) -> bool:
        """챗봇 활성 상태 반환"""
        return self.is_active
    
    def stop_voice_ordering(self) -> None:
        """음성 주문 중지"""
        self.is_active = False
        self.current_step = "start"
        self.current_question = ""
        self.awaiting_response = False
        self.conversation_state = {
            "allergens": [],
            "diet_type": "일반",
            "category": None,
            "cart_items": [],
            "payment_method": None
        }