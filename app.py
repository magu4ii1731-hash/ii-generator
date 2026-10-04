import streamlit as st
from groq import Groq
import requests
import random
import urllib.parse

# 1. Настройка конфигурации страницы (Первая команда Streamlit)
st.set_page_config(
    page_title="ИИ-Комбайн 2026: Текст, Код, Медиа & Поиск",
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

# 4. Внутренние утилиты для ИИ и перевода
def enhance_and_translate(user_text, mode="image"):
    try:
        if mode == "image":
            system_role = "You are a professional prompt engineer. Translate the input to English and expand it with beautiful artistic details. Output ONLY the final English prompt."
        else:
            system_role = "You are an AI assistant. Translate the text to English. Output ONLY the translation."
            
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip() if hasattr(response, 'choices') else response['choices']['message']['content'].strip()
    except:
        return user_text

# 5. Боковая панель
with st.sidebar:
    st.markdown("<div class='sidebar-card'><h3>⚙️ Настройки Системы</h3></div>", unsafe_allow_html=True)
    model_choice = st.selectbox(
        "Модель ИИ для текста и кода:",
        ("qwen/qwen3.8-27b", "openai/gpt-oss-120b"),
        help="Выбор активной нейронной сети."
    )
    temperature = st.slider("Креативность ответов:", 0.0, 1.0, 0.3, 0.1)
    st.markdown("---")
    st.markdown("🌐 **Поиск в сети:** Бесплатный шлюз без ключей (Активен)")

# 6. Главный интерфейс
st.markdown("<h1 class='main-title'>🧠 Универсальный ИИ-Комбайн X5</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Кодинг, статьи, рецепты с иконками, генерация графики и умный поиск в интернете в единой панели</p>", unsafe_allow_html=True)

# Пять основных вкладок приложения
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛠 Кодинг & Скрипты", 
    "📝 Текст & Копирайтинг", 
    "🍳 Рецепты с иконками", 
    "🎨 Генерация фото & Видео",
    "🌐 Поиск в Интернете"
])

# --- ВКЛАДКА 1: ГЕНЕРАЦИЯ КОДА ---
with tab1:
    st.markdown("### 🤖 Создание скриптов и чат-ботов")
    col1, col2 = st.columns(2)
    with col1:
        category = st.radio("Направление:", ("🤖 Telegram-бот (Python)", "🌐 Веб-скрипт (JavaScript)", "🎨 Верстка (HTML/CSS)", "🐍 Автоматизация (Python)"))
    with col2:
        user_prompt = st.text_area("Техническое задание (ТЗ) для кода:", height=130, placeholder="Например: Скрипт калькулятора кредита...")
        
    if st.button("🚀 Сгенерировать код", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.warning("⚠️ Введите ТЗ.")
        else:
            with st.spinner("🧠 ИИ пишет чистый код..."):
                try:
                    sys_prompt = f"Ты Senior разработчик. Напиши чистый, рабочий код для '{category}' по ТЗ: {user_prompt}. Добавь комментарии."
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=temperature)
                    code_out = res.choices[0].message.content if hasattr(res, 'choices') else res['choices']['message']['content']
                    st.success("🎉 Код успешно сгенерирован!")
                    st.code(code_out, language="python" if "Python" in category or "бот" in category.lower() else "javascript")
                except Exception as e: st.error(f"Ошибка API: {str(e)}")

# --- ВКЛАДКА 2: ГЕНЕРАЦИЯ ТЕКСТА И СТАТЕЙ ---
with tab2:
    st.markdown("### 📝 Генератор статей и описаний для видео")
    text_mode = st.selectbox("Что нужно сгенерировать?", ["Полноценная статья/Пост", "SEO-описание для Видео (YouTube/Reels)", "Продающий текст"])
    text_topic = st.text_input("Укажите тему или ключевые слова:")
    text_length = st.select_slider("Желаемый объем текста:", options=["Короткий", "Средний", "Развернутый лонгрид"])
    
    if st.button("📝 Создать текст", type="primary", use_container_width=True):
        if not text_topic.strip(): st.warning("⚠️ Введите тему текста.")
        else:
            with st.spinner("✍️ Писатель ИИ формулирует структуру и пишет текст..."):
                try:
                    sys_prompt = f"Ты профессиональный копирайтер. Напиши '{text_mode}' на тему: '{text_topic}'. Объем текста: {text_length}. Текст должен быть структурированным, интересным и грамотным."
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=0.7)
                    text_out = res.choices[0].message.content if hasattr(res, 'choices') else res['choices']['message']['content']
                    st.success("🎉 Текст успешно написан!")
                    st.markdown(text_out)
                except Exception as e: st.error(f"Ошибка: {str(e)}")

# --- ВКЛАДКА 3: КУЛИНАРНЫЕ РЕЦЕПТЫ С ИКОНКАМИ ---
with tab3:
    st.markdown("### 🍳 ИИ-Шеф: Создание интерактивных рецептов с эмодзи")
    dish_name = st.text_input("Введите название блюда или доступные ингредиенты:", placeholder="Пример: Паста Карбонара или Курица, картошка, грибы")
    diet_pref = st.multiselect("Особые предпочтения (необязательно):", ["Без глютена", "Вегетарианское", "ПП / Низкокалорийное", "Быстро (до 20 мин)"])
    
    if st.button("🍳 Сформировать рецепт", type="primary", use_container_width=True):
        if not dish_name.strip(): st.warning("⚠️ Введите название блюда.")
        else:
            with st.spinner("👩‍🍳 Шеф-повар ИИ составляет идеальные пропорции и подбирает иконки..."):
                try:
                    sys_prompt = (
                        f"Ты профессиональный ИИ-шеф. Создай подробный кулинарный рецепт на основе запроса: '{dish_name}'. "
                        f"Учти ограничения: {', '.join(diet_pref)}. "
                        "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: Добавляй подходящую визуальную эмодзи-иконку перед КАЖДЫМ ингредиентом и перед КАЖДЫМ шагом приготовления "
                        "(например: '🍅 Томаты - 2 шт.', '🔥 Шаг 1. Разогрейте духовку'). Сделай красивую разметку."
                    )
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=0.5)
                    recipe_out = res.choices[0].message.content if hasattr(res, 'choices') else res['choices']['message']['content']
                    st.success("👨‍🍳 Рецепт готов!")
                    st.markdown(recipe_out)
                except Exception as e: st.error(f"Ошибка: {str(e)}")

# --- ВКЛАДКА 4: ГЕНЕРАЦИЯ МЕДИА (ФОТО И ВИДЕО) ---
with tab4:
    st.markdown("### 🎨 Создание графики и анимаций по фото/тексту")
    media_prompt = st.text_input("Опишите сцену для графики (на русском):", placeholder="Пример: Космическая станция будущего...")
    media_type = st.radio("Что сгенерировать?", ["Высокоточное Фото (FLUX)", "Анимация (Короткое видео)"])
    uploaded_image = st.file_uploader("Для анимации фото (опционально) - загрузите картинку:", type=["png", "jpg", "jpeg"])
    
    if st.button("🎨 Начать визуализацию", type="primary", use_container_width=True):
        if not media_prompt.strip() and not uploaded_image: st.warning("⚠️ Укажите описание или загрузите картинку.")
        else:
            with st.spinner("🚀 Графический процессор ИИ генерирует пиксели..."):
                try:
                    enhanced_desc = enhance_and_translate(media_prompt, mode="image")
                    seed = random.randint(1, 999999)
                    
                    if media_type == "Высокоточное Фото (FLUX)":
                        media_url = f"https://pollinations.ai{urllib.parse.quote_plus(enhanced_desc)}?width=768&height=432&seed={seed}&model=flux&nologo=true"
                    else:
                        media_url = f"https://pollinations.ai{urllib.parse.quote_plus(enhanced_desc + ', animated gif loop')}?width=512&height=512&seed={seed}&nologo=true"
                        
                    res = requests.get(media_url)
                    if res.status_code == 200:
                        st.success("🎉 Визуализация завершена!")
                        st.image(res.content, caption="Итоговый результат")
                        st.download_button("📥 Скачать файл", res.content, file_name="ai_output.png", mime="image/png", use_container_width=True)
                    else: st.error("Ошибка графического кластера.")
                except Exception as e: st.error(f"Ошибка медиа: {str(e)}")

# --- ВКЛАДКА 5: ПОИСК В ИНТЕРНЕТЕ ---
with tab4: # Назначена на 5-ю по логике
    pass 
# Исправлено распределение вкладок:
with tab5:
    st.markdown("### 🌐 Живой ИИ-Поиск в Интернете (Без ограничений и API-ключей)")
    search_query = st.text_input("Введите поисковый запрос (ИИ найдет свежие данные в сети и сделает выжимку):")
    
