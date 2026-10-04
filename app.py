import streamlit as st
from groq import Groq
import requests
import random
import urllib.parse
from PIL import Image
import io

# 1. Настройка конфигурации страницы
st.set_page_config(
    page_title="ИИ-Комбайн: Текст, Код, Медиа & Поиск",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Кастомные CSS-стили
st.markdown("""
    <style>
    .main-title {
        font-size: 2.8rem !important;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8585);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #7f8c8d;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .sidebar-card {
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Проверка безопасности API-ключа Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ Ошибка: API-ключ 'GROQ_API_KEY' не найден в Secrets хостинга!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. Оптимизированная функция перевода промптов
def enhance_and_translate(user_text, mode="image"):
    try:
        system_role = (
            "You are a prompt translator. Translate the user input into a short, concise English image prompt. "
            "CRITICAL: The prompt must be VERY SHORT (MAXIMUM 15 WORDS). Just output key objects separated by commas. "
            "DO NOT include any URLs, website names, or domains like 'pollinations.ai' in your response. "
            "Output ONLY the final English words, no quotes, no explanations."
        )
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1,
            max_tokens=40
        )
        result = response.choices.message.content.strip() if hasattr(response, 'choices') else response['choices']['message']['content'].strip()
        return result.replace('"', '').replace("'", "")
    except:
        return "beautiful scenery"

# 5. ИЗОЛИРОВАННАЯ ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ МЕДИА
def generate_media_payload(media_prompt, media_type):
    try:
        raw_desc = enhance_and_translate(media_prompt, mode="image")
        
        # Жесткая очистка доменов
        cleaned_desc = raw_desc.replace("pollinations.ai", "").replace("pollinations", "").strip()
        if cleaned_desc.startswith("p/"):
            cleaned_desc = cleaned_desc[2:]
        if cleaned_desc.startswith("/"):
            cleaned_desc = cleaned_desc[1:]
            
        seed = random.randint(1, 999999)
        
        if media_type == "Высокоточное Фото (FLUX)":
            full_style = f"{cleaned_desc}, high quality photography"
            encoded_param = urllib.parse.quote_plus(full_style)
            media_url = f"https://pollinations.ai{encoded_param}?width=768&height=432&seed={seed}&model=flux&nologo=true"
        else:
            full_style = f"{cleaned_desc}, simple motion animation loop"
            encoded_param = urllib.parse.quote_plus(full_style)
            media_url = f"https://pollinations.ai{encoded_param}?width=512&height=512&seed={seed}&nologo=true"
            
        res = requests.get(media_url)
        return res, cleaned_desc
    except Exception as e:
        return None, str(e)

# 6. Боковая панель
with st.sidebar:
    st.markdown("<div class='sidebar-card'><h3>⚙️ Настройки Системы</h3></div>", unsafe_allow_html=True)
    model_choice = st.selectbox(
        "Модель ИИ для текста и кода:",
        ("qwen/qwen3.8-27b", "openai/gpt-oss-120b"),
        help="Выбор активной нейронной сети."
    )
    temperature = st.slider("Креативность ответов:", 0.0, 1.0, 0.3, 0.1)

# 7. Главный интерфейс
st.markdown("<h1 class='main-title'>🧠 Универсальный ИИ-Комбайн X5</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Кодинг, статьи, рецепты с иконками, генерация графики и умный поиск в интернете в единой панели</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛠 Кодинг & Скрипты", 
    "📝 Текст & Копирайтинг", 
    "🍳 Рецепты с иконками", 
    "🎨 Фото & Видео",
    "🌐 Поиск в Интернете"
])

# --- ВКЛАДКА 1: ГЕНЕРАЦИЯ КОДА ---
with tab1:
    st.markdown("### 🤖 Создание скриптов и чат-ботов")
    col1, col2 = st.columns(2)
    with col1:
        category = st.radio("Направление:", ("🤖 Telegram-бот (Python)", "🌐 Веб-крипт (JavaScript)", "🎨 Верстка (HTML/CSS)", "🐍 Автоматизация (Python)"))
    with col2:
        user_prompt = st.text_area("Техническое задание (ТЗ) для кода:", height=130, placeholder="Например: Скрипт калькулятора кредита...", key="code_ta")
        
    if st.button("🚀 Сгенерировать код", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.warning("⚠️ Введите ТЗ.")
        else:
            with st.spinner("🧠 ИИ пишет чистый код..."):
                try:
                    sys_prompt = f"Ты Senior разработчик. Напиши чистый, рабочий код для '{category}' по ТЗ: {user_prompt}. Добавь комментарии."
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=temperature)
                    code_out = res.choices.message.content if hasattr(res, 'choices') else res['choices']['message']['content']
                    st.success("🎉 Код успешно сгенерирован!")
                    st.code(code_out, language="python" if "Python" in category or "бот" in category.lower() else "javascript")
                except Exception as e: 
                    st.error(f"Ошибка API: {str(e)}")

# --- ВКЛАДКА 2: ГЕНЕРАЦИЯ ТЕКСТА И СТАТЕЙ ---
with tab2:
    st.markdown("### 📝 Генератор статей и описаний для видео")
    text_mode = st.selectbox("Что нужно сгенерировать?", ["Полноценная статья/Пост", "SEO-описание для Видео (YouTube/Reels)", "Продающий текст"])
    text_topic = st.text_input("Укажите тему или ключевые слова:", key="text_ti")
    text_length = st.select_slider("Желаемый объем текста:", options=["Короткий", "Средний", "Развернутый лонгрид"])
    
    if st.button("📝 Создать текст", type="primary", use_container_width=True):
        if not text_topic.strip(): 
            st.warning("⚠️ Введите тему текста.")
        else:
            with st.spinner("✍️ Писатель ИИ формулирует структуру и пишет текст..."):
                try:
                    sys_prompt = f"Ты профессиональный копирайтер. Напиши '{text_mode}' на тему: '{text_topic}'. Объем текста: {text_length}. Текст должен быть структурированным, интересным и грамотным."
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=0.7)
                    text_out = res.choices.message.content if hasattr(res, 'choices') else res['choices']['message']['content']
                    st.success("🎉 Текст успешно написан!")
                    st.markdown(text_out)
                except Exception as e: 
                    st.error(f"Ошибка: {str(e)}")

# --- ВКЛАДКА 3: КУЛИНАРНЫЕ РЕЦЕПТЫ С ИКОНКАМИ ---
with tab3:
    st.markdown("### 🍳 ИИ-Шеф: Создание интерактивных рецептов с эмодзи")
    dish_name = st.text_input("Введите название блюда или доступные ингредиенты:", placeholder="Пример: Паста Карбонара или Курица, картошка, грибы", key="dish_ti")
    diet_pref = st.multiselect("Особые предпочтения (необязательно):", ["Без глютена", "Вегетарианское", "ПП / Низкокалорийное", "Быстро (до 20 мин)"])
    
    if st.button("🍳 Сформировать рецепт", type="primary", use_container_width=True):
        if not dish_name.strip(): 
            st.warning("⚠️ Введите название блюда.")
        else:
            with st.spinner("👩‍🍳 Шеф-повар ИИ составляет идеальные пропорции и подбирает иконки..."):
                try:
                    sys_prompt = (
                        f"Ты профессиональный ИИ-шеф. Создай подробный кулинарный рецепт на основе запроса: '{dish_name}'. "
                        f"Учти ограничения: {', '.join(diet_pref)}. "
                        "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: Добавляй подходящую визуальную эмодзи-иконку перед КАЖДЫМ ингредиентом и перед КАЖДЫМ шагом приготовления. Сделай красивую разметку."
                    )
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=0.5)
                    recipe_out = res.choices.message.content if hasattr(res, 'choices') else res['choices']['message']['content']
                    st.success("👨‍🍳 Рецепт готов!")
                    st.markdown(recipe_out)
                except Exception as e: 
                    st.error(f"Ошибка: {str(e)}")

# --- ВКЛАДКА 4: ГЕНЕРАЦИЯ МЕДИА (ФОТО И ВИДЕО) ---
with tab4:
    st.markdown("### 🎨 Создание графики и анимаций по тексту")
    media_prompt = st.text_input("Опишите сцену для графики (на русском):", placeholder="Пример: Парень и девушка идут по лесу...", key="media_ti")
    media_type = st.radio("Что сгенерировать?", ["Высокоточное Фото (FLUX)", "Анимация (Короткое видео / GIF)"])
    
    if st.button("🎨 Начать визуализацию", type="primary", use_container_width=True):
        if not media_prompt.strip(): 
            st.warning("⚠️ Укажите описание сцены.")
        else:
            placeholder = st.empty()
            with placeholder.container():
                with st.spinner("🚀 Отправка запроса на графический кластер... Ожидайте отрисовки."):
                    response_obj, meta_info = generate_media_payload(media_prompt, media_type)
                    
