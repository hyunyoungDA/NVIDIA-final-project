import streamlit as st
import os
import time
import threading
import webbrowser
from PIL import Image
from menu_data import (
    menu_items, categories, main_subcategories, 
    diet_lists, allergen_map, allergen_list
)

# 페이지 설정
st.set_page_config(
    page_title="키오스크 메뉴",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 세션 상태 초기화
def initialize_session_state():
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "menu"
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'order_type' not in st.session_state:
        st.session_state.order_type = "dineIn"  # 기본값을 매장으로 설정
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = "전체"
    if 'selected_subcategory' not in st.session_state:
        st.session_state.selected_subcategory = "전체"
    if 'special_requests' not in st.session_state:
        st.session_state.special_requests = ""
    if 'allergy_filter' not in st.session_state:
        st.session_state.allergy_filter = []
    if 'diet_filter' not in st.session_state:
        st.session_state.diet_filter = "일반"
    if 'order_number' not in st.session_state:
        st.session_state.order_number = ""
    if 'selected_payment_method' not in st.session_state:
        st.session_state.selected_payment_method = ""

# 필터링 함수
def filter_menu_items():
    items = menu_items.copy()
    
    # 카테고리 필터
    if st.session_state.selected_category != "전체":
        items = [item for item in items if item["category"] == st.session_state.selected_category]
    
    # 서브카테고리 필터
    if st.session_state.selected_category == "메인" and st.session_state.selected_subcategory != "전체":
        items = [item for item in items if item.get("subcategory") == st.session_state.selected_subcategory]
    
    # 알레르기 필터
    if st.session_state.allergy_filter:
        filtered_items = []
        for item in items:
            item_allergens = allergen_map.get(item["name"], [])
            if not any(allergen in item_allergens for allergen in st.session_state.allergy_filter):
                filtered_items.append(item)
        items = filtered_items
    
    # 식단 필터
    if st.session_state.diet_filter == "비건":
        items = [item for item in items if item["name"] in diet_lists["vegan"]]
    elif st.session_state.diet_filter == "채식":
        items = [item for item in items if item["name"] in diet_lists["vegetarian"]]
    
    return items

# 장바구니 함수들
def add_to_cart(item):
    for cart_item in st.session_state.cart:
        if cart_item["id"] == item["id"]:
            cart_item["quantity"] += 1
            return
    item_copy = item.copy()
    item_copy["quantity"] = 1
    st.session_state.cart.append(item_copy)

def update_quantity(item_id, change):
    for i, item in enumerate(st.session_state.cart):
        if item["id"] == item_id:
            new_quantity = item["quantity"] + change
            if new_quantity <= 0:
                st.session_state.cart.pop(i)
            else:
                st.session_state.cart[i]["quantity"] = new_quantity
            break

def get_total_price():
    return sum(item["price"] * item["quantity"] for item in st.session_state.cart)

def get_total_items():
    return sum(item["quantity"] for item in st.session_state.cart)

# 결제 관련 함수
def generate_order_number():
    import random
    return str(random.randint(1000, 9999))

def reset_order():
    st.session_state.cart = []
    st.session_state.special_requests = ""
    st.session_state.order_type = None
    st.session_state.current_view = "orderType"
    st.session_state.selected_category = "메인"
    st.session_state.selected_subcategory = "버거"
    st.session_state.allergy_filter = []
    st.session_state.diet_filter = "일반"
    st.session_state.order_number = ""
    st.session_state.selected_payment_method = ""

# 메뉴 상세 정보 표시
def show_menu_detail(item):
    with st.expander(f"📋 {item['name']} 상세 정보", expanded=True):
        # 컬럼 중첩 문제를 피하기 위해 세로 배치로 변경
        try:
            if os.path.exists(item["image"]):
                image = Image.open(item["image"])
                st.image(image, width=300, use_container_width=False)
            else:
                st.write("🍽️ 이미지 없음")
        except:
            st.write("🍽️ 이미지 로드 실패")
        
        st.write(f"**설명:** {item['description']}")
        st.write(f"**가격:** ₩{item['price']:,}")
        st.write(f"**조리시간:** {item['cooking_time']}분")
        st.write(f"**나트륨:** {item['sodium']}mg")
        
        # 알레르기 정보
        allergens = allergen_map.get(item["name"], [])
        if allergens:
            allergen_tags = " ".join([f"`{allergen}`" for allergen in allergens])
            st.write(f"**알레르기:** {allergen_tags}")
        else:
            st.write("**알레르기:** 없음")
        
        # 식단 정보
        diet_info = []
        if item["name"] in diet_lists["vegan"]:
            diet_info.append("비건")
        elif item["name"] in diet_lists["vegetarian"]:
            diet_info.append("채식")
        else:
            diet_info.append("일반")
        
        if item.get("is_customizable"):
            diet_info.append("커스터마이징 가능")
        
        st.write(f"**식단 정보:** {', '.join(diet_info)}")
        
        if st.button(f"장바구니에 담기 - {item['name']}", key=f"detail_add_{item['id']}"):
            add_to_cart(item)
            st.success(f"{item['name']}이(가) 장바구니에 추가되었습니다!")
            st.rerun()

# 메인 앱
def main():
    initialize_session_state()
    
    # 헤더
    st.markdown("""
    <style>
    .main-header {
        background-color: white;
        padding: 1rem;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    .menu-card {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: white;
    }
    .diet-tag {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.1rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .vegan-tag { background-color: #166534; color: white; }
    .vegetarian-tag { background-color: #84cc16; color: white; }
    .normal-tag { background-color: #f3f4f6; color: #374151; }
    .customizable-tag { background-color: #fef3c7; color: #92400e; }
    .menu-image {
        width: 200px;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
        display: block;
        margin: 0 auto;
    }
    .cart-image {
        width: 120px;
        height: 90px;
        object-fit: cover;
        border-radius: 6px;
        display: block;
        margin: 0 auto;
    }
    .drink-image {
        width: 150px;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
        display: block;
        margin: 0 auto;
    }
    .cheese-sticks-image {
        width: 150px;
        height: 120px;
        object-fit: cover;
        border-radius: 8px;
        display: block;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 헤더 영역
    header_col1, header_col2, header_col3 = st.columns([2, 3, 2])
    
    with header_col1:
        if st.session_state.current_view == "menu" and st.session_state.order_type:
            if st.button(f"📍 {('매장' if st.session_state.order_type == 'dineIn' else '포장')}", key="order_type_btn"):
                # 매장/포장 전환
                st.session_state.order_type = "takeOut" if st.session_state.order_type == "dineIn" else "dineIn"
                st.rerun()
    
    with header_col2:
        st.markdown("<h1 style='text-align: center;'>🍔 키오스크 메뉴</h1>", unsafe_allow_html=True)
    
    with header_col3:
        col_mode, col_cart = st.columns(2)
        with col_mode:
            st.markdown("👤 **일반모드**")
        
        with col_cart:
            if st.session_state.cart:
                if st.button(f"🛒 장바구니 ({get_total_items()})", key="cart_btn"):
                    st.session_state.current_view = "cart"
                    st.rerun()
    
    # 뷰별 렌더링
    if st.session_state.current_view == "menu":
        show_menu_view()
    elif st.session_state.current_view == "cart":
        show_cart_view()
    elif st.session_state.current_view == "payment":
        show_payment_view()
    elif st.session_state.current_view == "processing":
        show_processing_view()
    elif st.session_state.current_view == "completed":
        show_completed_view()

def show_order_type_selection():
    st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>주문 방식을 선택하세요</h2>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🍽️ 매장", key="dine_in", use_container_width=True):
            st.session_state.order_type = "dineIn"
            # 카테고리를 "전체"로 설정
            st.session_state.selected_category = "전체"
            st.session_state.selected_subcategory = "전체"
            st.session_state.current_view = "menu"
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📦 포장", key="take_out", use_container_width=True):
            st.session_state.order_type = "takeOut"
            # 카테고리를 "전체"로 설정
            st.session_state.selected_category = "전체"
            st.session_state.selected_subcategory = "전체"
            st.session_state.current_view = "menu"
            st.rerun()

def show_menu_view():
    # 필터 설정 영역
    st.markdown("### 🔧 설정")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        with st.expander("🚫 알레르기 설정"):
            for allergen in allergen_list:
                current_value = allergen in st.session_state.allergy_filter
                new_value = st.checkbox(allergen, value=current_value, key=f"allergy_{allergen}")
                
                if new_value != current_value:
                    if new_value:
                        st.session_state.allergy_filter.append(allergen)
                    else:
                        st.session_state.allergy_filter.remove(allergen)
    
    with filter_col2:
        with st.expander("🥗 식단 설정"):
            diet_options = ["일반", "채식", "비건"]
            selected_diet = st.radio(
                "식단 선택", 
                diet_options, 
                index=diet_options.index(st.session_state.diet_filter),
                key="diet_radio"
            )
            if selected_diet != st.session_state.diet_filter:
                st.session_state.diet_filter = selected_diet
    
    with filter_col3:
        if st.button("🔄 필터 리셋"):
            st.session_state.allergy_filter = []
            st.session_state.diet_filter = "일반"
            st.rerun()
    
    # 카테고리 선택
    st.markdown("### 📂 카테고리")
    category_cols = st.columns(len(categories))
    for i, category in enumerate(categories):
        with category_cols[i]:
            if st.button(
                category, 
                key=f"cat_{category}",
                type="primary" if st.session_state.selected_category == category else "secondary",
                use_container_width=True
            ):
                st.session_state.selected_category = category
                st.session_state.selected_subcategory = "전체"
                st.rerun()
    
    # 서브카테고리 선택 (메인일 때만)
    if st.session_state.selected_category == "메인":
        st.markdown("### 🍽️ 세부 카테고리")
        sub_cols = st.columns(len(main_subcategories))
        for i, subcategory in enumerate(main_subcategories):
            with sub_cols[i]:
                if st.button(
                    subcategory,
                    key=f"subcat_{subcategory}",
                    type="primary" if st.session_state.selected_subcategory == subcategory else "secondary",
                    use_container_width=True
                ):
                    st.session_state.selected_subcategory = subcategory
                    st.rerun()
    
    # 메뉴 목록
    filtered_items = filter_menu_items()
    show_normal_menu_view(filtered_items)

def show_normal_menu_view(filtered_items):
    st.markdown("### 🍽️ 메뉴")
    
    if not filtered_items:
        st.warning("조건에 맞는 메뉴가 없습니다.")
        return
    
    # 3열 그리드로 작은 메뉴 카드 표시
    cols_per_row = 3
    for i in range(0, len(filtered_items), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(filtered_items):
                with cols[j]:
                    show_menu_card_small(filtered_items[i + j])

def show_menu_card_small(item):
    with st.container():
        try:
            if os.path.exists(item["image"]):
                image = Image.open(item["image"])
                # 음료는 정사각형, 치즈스틱은 세로 길이 줄임
                if item["category"] == "음료":
                    st.image(image, width=150, use_container_width=False)
                elif item["name"] == "치즈스틱":
                    st.image(image, width=150, use_container_width=False)
                else:
                    st.image(image, width=150, use_container_width=False)
            else:
                st.write("🍽️ 이미지 없음")
        except:
            st.write("🍽️ 이미지 로드 실패")
        
        st.markdown(f"**{item['name']}**")
        
        # 태그들
        tags_html = ""
        if item["name"] in diet_lists["vegan"]:
            tags_html += '<span class="diet-tag vegan-tag">비건</span>'
        elif item["name"] in diet_lists["vegetarian"]:
            tags_html += '<span class="diet-tag vegetarian-tag">채식</span>'
        
        if item.get("is_customizable"):
            tags_html += '<span class="diet-tag customizable-tag">커스터마이징</span>'
        
        tags_html += f'<span class="diet-tag normal-tag">{item["cooking_time"]}분</span>'
        tags_html += f'<span class="diet-tag normal-tag">₩{item["price"]:,}</span>'
        
        st.markdown(tags_html, unsafe_allow_html=True)
        
        button_col1, button_col2 = st.columns(2)
        with button_col1:
            if st.button("담기", key=f"add_{item['id']}", use_container_width=True):
                add_to_cart(item)
                st.success(f"{item['name']} 추가!")
                time.sleep(1)
                st.rerun()
        
        with button_col2:
            if st.button("상세", key=f"detail_{item['id']}", use_container_width=True):
                show_menu_detail(item)

def show_cart_view():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 🛒 장바구니")
    with col2:
        if st.button("← 메뉴로 돌아가기"):
            st.session_state.current_view = "menu"
            st.rerun()
    
    if not st.session_state.cart:
        st.markdown("<div style='text-align: center; padding: 3rem;'>", unsafe_allow_html=True)
        st.write("🛒 장바구니가 비어있습니다")
        if st.button("메뉴 보기"):
            st.session_state.current_view = "menu"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # 장바구니 아이템들
    for item in st.session_state.cart:
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
            
            with col1:
                try:
                    if os.path.exists(item["image"]):
                        image = Image.open(item["image"])
                        st.image(image, width=120, use_container_width=False)
                    else:
                        st.write("🍽️")
                except:
                    st.write("🍽️")
            
            with col2:
                st.write(f"**{item['name']}**")
                st.write(f"₩{item['price']:,}")
            
            with col3:
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                with btn_col1:
                    if st.button("➖", key=f"minus_{item['id']}", help="수량 줄이기"):
                        update_quantity(item['id'], -1)
                        st.rerun()
                
                with btn_col2:
                    st.markdown(f"<div style='text-align: center; padding: 0.5rem; background-color: #374151; color: white; border-radius: 5px; font-weight: bold; font-size: 1.1rem;'>{item['quantity']}</div>", unsafe_allow_html=True)
                
                with btn_col3:
                    if st.button("➕", key=f"plus_{item['id']}", help="수량 늘리기"):
                        update_quantity(item['id'], 1)
                        st.rerun()
            
            with col4:
                st.write(f"**₩{(item['price'] * item['quantity']):,}**")
            
            st.divider()
    
    # 특별 요청사항
    st.markdown("### 📝 특별 요청사항")
    st.session_state.special_requests = st.text_area(
        "특별한 요청사항이 있으시면 입력해주세요",
        value=st.session_state.special_requests,
        key="special_requests_input"
    )
    
    # 총 금액 및 결제 버튼
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### 총 금액: ₩{get_total_price():,}")
    with col2:
        if st.button("💳 결제하기", use_container_width=True, type="primary"):
            st.session_state.current_view = "payment"
            st.rerun()

def show_payment_view():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 💳 결제 방법 선택")
    with col2:
        if st.button("← 장바구니로"):
            st.session_state.current_view = "cart"
            st.rerun()
    
    # 주문 요약
    st.markdown("### 📋 주문 내역")
    for item in st.session_state.cart:
        st.write(f"{item['name']} x {item['quantity']} = ₩{(item['price'] * item['quantity']):,}")
    
    st.markdown(f"**총 금액: ₩{get_total_price():,}**")
    st.divider()
    
    # 결제 방법 선택
    st.markdown("### 💳 결제 방법을 선택하세요")
    
    payment_col1, payment_col2 = st.columns(2)
    
    with payment_col1:
        if st.button("💳 신용카드", use_container_width=True, key="card_btn"):
            process_payment("신용카드")
        
        if st.button("📱 모바일 결제", use_container_width=True, key="mobile_btn"):
            process_payment("모바일 결제")
    
    with payment_col2:
        if st.button("💵 현금", use_container_width=True, key="cash_btn"):
            process_payment("현금")
        
        if st.button("🎁 상품권", use_container_width=True, key="gift_btn"):
            process_payment("상품권")

def process_payment(method):
    st.session_state.selected_payment_method = method
    st.session_state.order_number = generate_order_number()
    st.session_state.current_view = "processing"
    st.rerun()

def show_processing_view():
    st.markdown("<div style='text-align: center; padding: 3rem;'>", unsafe_allow_html=True)
    st.markdown("## ⏳ 결제 처리 중")
    st.markdown("잠시만 기다려주세요...")
    
    if st.session_state.selected_payment_method:
        st.write(f"결제 방법: {st.session_state.selected_payment_method}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 2초 후 완료 화면으로
    time.sleep(2)
    st.session_state.current_view = "completed"
    st.rerun()

def show_completed_view():
    st.markdown("<div style='text-align: center; padding: 3rem;'>", unsafe_allow_html=True)
    st.markdown("# ✅ 결제 완료!")
    st.markdown("주문이 성공적으로 접수되었습니다.")
    
    st.markdown(f"## 주문번호: {st.session_state.order_number}")
    
    st.write(f"주문 유형: {'매장 식사' if st.session_state.order_type == 'dineIn' else '포장'}")
    st.write(f"총 금액: ₩{get_total_price():,}")
    
    st.markdown("5초 후 자동으로 얼굴 인식 페이지로 돌아갑니다.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 5초 후 얼굴 인식 페이지로 이동
    time.sleep(5)
    webbrowser.open("http://localhost:8501")
    reset_order()
    st.rerun()

if __name__ == "__main__":
    main()
