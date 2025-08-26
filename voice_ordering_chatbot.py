import streamlit as st
import streamlit.components.v1 as components
import openai
import json
from datetime import datetime
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import os
from dotenv import load_dotenv
import pandas as pd
import time
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

# 메뉴 데이터
MENU_DATA = {
    "store": "Kiosk-Demo",
    "brand": ["DEMO"],
    "items": [
        {
            "id": "item_001",
            "name": "청양 통새우버거",
            "category": "메인(버거)",
            "price": 12900,
            "allergens": ["달걀", "밀", "대두", "우유", "토마토", "새우", "조개류(굴)"],
            "nutrition": {"calorie_kcal": 540.0, "protein_g": 19.0, "sodium_mg": 1450.0, "sugar_g": 12.0, "saturated_fat_g": 4.1, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "새우"
        },
        {
            "id": "item_002",
            "name": "치킨버거",
            "category": "메인(버거)",
            "price": 8900,
            "allergens": ["달걀", "밀", "대두", "우유", "닭고기", "땅콩", "조개류(가리비)"],
            "nutrition": {"calorie_kcal": 478.0, "protein_g": 24.0, "sodium_mg": 950.0, "sugar_g": 11.0, "saturated_fat_g": 5.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "닭고기"
        },
        {
            "id": "item_003",
            "name": "데리버거",
            "category": "메인(버거)",
            "price": 9500,
            "allergens": ["달걀", "밀", "대두", "우유", "쇠고기", "닭고기", "조개류(가리비)"],
            "nutrition": {"calorie_kcal": 446.0, "protein_g": 19.0, "sodium_mg": 740.0, "sugar_g": 10.0, "saturated_fat_g": 7.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "쇠고기, 닭고기, 조개류"
        },
        {
            "id": "item_004",
            "name": "모짜렐라 버거",
            "category": "메인(버거)",
            "price": 10500,
            "allergens": ["달걀", "밀", "대두", "우유", "쇠고기", "돼지고기"],
            "nutrition": {"calorie_kcal": 699.0, "protein_g": 30.0, "sodium_mg": 1020.0, "sugar_g": 6.0, "saturated_fat_g": 16.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": False, "no_alcohol": True},
            "notes": "쇠고기, 돼지고기"
        },
        {
            "id": "item_005",
            "name": "불고기버거",
            "category": "메인(버거)",
            "price": 11900,
            "allergens": ["밀", "대두", "달걀", "우유", "토마토", "쇠고기"],
            "nutrition": {"calorie_kcal": 572.0, "protein_g": 24.0, "sodium_mg": 800.0, "sugar_g": 15.0, "saturated_fat_g": 12.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "쇠고기"
        },
        {
            "id": "item_006",
            "name": "멕시칸 랩",
            "category": "메인(랩)",
            "price": 8500,
            "allergens": ["달걀", "우유", "대두", "밀", "돼지고기", "쇠고기"],
            "nutrition": {"calorie_kcal": 607.4, "protein_g": 19.4, "sodium_mg": 931.2, "sugar_g": 10.9, "saturated_fat_g": 9.9, "carb_g": 52.5},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": False, "no_alcohol": True},
            "notes": "돼지고기, 쇠고기"
        },
        {
            "id": "item_007",
            "name": "연어 포케볼",
            "category": "메인(보울)",
            "price": 13900,
            "allergens": ["대두", "밀"],
            "nutrition": {"calorie_kcal": 475.4, "protein_g": 23.3, "sodium_mg": 577.1, "sugar_g": 4.6, "saturated_fat_g": 3.2, "carb_g": 63.7},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "연어"
        },
        {
            "id": "item_008",
            "name": "로스트 닭다리살 샐러디",
            "category": "메인(샐러디)",
            "price": 11500,
            "allergens": ["우유", "대두", "밀", "토마토", "닭고기", "쇠고기"],
            "nutrition": {"calorie_kcal": 259.2, "protein_g": 29.7, "sodium_mg": 471.9, "sugar_g": 12.2, "saturated_fat_g": 3.9, "carb_g": 29.7},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "닭고기, 쇠고기"
        },
        {
            "id": "item_009",
            "name": "두부 단호박 샐러디",
            "category": "메인(샐러디)",
            "price": 9500,
            "allergens": ["대두", "밀"],
            "nutrition": {"calorie_kcal": 214.6, "protein_g": 6.8, "sodium_mg": 214.9, "sugar_g": 12.4, "saturated_fat_g": 1.1, "carb_g": 28.1},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "비건"
        },
        {
            "id": "item_010",
            "name": "두부 포케볼",
            "category": "메인(보울)",
            "price": 9900,
            "allergens": ["대두", "호두"],
            "nutrition": {"calorie_kcal": 517.4, "protein_g": 17.0, "sodium_mg": 61.2, "sugar_g": 5.0, "saturated_fat_g": 2.5, "carb_g": 69.4},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "비건"
        },
        {
            "id": "item_011",
            "name": "감자튀김",
            "category": "사이드",
            "price": 3500,
            "allergens": ["대두", "토마토"],
            "nutrition": {"calorie_kcal": 285.0, "protein_g": 3.0, "sodium_mg": 430.0, "sugar_g": 2.0, "saturated_fat_g": 2.8, "carb_g": None},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "감자"
        },
        {
            "id": "item_012",
            "name": "치즈스틱",
            "category": "사이드",
            "price": 4500,
            "allergens": ["밀", "대두", "달걀", "우유"],
            "nutrition": {"calorie_kcal": 158.0, "protein_g": 8.0, "sodium_mg": 270.0, "sugar_g": 1.0, "saturated_fat_g": 3.7, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "치즈"
        },
        {
            "id": "item_013",
            "name": "콜라",
            "category": "음료",
            "price": 2000,
            "allergens": [],
            "nutrition": {"calorie_kcal": 127.0, "protein_g": 0.0, "sodium_mg": 15.0, "sugar_g": 31.0, "saturated_fat_g": 0.0, "carb_g": None},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "음료"
        },
        {
            "id": "item_014",
            "name": "사이다",
            "category": "음료",
            "price": 2000,
            "allergens": [],
            "nutrition": {"calorie_kcal": 133.0, "protein_g": 0.0, "sodium_mg": 7.0, "sugar_g": 31.0, "saturated_fat_g": 0.0, "carb_g": None},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "음료"
        },
        {
            "id": "item_015",
            "name": "아이스크림",
            "category": "디저트",
            "price": 4500,
            "allergens": ["우유", "밀", "대두"],
            "nutrition": {"calorie_kcal": 148.0, "protein_g": 3.0, "sodium_mg": 45.0, "sugar_g": 16.0, "saturated_fat_g": 3.2, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "디저트"
        },
        {
            "id": "item_016",
            "name": "팥빙수",
            "category": "디저트",
            "price": 7500,
            "allergens": ["우유"],
            "nutrition": {"calorie_kcal": 605.0, "protein_g": 10.0, "sodium_mg": 150.0, "sugar_g": 99.0, "saturated_fat_g": 3.1, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "디저트"
        }
    ]
}

# Session State 초기화
def initialize_session_state():
    if 'cart' not in st.session_state:
        st.session_state.cart = {}
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "menu"
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = '메인'
    if 'latest_audio_data' not in st.session_state:
        st.session_state.latest_audio_data = None
    if 'audio_counter' not in st.session_state:
        st.session_state.audio_counter = 0


# LangChain 기반 LLM 호출 함수 (이 함수가 이제 핵심입니다)
def get_langchain_response(user_message, conversation_history):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요."

    llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo", temperature=0.7)
            
    system_template = """
    당신은 한국의 키오스크 주문 도우미입니다. 고객의 주문을 도와주고 친근하게 대화하세요.
    메뉴 정보:
    {menu_data}
    대화 규칙:
    1. 고객이 특정 메뉴를 묻거나 보길 원하면 JSON 형식으로 응답하세요: {{"action": "show_menu", "category": "메뉴의 상위 카테고리(메인, 사이드, 음료, 디저트)"}}
    예시) "버거 보여줘": {{"action": "show_menu", "category": "메인"}}
    2. 고객이 메뉴를 주문하면 JSON 형식으로 응답하세요: {{"action": "add_to_cart", "items": [{{"name": "메뉴명", "quantity": 수량, "item_id": "item_xxx"}}]}}
    3. 고객이 주문 완료나 결제 의사를 표현하면: {{"action": "proceed_to_payment"}}
    4. 일반 대화나 메뉴 추천, 기타 질문에는 일반 텍스트로 응답하세요.
    """
    human_template = "현재 대화 내역: {chat_history}\n고객: {user_input}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", human_template)
    ])
    
    # LangChain Runnable (체인) 구성 및 실행
    chain = prompt | llm
    
    # 대화 기록을 문자열로 변환하여 템플릿에 전달
    chat_history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
    
    response = chain.invoke({
        "user_input": user_message,
        "menu_data": json.dumps(MENU_DATA, ensure_ascii=False, indent=2),
        "chat_history": chat_history_str
    })
    
    return response.content


# AI 응답을 처리하는 함수
def process_ai_response(ai_response):
    try:
        if ai_response.startswith('{') and ai_response.endswith('}'):
            response_json = json.loads(ai_response)
            
            if response_json.get('action') == 'add_to_cart':
                ordered_items = []
                for item in response_json.get('items', []):
                    item_name = item['name']
                    quantity = item['quantity']
                    menu_item = next((x for x in MENU_DATA['items'] if x['name'] == item_name), None)
                    if menu_item:
                        if item_name in st.session_state.cart:
                            st.session_state.cart[item_name]['quantity'] += quantity
                        else:
                            st.session_state.cart[item_name] = {
                                'quantity': quantity,
                                'price': menu_item['price'],
                                'item_id': menu_item['id']
                            }
                        ordered_items.append(f"{item_name} {quantity}개")
                return f"{', '.join(ordered_items)}를 장바구니에 추가했습니다!"
            
            elif response_json.get('action') == 'proceed_to_payment':
                st.session_state.current_page = "payment"
                st.rerun()
                return "결제 페이지로 이동합니다."
            
            elif response_json.get('action') == 'show_menu':
                category = response_json.get('category')
                
                if category.startswith('메인'):
                    st.session_state.selected_category = '메인'
                elif category in [item['category'] for item in MENU_DATA['items']]:
                    st.session_state.selected_category = category
                
                return f"네, {st.session_state.selected_category} 메뉴를 보여드릴게요."
        
        return ai_response
    
    except json.JSONDecodeError:
        return ai_response

# 음성 인식(STT)
def speech_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 음성을 듣고 있습니다...")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language='ko-KR')
            return text
        except sr.UnknownValueError:
            return "음성을 인식할 수 없습니다."
        except sr.RequestError as e:
            return f"음성 인식 서비스 오류: {e}"
        except sr.WaitTimeoutError:
            return "음성 입력 시간 초과"

# gTTS 오디오 생성 함수
def get_audio_bytes(text):
    try:
        tts = gTTS(text, lang='ko')
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        st.error(f"gTTS 오디오 생성 오류: {e}")
        return None

# 장바구니 표시
def display_cart():
    total = 0
    st.markdown("### 🛒 장바구니")
    if not st.session_state.cart:
        st.write("장바구니가 비어있습니다.")
        return
    
    for item_name, item_data in st.session_state.cart.items():
        quantity = item_data['quantity']
        price = item_data['price']
        item_total = quantity * price
        total += item_total
        
        col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
        with col_c1:
            st.write(f"**{item_name}**")
        with col_c2:
            st.write(f"{quantity}개")
        with col_c3:
            if st.button("❌", key=f"remove_{item_name}"):
                del st.session_state.cart[item_name]
                st.rerun()
    
    st.markdown("---")
    st.markdown(f"### 총 금액: **{total:,}원**")
    
    if st.button("🛍️ 결제하기", key="checkout_button", use_container_width=True):
        st.session_state.current_page = "payment"
        st.rerun()

# 메뉴판 페이지
def display_menu_page():
    df = pd.DataFrame(MENU_DATA['items'])
    df['display_category'] = df['category'].apply(lambda x: '메인' if x.startswith('메인') else x)
    
    categories = sorted(df['display_category'].unique().tolist())
    
    try:
        default_index = categories.index(st.session_state.selected_category)
    except ValueError:
        default_index = 0
    
    selected_category = st.selectbox(
        "카테고리를 선택하세요:",
        categories,
        index=default_index,
        key='menu_category_select'
    )
    
    st.session_state.selected_category = selected_category

    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df['display_category'] == selected_category]

    if filtered_df.empty:
        st.warning(f"선택한 조건에 맞는 '{selected_category}' 메뉴가 없습니다.")
    else:
        st.subheader(f"✨ {selected_category} 메뉴")
        for index, item in filtered_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### **{item['name']}**")
                    st.markdown(f"가격: **{item['price']:,}원**")
                with col2:
                    st.markdown(" ")
                    if st.button("주문하기", key=f"order_{item['id']}"):
                        add_to_cart_from_button(item['name'], 1)
                        
def add_to_cart_from_button(item_name, quantity):
    menu_item = next((x for x in MENU_DATA['items'] if x['name'] == item_name), None)
    if menu_item:
        if item_name in st.session_state.cart:
            st.session_state.cart[item_name]['quantity'] += quantity
        else:
            st.session_state.cart[item_name] = {
                'quantity': quantity,
                'price': menu_item['price'],
                'item_id': menu_item['id']
            }
        st.rerun()

# 결제 페이지
def display_payment_page():
    st.title("💳 결제")
    
    if not st.session_state.cart:
        st.warning("장바구니가 비어있습니다.")
        if st.button("메뉴판으로 돌아가기"):
            st.session_state.current_page = "menu"
            st.rerun()
        return
    
    st.subheader("주문 내역")
    total = 0
    for item_name, item_data in st.session_state.cart.items():
        quantity = item_data['quantity']
        price = item_data['price']
        item_total = quantity * price
        total += item_total
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(item_name)
        with col2:
            st.write(f"{quantity}개")
        with col3:
            st.write(f"{item_total:,}원")
    
    st.markdown("---")
    st.markdown(f"### 총 결제금액: **{total:,}원**")
    
    st.subheader("결제 방법")
    payment_method = st.radio("결제 방법을 선택하세요:", ["카드결제", "현금결제", "모바일페이"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 메뉴판으로 돌아가기", key="back_to_menu"):
            st.session_state.current_page = "menu"
            st.rerun()
    
    with col2:
        if st.button("💳 결제하기", type="primary", key="finalize_payment"):
            st.success(f"주문이 완료되었습니다! 결제금액: {total:,}원 ({payment_method})")
            st.balloons()
            st.session_state.cart = {}
            st.session_state.conversation = []
            
            time.sleep(5)
            st.session_state.current_page = "menu"
            st.rerun()


# 메인 함수
def main():
    st.set_page_config(
        page_title="음성 주문 키오스크",
        page_icon="🍔",
        layout="wide"
    )
    
    initialize_session_state()
    
    menu_col, voice_col = st.columns([2, 1])
    
    with menu_col:
        if st.session_state.current_page == "menu":
            display_menu_page()
        elif st.session_state.current_page == "payment":
            display_payment_page()
            
    with voice_col:
        st.title("🗣️ 음성 주문")
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container(border=True):
            display_cart()
            
        st.markdown("---")
        st.subheader("💬 대화")
        
# 오디오 재생을 위한 빈 컨테이너를 제거
        
        chat_container = st.container(height=300, border=True)
        
        with chat_container:
            for msg in st.session_state.conversation:
                if msg['role'] == 'user':
                    st.markdown(f"**고객:** {msg['content']}")
                else:
                    st.markdown(f"**키오스크:** {msg['content']}")
        
        st.markdown('<div id="scroll_to_bottom"></div>', unsafe_allow_html=True)
        st.markdown("""
            <script>
                var element = document.getElementById("scroll_to_bottom");
                if (element) {
                    element.scrollIntoView({behavior: "smooth", block: "end"});
                }
            </script>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # '음성으로 주문하기' 버튼
        if st.button("🎤 음성으로 주문하기", key="voice_order", type="primary", use_container_width=True):
            with st.spinner("음성을 인식하고 AI 응답을 기다리는 중..."):
                user_input = speech_to_text()
                if user_input and user_input not in ["음성을 인식할 수 없습니다.", "음성 입력 시간 초과"]:
                    st.session_state.conversation.append({"role": "user", "content": user_input})
                    
                    # LangChain 기반 함수를 호출
                    processed_response = process_ai_response(get_langchain_response(user_input, st.session_state.conversation))
                    
                    st.session_state.conversation.append({"role": "assistant", "content": processed_response})

                    # AI의 답변을 음성 데이터로 변환하여 세션 상태에 저장
                    audio_bytes = get_audio_bytes(processed_response)
                    st.session_state.latest_audio_data = audio_bytes
                    
                else:
                    st.error(user_input)
            
            st.rerun()
        
        # '답변 듣기' 버튼
        play_audio = st.button("🔊 답변 듣기", key="play_audio", use_container_width=True)
        
        # 항상 숨겨진 오디오 플레이어 (답변 듣기 버튼 아래)
        if st.session_state.latest_audio_data:
            # CSS를 사용하여 오디오 컨트롤을 완전히 숨김
            st.markdown("""
                <style>
                audio {
                    display: none !important;
                    visibility: hidden !important;
                    position: absolute !important;
                    opacity: 0 !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # 답변 듣기 버튼이 클릭되었을 때만 자동재생
            if play_audio:
                st.audio(st.session_state.latest_audio_data, format='audio/mp3', autoplay=True, loop=False)
            else:
                st.audio(st.session_state.latest_audio_data, format='audio/mp3', autoplay=False, loop=False)
        else:
            if play_audio:
                st.info("재생할 음성 답변이 없습니다.")

if __name__ == "__main__":
    main()