import streamlit as st
from groq import Groq
import requests
import random
import urllib.parse
import time
import io
import re
from PIL import Image

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
# =====================================================================
# РЕКЛАМА: вставьте свой HTML сюда или добавьте в Secrets ключ AD_CODE
# =====================================================================
AD_CODE = """
<div style="text-align:center; padding:12px; border:2px dashed #f0c36d; border-radius:12px; background:#fffbe8;">
  <span style="font-size:1.05rem;">📢 <b>Здесь может быть ваша реклама</b></span><br>
  <span style="color:#999; font-size:0.85rem;">Отредактируйте переменную AD_CODE в коде приложения</span>
</div>
"""
if "AD_CODE" in st.secrets:
    AD_CODE = st.secrets["AD_CODE"]

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
    /* Фон приложения — мягкий градиент */
    .stApp {
        background: linear-gradient(120deg, #fdfbfb 0%, #f5f7fa 50%, #eef1f5 100%);
    }
    /* Заголовок с градиентом */
    .main-title {
        font-size: 3rem !important;
        font-weight: 900;
        background: linear-gradient(90deg, #FF4B4B, #FF8585, #ffa07a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        letter-spacing: -1px;
    }
    .sub-title {
        color: #6c7a80;
        font-size: 1.15rem;
        margin-bottom: 1.5rem;
    }
    /* Карточки */
    .sidebar-card, .ad-card {
        padding: 15px;
        background-color: #ffffff;
        border-radius: 12px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    /* Кнопки — градиентные, с тенью и эффектом при наведении */
    .stButton > button {
        background: linear-gradient(90deg, #FF4B4B, #FF7070) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(255,75,75,0.35) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(255,75,75,0.45) !important;
    }
    /* Вкладки — акцентный цвет */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #FF4B4B !important;
    }
    .stTabs [aria-selected="true"] {
        color: #FF4B4B !important;
        font-weight: 700 !important;
    }
    /* Рекламный баннер */
    .ad-banner {
        margin: 1rem 0;
        padding: 14px;
        border: 2px dashed #f0c36d;
        border-radius: 14px;
        background: #fffbe8;
        text-align: center;
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
    """Переводит русский промпт в короткий английский. Пробует несколько моделей, в конце — исходный текст."""
    system_role = (
        "You are a prompt translator. Translate the user input into a short, concise English image prompt. "
        "CRITICAL: The prompt must be VERY SHORT (MAXIMUM 15 WORDS). Just output key objects separated by commas. "
        "DO NOT include any URLs, website names, or domains in your response. "
        "Output ONLY the final English words, no quotes, no explanations."
    )
    for model in ("openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.1,
                max_tokens=40
            )
            result = get_content(response).replace("*", "").replace("#", "")
            if result:
                return result.replace('"', "").replace("'", "")
        except Exception:
            continue
    # Если все модели недоступны — используем исходный текст (Pollinations понимает русский)
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

def make_gif_from_image(img_bytes, frames=24, max_zoom=1.2):
    """Создаёт плавный зум (Ken Burns) из одного фото -> анимированный GIF."""
    base = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = base.size
    gif_frames = []
    for i in range(frames):
        t = i / (frames - 1)
        scale = 1 + (max_zoom - 1) * t
        nw, nh = max(1, int(w / scale)), max(1, int(h / scale))
        x = int((w - nw) * t / 2)
        y = int((h - nh) * t / 2)
        frame = base.crop((x, y, x + nw, y + nh)).resize((w, h), Image.LANCZOS)
        gif_frames.append(frame)
    buf = io.BytesIO()
    gif_frames[0].save(buf, format="GIF", save_all=True, append_images=gif_frames[1:], duration=90, loop=0)
    return buf.getvalue()

def generate_animation_gif(media_prompt):
    """Бесплатная анимация: 1 фото по запросу -> плавный зум -> GIF. Возвращает (bytes, описание)."""
    raw_desc = enhance_and_translate(media_prompt)
    cleaned = raw_desc.replace("pollinations", "").strip()
    seed = random.randint(1, 999999)
    encoded = urllib.parse.quote_plus(f"{cleaned}, cinematic scene")
    params = {"width": 512, "height": 512, "seed": seed, "model": "flux", "nologo": "true"}
    url = f"{POLLINATIONS_BASE}/image/{encoded}"
    res = requests.get(url, params=params, headers=_auth_headers(), timeout=120)
    res.raise_for_status()
    return make_gif_from_image(res.content), cleaned


class NeedPollinationsKey(Exception):
    """Видео требует бесплатный ключ Pollinations."""
    pass

class NoPollenError(Exception):
    """На аккаунте нет Pollen для оплаты видео."""
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
    if res.status_code == 402:
        raise NoPollenError
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

def clean_md(text):
    """Убирает markdown-разметку, эмодзи-модификаторы (U+FE0F, U+20E3) из строки."""
    for ch in ("**", "__", "`"):
        text = text.replace(ch, "")
    return text.replace("\uFE0F", "").replace("\u20E3", "").strip()

def extract_steps(recipe_text):
    """Извлекает шаги приготовления: 'N.', 'N)', 'Шаг N:', эмодзи-цифры (1️⃣). Ингредиенты пропускает."""
    steps = []
    # признак строки-ингредиента: '— 500 г', '— 2 ст. л.' и т.п.
    ingredient_re = re.compile(r"\u2014\s*[\d\s/.]+\s*(?:г|гр|кг|мл|л|шт|щепот|ч\.?\s*л|ст\.?\s*л)\b", re.IGNORECASE)
    for line in recipe_text.splitlines():
        s = line.strip()
        if not s:
            continue
        # эмодзи-цифра ('1️⃣ текст') — пунктуация после номера не нужна
        emoji_num = bool(re.match(r"^[0-9][\uFE0F\u20E3]+", s))
        # нормализуем эмодзи-цифры: '1️⃣' / '1⃣' -> '1'
        s = re.sub(r"^([0-9])[\uFE0F\u20E3]+", r"\1", s)
        # нумерованные строки: 'N.', 'N)', 'Шаг N:' — точка обязательна, если не эмодзи-формат
        punct = r"[.):]" if not emoji_num else r"[.):]?"
        m = re.match(r"^(?:Шаг\s*)?(\d+)\s*" + punct + r"\s*(.+)", s, re.IGNORECASE)
        if not m:
            continue
        step = clean_md(m.group(2))
        if len(step) <= 5:
            continue
        low = step.lower()
        if low.startswith(("ингредиент", "приготовлен", "совет", "подач", "шаги")):
            continue
        if ingredient_re.search(step):
            continue
        steps.append(step)
    return steps

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
                        "Структура: сначала список ингредиентов (перед каждым — эмодзи), "
                        "затем нумерованный список шагов приготовления. "
                        "ВАЖНО: каждый шаг начинай с новой строки строго в формате '1. текст шага', '2. текст шага' и т.д. "
                        "Эмодзи ставь внутри текста шага, но НЕ перед его номером. Без markdown-заголовков внутри списка шагов."
                    )
                    res = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": sys_prompt}], temperature=0.5)
                    recipe_text = get_content(res)
                    st.success("👨‍🍳 Рецепт готов!")
                    st.markdown(recipe_text)

                    # Фото приготовления по шагам, в порядке следования
                    with_photos = st.checkbox("📸 Добавить фото приготовления по шагам", value=True, key="recipe_photos_cb")
                    steps = extract_steps(recipe_text)
                    if with_photos:
                        if not steps:
                            st.info("ℹ️ Нумерованные шаги не найдены — фото сгенерировать не удалось.")
                        else:
                            st.markdown("#### 📸 Приготовление по шагам")
                            for idx, step in enumerate(steps[:8], 1):
                                with st.spinner(f"📸 Генерирую фото шага {idx} из {min(len(steps), 8)}..."):
                                    try:
                                        img_bytes, _ = generate_image(f"{dish_name}: {step}, appetizing food photography")
                                        st.image(img_bytes, caption=f"Шаг {idx}: {step}", use_container_width=True)
                                    except Exception as ex:
                                        st.warning(f"⚠️ Не удалось сгенерировать фото шага {idx}: {ex}")
                                time.sleep(1)
                except Exception as e:
                    st.error(f"Ошибка: {e}")

def run_media_tab():
    st.markdown("### 🎨 Генерация фото и видео по тексту")
    st.caption("Фото и GIF-анимация — бесплатно. Видео MP4 платное (нужен Pollen на балансе): https://enter.pollinations.ai")
    media_prompt = st.text_input("Опишите сцену (на русском):", placeholder="Пример: Парень и девушка идут по лесу...", key="media_ti")
    media_type = st.radio(
        "Что сгенерировать?",
        ["Высокоточное Фото (FLUX)", "🎞️ Анимация GIF (бесплатно)", "🎬 Видео MP4 (платно, нужен Pollen)"],
        horizontal=True
    )

    if st.button("🎨 Начать генерацию", type="primary", use_container_width=True, key="gen_media_btn"):
        if not media_prompt.strip():
            st.warning("⚠️ Укажите описание сцены.")
        else:
            try:
                if media_type == "🎬 Видео MP4 (платно, нужен Pollen)":
                    with st.spinner("🎬 Генерация видео занимает 1–3 минуты, не закрывайте страницу..."):
                        content, info = generate_video(media_prompt)
                        st.session_state.generated_media = content
                        st.session_state.current_media_type = "video"
                elif media_type == "🎞️ Анимация GIF (бесплатно)":
                    with st.spinner(f"🎞️ Генерирую 6 кадров и собираю GIF (~1 минута)..."):
                        content, info = generate_animation_gif(media_prompt)
                        st.session_state.generated_media = content
                        st.session_state.current_media_type = "gif"
                else:
                    with st.spinner("🚀 Генерация фото..."):
                        content, info = generate_image(media_prompt)
                        st.session_state.generated_media = content
                        st.session_state.current_media_type = "image"
                st.session_state.meta_info = info
                st.rerun()
            except NoPollenError:
                st.error("💰 Генерация видео платная: на аккаунте Pollinations закончился Pollen.")
                st.info("Варианты:\n"
                        "1. Зайдите в кабинет **https://enter.pollinations.ai** → выполните квесты для бесплатного Quest Pollen (фото работают бесплатно).\n"
                        "2. Или пополните баланс (Top up).\n"
                        "3. Пока пользуйтесь генерацией фото — она работает без баланса.")
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
        elif st.session_state.current_media_type == "gif":
            st.image(st.session_state.generated_media, use_container_width=True)
            ext, mime = "gif", "image/gif"
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
    st.markdown(f'<div class="ad-banner">{AD_CODE}</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("#### ⚙️ Настройки ИИ (Groq)")
        st.markdown('<div class="sidebar-card">Модель и креативность для текстов и кода. Медиа генерируются отдельным бесплатным сервером.</div>', unsafe_allow_html=True)
        model_choice = st.selectbox(
            "Модель:",
            ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"],
            index=0
        )
        temperature = st.slider("Креативность (temperature):", 0.0, 1.0, 0.7, 0.1)
        st.divider()
        st.markdown(f'<div class="ad-card">{AD_CODE}</div>', unsafe_allow_html=True)
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

    st.markdown(f'<div class="ad-banner">{AD_CODE}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
