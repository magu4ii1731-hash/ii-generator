import streamlit as st
from groq import Groq
import requests
import random

# 1. Настройка конфигурации страницы
st.set_page_config(
    page_title="ИИ-Генератор Кода и Видео",
    page_icon="⚡",
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

# 3. Инициализация API-ключей с проверкой безопасности
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ Ошибка: API-ключ 'GROQ_API_KEY' не найден в Secrets хостинга!")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. Боковая панель (Sidebar)
with st.sidebar:
    st.markdown("<div class='sidebar-card'><h3>⚙️ Настройки ИИ</h3></div>", unsafe_allow_html=True)
    
    model_choice = st.selectbox(
        "Модель для текста/кода:",
        ("qwen/qwen3.8-27b", "openai/gpt-oss-120b"),
        help="Актуальные модели для генерации логики и скриптов."
    )
    
    temperature = st.slider(
        "Креативность текста:",
        min_value=0.0, max_value=1.0, value=0.2, step=0.1
    )
    
    st.markdown("---")
    st.markdown("""
    ### 🎥 Видео-кластер:
    Переключено на децентрализованную сеть Pollinations API. Ошибки авторизации 403 полностью устранены.
    """)

# 5. Главный экран
st.markdown("<h1 class='main-title'>⚡ Мульти-Генератор: Код & Видео</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Создавайте работающие скрипты или анимации в один клик без вложений и блокировок</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🛠 Разработка кода", "🎥 Генерация видео", "ℹ️ Инструкция"])

# --- ВКЛАДКА 1: ГЕНЕРАЦИЯ КОДА ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        category = st.radio(
            "Направление разработки:",
            ("🤖 Telegram-бот (Python)", "🌐 Веб-скрипт (JavaScript)", "🎨 Верстка страницы (HTML / CSS)", "🐍 Автоматизация (Python)")
        )
    with col2:
        user_prompt = st.text_area(
            "Ваше technical задание (ТЗ):",
            height=130,
            placeholder="Опишите детально, что должен делать скрипт..."
        )

    generate_btn = st.button("🚀 Запустить генерацию кода", type="primary", use_container_width=True)

    if generate_btn:
        if not user_prompt.strip():
            st.warning("⚠️ Пожалуйста, заполните ТЗ.")
        else:
            with st.spinner("🧠 Нейросеть анализирует задачу и строит алгоритм..."):
                try:
                    system_instruction = (
                        "Ты — ведущий fullstack-разработчик. Напиши идеальный, чистый и рабочий код. "
                        f"Категория задачи: {category}. Техническое задание: {user_prompt}. "
                        "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:\n"
                        "1. Код должен быть полностью готовым к запуску без сокращений.\n"
                        "2. Добавляй комментарии на русском языке.\n"
                        "3. Форматируй код корректно."
                    )
                    
                    completion = client.chat.completions.create(
                        model=model_choice,
                        messages=[{"role": "user", "content": system_instruction}],
                        temperature=temperature,
                        max_tokens=4096
                    )
                    
                    if hasattr(completion, 'choices') and len(completion.choices) > 0:
                        choice = completion.choices
                        if hasattr(choice, 'message'):
                            generated_code = choice.message.content
                        else:
                            generated_code = choice['message']['content']
                    else:
                        generated_code = completion['choices']['message']['content']
                    
                    st.success("🎉 Код успешно сгенерирован!")
                    lang = "python" if "Python" in category or "бот" in category.lower() else "javascript"
                    st.code(generated_code, language=lang)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Произошла ошибка API при создании кода: {str(e)}")

# --- ВКЛАДКА 2: ГЕНЕРАЦИЯ ВИДЕО ---
with tab2:
    st.markdown("### 🎬 Создание анимации по текстовому описанию")
    video_prompt = st.text_input(
        "Опишите, что должно происходить на сцене (пишите на английском):",
        placeholder="Example: Cyberpunk programmer working late night, glowing matrix code on background, lofi style, animated"
    )
    
    # Дополнительные настройки для видео-анимации
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        motion_style = st.selectbox("Стиль анимации:", ["Cinematic", "Anime", "3D Render", "Digital Art", "Cyberpunk"])
    with col_v2:
        aspect_ratio = st.selectbox("Соотношение сторон:", ["16:9 (Горизонтальное)", "9:16 (Вертикальное / Shorts)", "1:1 (Квадратное)"])

    video_btn = st.button("🎬 Сгенерировать медиа", type="primary", use_container_width=True)
    
    if video_btn:
        if not video_prompt.strip():
            st.warning("⚠️ Пожалуйста, введите описание сцены.")
        else:
            with st.spinner("🚀 Отправка на публичный медиа-сервер... Генерация занимает до 10-15 секунд."):
                try:
                    # Корректируем размеры под выбор соотношения сторон
                    width, height = 512, 512
                    if "16:9" in aspect_ratio:
                        width, height = 768, 432
                    elif "9:16" in aspect_ratio:
                        width, height = 432, 768
                        
                    # Собираем промпт и очищаем от пробелов
                    full_prompt = f"{video_prompt}, {motion_style} style, animated gif masterpiece"
                    encoded_prompt = requests.utils.quote(full_prompt)
                    seed = random.randint(1, 999999)
                    
                    # Запрос к высокоскоростному безопасному кластеру Pollinations
                    media_url = f"https://pollinations.ai{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"
                    
                    response = requests.get(media_url)
                    
                    if response.status_code == 200 and response.content:
                        st.success("🎉 ИИ-сцена успешно сгенерирована!")
                        
                        # Выводим анимацию/изображение
                        st.image(response.content, caption=f"Ваш запрос: {video_prompt}")
                        
                        # Кнопка скачивания файла без каких-либо лимитов
                        st.download_button(
                            label="📥 Скачать готовую сцену (.png/gif)",
                            data=response.content,
                            file_name="generated_scene.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    else:
                        st.error(f"Сервер временно не отвечает. Код ответа: {response.status_code}. Пожалуйста, попробуйте еще раз.")
                            
                except Exception as video_err:
                    st.error(f"Ошибка при обработке медиафайла: {str(video_err)}")

# --- ВКЛАДКА 3: ИНСТРУКЦИЯ ---
with tab3:
    st.markdown("""
    ### 🚀 Руководство пользователя
    1. **Вкладка кода:** выберите язык программирования, введите ТЗ на русском языке и нажмите генерацию. Код пишется без сокращений.
    2. **Вкладка видео:** введите детализированную сцену на английском языке, выберите пропорции (например, 9:16 для мобильных Shorts) и запустите рендеринг. Скачивание доступно сразу по кнопке.
    """)

    
