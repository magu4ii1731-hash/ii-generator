import streamlit as st
from groq import Groq

# 1. Настройка конфигурации страницы
st.set_page_config(
    page_title="Groq ИИ-Генератор",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Кастомные CSS-стили для интерфейса
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

# 3. Инициализация клиента Groq с проверкой безопасности
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ Ошибка: API-ключ 'GROQ_API_KEY' не найден в Secrets хостинга!")
    st.stop()

# Подключаем клиент Groq, используя секретный ключ
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. Боковая панель (Sidebar)
# 4. Боковая панель (Sidebar)
with st.sidebar:
    st.markdown("<div class='sidebar-card'><h3>⚙️ Настройки Groq ИИ</h3></div>", unsafe_allow_html=True)
    
    # Все строки ниже имеют ровно 4 пробела отступа от левого края
    model_choice = st.selectbox(
        "Выберите модель:",
        ("llama-3.3-70b-specdec", "llama3-70b-8192", "llama-3.1-8b-instant"),
        help="Модели 70b пишут код профессионально, а 8b работает максимально молниеносно."
    )
    
    temperature = st.slider(
        "Креативность (Temperature):",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.1,
        help="Для генерации точного и рабочего кода рекомендуется значение 0.1 - 0.2."
    )
    
    st.markdown("---")
    st.markdown("""
    ### 💡 Идеи для ТЗ:
    * *Скрипт на JS, который плавно прокручивает страницу до якоря при клике на меню.*
    * *Telegram-бот на aiogram v3, который присылает пользователю случайную цитату по кнопке.*
    * *Красивая HTML/CSS карточка товара с кнопкой 'Купить' и анимацией при наведении.*
    """)

    )

    )
    
    temperature = st.slider(
        "Креативность (Temperature):",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.1,
        help="Для генерации точного и рабочего кода рекомендуется значение 0.1 - 0.2."
    )
    
    st.markdown("---")
    st.markdown("""
    ### 💡 Идеи для ТЗ:
    * *Скрипт на JS, который плавно прокручивает страницу до якоря при клике на меню.*
    * *Telegram-бот на aiogram v3, который присылает пользователю случайную цитату по кнопке.*
    * *Красивая HTML/CSS карточка товара с кнопкой 'Купить' и анимацией при наведении.*
    """)

# 5. Главный экран
st.markdown("<h1 class='main-title'>⚡ Ultra-Fast ИИ-Генератор Скриптов</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Мгновенное создание кода без VPN ограничений на базе мощных Llama моделей от Meta</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🛠 Разработка кода", "ℹ️ Инструкция по запуску"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.radio(
            "Направление разработки:",
            (
                "🤖 Telegram-бот (Python)", 
                "🌐 Веб-скрипт (JavaScript)", 
                "🎨 Верстка страницы (HTML / CSS)", 
                "🐍 Автоматизация (Python-скрипт)"
            )
        )
        
    with col2:
        user_prompt = st.text_area(
            "Ваше техническое задание (ТЗ):",
            height=130,
            placeholder="Опишите детально, что должен делать скрипт... Например: Скрипт калькулятора кредита для сайта..."
        )

    generate_btn = st.button("🚀 Запустить генерацию кода", type="primary", use_container_width=True)

    # 6. Логика отправки запроса в Groq Cloud API
    if generate_btn:
        if not user_prompt.strip():
            st.warning("⚠️ Пожалуйста, заполните ТЗ.")
        else:
            with st.spinner("🧠 Нейросеть Llama анализирует задачу и строит алгоритм..."):
                try:
                    # Формируем системные требования разработчика
                    system_instruction = (
                        "Ты — ведущий fullstack-разработчик. Напиши идеальный, чистый и рабочий код. "
                        f"Категория задачи: {category}. Техническое задание: {user_prompt}. "
                        "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:\n"
                        "1. Код должен быть полностью готовым к запуску (без сокращений и заглушек типа '// тут ваш код').\n"
                        "2. Добавляй понятные комментарии на русском языке.\n"
                        "3. Если нужны внешние библиотеки, напиши команду для их установки в первой строчке в комментариях.\n"
                        "4. Выдавай код в формате Markdown-блока с указанием языка."
                    )
                    
                    # Запрос к API Groq
                    completion = client.chat.completions.create(
                        model=model_choice,
                        messages=[
                            {"role": "user", "content": system_instruction}
                        ],
                        temperature=temperature,
                        max_tokens=4096
                    )
                    
                    # Извлечение текста ответа
                    generated_code = completion.choices[0].message.content
                    
                    st.success("🎉 Код успешно сгенерирован за доли секунды!")
                    
                    # Определение подсветки синтаксиса
                    lang = "python" if "Python" in category or "бот" in category.lower() else "javascript"
                    
                    st.markdown("### 📋 Сгенерированный код:")
                    st.code(generated_code, language=lang)
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Произошла ошибка API: {str(e)}")
                    st.info("Проверьте правильность добавления GROQ_API_KEY в разделы настроек.")

with tab2:
    st.markdown("""
    ### 🚀 Как запустить ваш готовый скрипт?
    
    * **Если вы сгенерировали HTML/CSS/JS сайт:**
      Создайте на компьютере текстовый файл, назовите его `index.html`, откройте его через обычный Блокнот и вставьте туда код. Сохраните и просто откройте этот файл любым веб-браузером.
    * **Если вы создали Telegram-бота или Python-скрипт:**
      Установите Python, откройте консоль (терминал), выполните команду установки зависимостей (например, `pip install aiogram`), сохраните код в файл `main.py` и запустите его командой: `python main.py`.
    """)
