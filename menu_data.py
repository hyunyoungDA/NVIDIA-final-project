# menu_data.py

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
            "notes": "새우",
            "image": "public/spicy-shrimp-burger.png"
        },
        {
            "id": "item_002",
            "name": "치킨버거",
            "category": "메인(버거)",
            "price": 8900,
            "allergens": ["달걀", "밀", "대두", "우유", "닭고기", "땅콩", "조개류(가리비)"],
            "nutrition": {"calorie_kcal": 478.0, "protein_g": 24.0, "sodium_mg": 950.0, "sugar_g": 11.0, "saturated_fat_g": 5.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "닭고기",
            "image": "public/crispy-chicken-burger.png"
        },
        {
            "id": "item_003",
            "name": "데리버거",
            "category": "메인(버거)",
            "price": 9500,
            "allergens": ["달걀", "밀", "대두", "우유", "쇠고기", "닭고기", "조개류(가리비)"],
            "nutrition": {"calorie_kcal": 446.0, "protein_g": 19.0, "sodium_mg": 740.0, "sugar_g": 10.0, "saturated_fat_g": 7.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "쇠고기, 닭고기, 조개류",
            "image": "public/teriyaki-chicken-burger.png"
        },
        {
            "id": "item_004",
            "name": "모짜렐라 버거",
            "category": "메인(버거)",
            "price": 10500,
            "allergens": ["달걀", "밀", "대두", "우유", "쇠고기", "돼지고기"],
            "nutrition": {"calorie_kcal": 699.0, "protein_g": 30.0, "sodium_mg": 1020.0, "sugar_g": 6.0, "saturated_fat_g": 16.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": False, "no_alcohol": True},
            "notes": "쇠고기, 돼지고기",
            "image": "public/melting-mozzarella-burger.png"
        },
        {
            "id": "item_005",
            "name": "불고기버거",
            "category": "메인(버거)",
            "price": 11900,
            "allergens": ["밀", "대두", "달걀", "우유", "토마토", "쇠고기"],
            "nutrition": {"calorie_kcal": 572.0, "protein_g": 24.0, "sodium_mg": 800.0, "sugar_g": 15.0, "saturated_fat_g": 12.0, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "쇠고기",
            "image": "public/korean-bulgogi-burger.png"
        },
        {
            "id": "item_006",
            "name": "멕시칸 랩",
            "category": "메인(랩)",
            "price": 8500,
            "allergens": ["달걀", "우유", "대두", "밀", "돼지고기", "쇠고기"],
            "nutrition": {"calorie_kcal": 607.4, "protein_g": 19.4, "sodium_mg": 931.2, "sugar_g": 10.9, "saturated_fat_g": 9.9, "carb_g": 52.5},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": False, "no_alcohol": True},
            "notes": "돼지고기, 쇠고기",
            "image": "public/mexican-beef-pork-wrap.png"
        },
        {
            "id": "item_007",
            "name": "연어 포케볼",
            "category": "메인(보울)",
            "price": 13900,
            "allergens": ["대두", "밀"],
            "nutrition": {"calorie_kcal": 475.4, "protein_g": 23.3, "sodium_mg": 577.1, "sugar_g": 4.6, "saturated_fat_g": 3.2, "carb_g": 63.7},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "연어",
            "image" : "public/salmon-poke-bowl.png"
        },
        {
            "id": "item_008",
            "name": "로스트 닭다리살 샐러디",
            "category": "메인(샐러디)",
            "price": 11500,
            "allergens": ["우유", "대두", "밀", "토마토", "닭고기", "쇠고기"],
            "nutrition": {"calorie_kcal": 259.2, "protein_g": 29.7, "sodium_mg": 471.9, "sugar_g": 12.2, "saturated_fat_g": 3.9, "carb_g": 29.7},
            "diet_tags": {"vegan": False, "vegetarian": False, "no_pork": True, "no_alcohol": True},
            "notes": "닭고기, 쇠고기",
            "image" : "public/roasted-chicken-salad.png"
        },
        {
            "id": "item_009",
            "name": "두부 단호박 샐러디",
            "category": "메인(샐러디)",
            "price": 9500,
            "allergens": ["대두", "밀"],
            "nutrition": {"calorie_kcal": 214.6, "protein_g": 6.8, "sodium_mg": 214.9, "sugar_g": 12.4, "saturated_fat_g": 1.1, "carb_g": 28.1},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "비건",
            "image" : "public/tofu-pumpkin-salad-bowl.png"
        },
        {
            "id": "item_010",
            "name": "두부 포케볼",
            "category": "메인(보울)",
            "price": 9900,
            "allergens": ["대두", "호두"],
            "nutrition": {"calorie_kcal": 517.4, "protein_g": 17.0, "sodium_mg": 61.2, "sugar_g": 5.0, "saturated_fat_g": 2.5, "carb_g": 69.4},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "비건",
            "image": "public/tofu-poke-bowl.png"
        },
        {
            "id": "item_011",
            "name": "감자튀김",
            "category": "사이드",
            "price": 3500,
            "allergens": ["대두", "토마토"],
            "nutrition": {"calorie_kcal": 285.0, "protein_g": 3.0, "sodium_mg": 430.0, "sugar_g": 2.0, "saturated_fat_g": 2.8, "carb_g": None},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "감자",
            "image": "public/golden-french-fries.png"
        },
        {
            "id": "item_012",
            "name": "치즈스틱",
            "category": "사이드",
            "price": 4500,
            "allergens": ["밀", "대두", "달걀", "우유"],
            "nutrition": {"calorie_kcal": 158.0, "protein_g": 8.0, "sodium_mg": 270.0, "sugar_g": 1.0, "saturated_fat_g": 3.7, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "치즈",
            "image": "public/crispy-golden-mozzarella-sticks.png"
        },
        {
            "id": "item_013",
            "name": "콜라",
            "category": "음료",
            "price": 2000,
            "allergens": [],
            "nutrition": {"calorie_kcal": 127.0, "protein_g": 0.0, "sodium_mg": 15.0, "sugar_g": 31.0, "saturated_fat_g": 0.0, "carb_g": None},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "음료",
            "image": "public/refreshing-cola.png"
        },
        {
            "id": "item_014",
            "name": "사이다",
            "category": "음료",
            "price": 2000,
            "allergens": [],
            "nutrition": {"calorie_kcal": 133.0, "protein_g": 0.0, "sodium_mg": 7.0, "sugar_g": 31.0, "saturated_fat_g": 0.0, "carb_g": None},
            "diet_tags": {"vegan": True, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "음료",
            "image": "public/refreshing-sprite.png"
        },
        {
            "id": "item_015",
            "name": "아이스크림",
            "category": "디저트",
            "price": 4500,
            "allergens": ["우유", "밀", "대두"],
            "nutrition": {"calorie_kcal": 148.0, "protein_g": 3.0, "sodium_mg": 45.0, "sugar_g": 16.0, "saturated_fat_g": 3.2, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "디저트",
            "image": "public/vanilla-ice-cream.png"
        },
        {
            "id": "item_016",
            "name": "팥빙수",
            "category": "디저트",
            "price": 7500,
            "allergens": ["우유"],
            "nutrition": {"calorie_kcal": 605.0, "protein_g": 10.0, "sodium_mg": 150.0, "sugar_g": 99.0, "saturated_fat_g": 3.1, "carb_g": None},
            "diet_tags": {"vegan": False, "vegetarian": True, "no_pork": True, "no_alcohol": True},
            "notes": "디저트",
            "image": "public/patbingsu.png"
        }
    ]
}