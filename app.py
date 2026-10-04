import streamlit as st
from groq import Groq
import requests
import random
import urllib.parse
import time

# =====================================================================
# 1. КОНФИГУРАЦИЯ СТРАНИЦЫ
# =====================================================================
st.set_page_config(
    page_title="ИИ-Комбайн: Текст, Код, Медиа & Поиск",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния сессии
if "generated_media" not in st.session_state:
    st.session_state.generated_media = None      # байты файла
if "meta_info" not in st.session_state:
    st.session_state.meta_info = ""
if "current_media_type" not in st.session_state:
    st.session_state.current_media_type = ""

# Проверка API-ключа Groq (бесплатный ключ: https://console.groq.com/keys)
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ Добавьте ключ 'GROQ_API_KEY' в Secrets хостинга (Streamlit Cloud → Settings → Secrets). "
             "Бесплатный ключ: https://console.groq.com/keys")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Опциональный ключ Pollinations (фото/видео). Бесплатно: https://enter.pollinations.ai
# В Secrets: POLLINATIONS_API_KEY = "ваш_ключ"
POLLINATIONS_KEY = st.secrets.get("POLLINATIONS_API_KEY", "")

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

# =====================================================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =====================================================================
def get_content(response):
    """Безопасно извлекает текст ответа Groq API."""
    return response.choices[0].message.content.strip()

def enhance_and_translate(user_text):
    """Переводит русский промпт в короткий английский для генерации медиа."""
    try:
        system_role = (
            "You are a prompt translator. Translate the user input into a short, concise English image prompt. "
            "CRITICAL: The prompt must be VERY SHORT (MAXIMUM 15 WORDS). Just output key objects separated by commas. "
            "DO NOT include any URLs, website names, or domains in your response. "
            "Output ONLY the final English words, no quotes, no explanations."
        )
        response = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1,
            max_tokens=40
        )
        result = get_content(response)
        return result.replace('"', "").replace("'", "")
    except Exception:
        # Если перевод не удался — используем исходный текст (Pollinations понимает русский)
        return user_text

POLLINATIONS_BASE = "https://gen.pollinations.ai"

def _auth_headers():
    """Pollinations требует ключ через заголовок Authorization: Bearer, НЕ через ?token= в URL."""
    return {"Authorization": f"Bearer {POLLINATIONS_KEY}"} if POLLINATIONS_KEY else {}

def generate_image(media_prompt):
    """Генерация фото через Pollinations (FLUX). Возвращает (bytes, описание)."""
    raw_desc = enhance_and_translate(media_prompt)
    cleaned = raw_desc.replace("pollinations", "").strip()
    seed = random.randint(1, 999999)
    full_prompt = f"{cleaned}, high quality photography"
    encoded = urllib.parse.quote_plus(full_prompt)
    params = {"width": 768, "height": 432, "seed": seed, "model": "flux", "nologo": "true"}
    url = f"{POLLINATIONS_BASE}/image/{encoded}"
    res = requests.get(url, params=params, headers=_auth_headers(), timeout=120)
    res.raise_for_status()
    return res.content, cleaned

class NeedPollinationsKey(Exception):
    """Видео требует бесплатный ключ Pollinations."""
    pass

def generate_video(media_prompt):
    """Генерация видео (MP4) через Pollinations. Возвращает (bytes, описание)."""
    if not POLLINATIONS_KEY:
        raise NeedPollinationsKey
    raw_desc = enhance_and_translate(media_prompt)
    cleaned = raw_desc.replace("pollinations", "").strip()
    seed = random.randint(1, 999999)
    full_prompt = f"{cleaned}, cinematic smooth motion"
    encoded = urllib.parse.quote_plus(full_prompt)
    params = {"width": 512, "height": 512, "seed": seed, "nologo": "true"}
    url = f"{POLLINATIONS_BASE}/video/{encoded}"

    res = requests.get(url, params=params, headers=_auth_headers(), timeout=300)
    if res.status_code == 401:
        raise NeedPollinationsKey
    res.raise_for_status()
    content_type = res.headers.get("Content-Type", "")

    if "video" in content_type or res.content[:4] == b"\x00\x00\x00":
        return res.content, cleaned

    # Если вернулся JSON — там ссылка на готовый ролик или статус
    try:
        data = res.json()
        video_url = data.get("url") or data.get("video_url") or data.get("output")
        if video_url:
            for _ in range(40):  # ждём до ~3 минут
                time.sleep(5)
                poll = requests.get(video_url, timeout=60)
                if poll.status_code == 200 and len(poll.content) > 10000:
                    return poll.content, cleaned
        raise ValueError(f"Сервер не вернул видео: {data}")
    except Exception:
        raise

# =====================================================================
# 3. ВКЛАДКИ ПРИЛОЖЕНИЯ
# =====================================================================
def run_coding_tab(model_choice, temperature):
    st.markdown("### 🤖 Создание скриптов и чат-ботов")
    col1, col2 = st.columns(2)
    with col1:
        category = st.radio("Направление:", ("🤖 Telegram-бот (Python)", "🌐 Веб-скрипт (JavaScript)", "🎨 Верстка (HTML/CSS)", "🐍 Автоматизация (Python)"))
    with col2:
        user_prompt = st.text_area("Техническое задание (ТЗ) для кода:", height=130, placeholder="Например: Скрипт калькулятора кредита...", key="code_ta")

    if st.button("🚀 Сгенерировать код", type="primary", use_container_width=True, key="gen_code_btn"):
        if not user_prompt.strip():
            st.warning("⚠️ Введите ТЗ.")
        else:
            with st.spinner("🧠 ИИ пишет чистый код..."):
                try:
                    if "Python" in category or "бот" in category:
                        lang = "python"
                    elif "JavaScript" in category:
                        lang = "javascript"
                    else:
                        lang = "html"
                    sys_prompt = f"Ты Senior разработчик. Напиши чистый, рабочий код для '{category}' по ТЗ: {user_prompt}. Добавь комментарии."
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=temperature)
                    st.success("🎉 Код успешно сгенерирован!")
                    st.code(get_content(res), language=lang)
                except Exception as e:
                    st.error(f"Ошибка API: {e}")

def run_text_tab(model_choice):
    st.markdown("### 📝 Генератор статей и описаний для видео")
    text_mode = st.selectbox("Что нужно сгенерировать?", ["Полноценная статья/Пост", "SEO-описание для Видео (YouTube/Reels)", "Продающий текст"])
    text_topic = st.text_input("Укажите тему или ключевые слова:", key="text_ti")
    text_length = st.select_slider("Желаемый объем текста:", options=["Короткий", "Средний", "Развернутый лонгрид"])

    if st.button("📝 Создать текст", type="primary", use_container_width=True, key="gen_text_btn"):
        if not text_topic.strip():
            st.warning("⚠️ Введите тему текста.")
        else:
            with st.spinner("✍️ Писатель ИИ формулирует структуру и пишет текст..."):
                try:
                    sys_prompt = f"Ты профессиональный копирайтер. Напиши '{text_mode}' на тему: '{text_topic}'. Объем текста: {text_length}. Текст должен быть структурированным, интересным и грамотным."
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=0.7)
                    st.success("🎉 Текст успешно написан!")
                    st.markdown(get_content(res))
                except Exception as e:
                    st.error(f"Ошибка: {e}")

def run_recipes_tab(model_choice):
    st.markdown("### 🍳 ИИ-Шеф: Рецепты с эмодзи")
    dish_name = st.text_input("Введите название блюда или доступные ингредиенты:", placeholder="Пример: Паста Карбонара или Курица, картошка, грибы", key="dish_ti")
    diet_pref = st.multiselect("Особые предпочтения (необязательно):", ["Без глютена", "Вегетарианское", "ПП / Низкокалорийное", "Быстро (до 20 мин)"])

    if st.button("🍳 Сформировать рецепт", type="primary", use_container_width=True, key="gen_recipe_btn"):
        if not dish_name.strip():
            st.warning("⚠️ Введите название блюда.")
        else:
            with st.spinner("👩‍🍳 Шеф-повар ИИ составляет рецепт..."):
                try:
                    restrictions = ", ".join(diet_pref) if diet_pref else "нет"
                    sys_prompt = (
                        f"Ты профессиональный ИИ-шеф. Создай подробный кулинарный рецепт на основе запроса: '{dish_name}'. "
                        f"Учти ограничения: {restrictions}. "
                        "ОБЯЗАТЕЛЬНО: добавляй подходящую эмодзи-иконку перед КАЖДЫМ ингредиентом и перед КАЖДЫМ шагом приготовления."
                    )
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=0.5)
                    st.success("👨‍🍳 Рецепт готов!")
                    st.markdown(get_content(res))
                except Exception as e:
                    st.error(f"Ошибка: {e}")

def run_media_tab():
    st.markdown("### 🎨 Генерация фото и видео по тексту")
    st.caption("Фото — без ключа. Видео требует бесплатный ключ Pollinations (https://enter.pollinations.ai) → добавьте его в Secrets как POLLINATIONS_API_KEY.")
    media_prompt = st.text_input("Опишите сцену (на русском):", placeholder="Пример: Парень и девушка идут по лесу...", key="media_ti")
    media_type = st.radio("Что сгенерировать?", ["Высокоточное Фото (FLUX)", "🎬 Видео (MP4)"], horizontal=True)

    if st.button("🎨 Начать генерацию", type="primary", use_container_width=True, key="gen_media_btn"):
        if not media_prompt.strip():
            st.warning("⚠️ Укажите описание сцены.")
        else:
            try:
                if media_type == "🎬 Видео (MP4)":
                    with st.spinner("🎬 Генерация видео занимает 1–3 минуты, не закрывайте страницу..."):
                        content, info = generate_video(media_prompt)
                        st.session_state.generated_media = content
                        st.session_state.current_media_type = "video"
                else:
                    with st.spinner("🚀 Генерация фото..."):
                        content, info = generate_image(media_prompt)
                        st.session_state.generated_media = content
                        st.session_state.current_media_type = "image"
                st.session_state.meta_info = info
                st.rerun()
            except NeedPollinationsKey:
                st.error("🔑 Для генерации видео нужен бесплатный ключ Pollinations.")
                st.info("1. Зайдите на **https://enter.pollinations.ai** → регистрация за минуту.\n"
                        "2. Скопируйте API-ключ.\n"
                        "3. В Streamlit Cloud: **Settings → Secrets** добавьте строку:\n"
                        "`POLLINATIONS_API_KEY = \"ваш_ключ\"`")
            except Exception as e:
                st.error(f"Графический сервер не ответил: {e}")

    # Отображение результата
    if st.session_state.generated_media:
        st.divider()
        st.markdown("#### 🖼️ Результат генерации")
        if st.session_state.current_media_type == "video":
            st.video(st.session_state.generated_media)
            ext, mime = "mp4", "video/mp4"
        else:
            st.image(st.session_state.generated_media, use_container_width=True)
            ext, mime = "png", "image/png"
        st.caption(f"🎨 Промпт: {st.session_state.meta_info}")
        st.download_button(
            label="💾 Скачать файл",
            data=st.session_state.generated_media,
            file_name=f"generated_{random.randint(1000, 9999)}.{ext}",
            mime=mime,
            key="dl_btn"
        )

# =====================================================================
# 4. ГЛАВНЫЙ ИНТЕРФЕЙС
# =====================================================================
def main():
    st.markdown('<div class="main-title">🧠 ИИ-Комбайн</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Тексты, код, рецепты, фото и видео — всё в одном приложении</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("#### ⚙️ Настройки ИИ (Groq)")
        st.markdown('<div class="sidebar-card">Модель и креативность для текстов и кода. Медиа генерируются отдельным бесплатным сервером.</div>', unsafe_allow_html=True)
        model_choice = st.selectbox(
            "Модель:",
            ["llama-3.3-70b-versatile", "qwen/qwen3-32b", "openai/gpt-oss-120b"],
            index=0
        )
        temperature = st.slider("Креативность (temperature):", 0.0, 1.0, 0.7, 0.1)
        st.divider()
        st.caption("🔑 GROQ_API_KEY — в Secrets хостинга.")

    tab_text, tab_code, tab_recipes, tab_media = st.tabs(["📝 Тексты", "🤖 Код", "🍳 Рецепты", "🎨 Фото/Видео"])

    with tab_text:
        run_text_tab(model_choice)
    with tab_code:
        run_coding_tab(model_choice, temperature)
    with tab_recipes:
        run_recipes_tab(model_choice)
    with tab_media:
        run_media_tab()

if __name__ == "__main__":
    main()
