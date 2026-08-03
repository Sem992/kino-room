import streamlit as st
import json
import os
import random
import requests
import textwrap

# 1. Настройка страницы
st.set_page_config(
    page_title="Кино Room",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 🔑 НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К SUPABASE
# =========================================================
SUPABASE_URL = "https://cmlxeafxjgjsaotzkwbn.supabase.co"
SUPABASE_KEY = "sb_publishable_cS46YQuO8d64KEQlS2PnHg__qFLdFcb"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

POPULAR_GENRES = [
    "Комедия", "Драма", "Фантастика", "Боевик", "Триллер",
    "Ужасы", "Мелодрама", "Анимация", "Приключения", "Фэнтези"
]


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ SUPABASE (С КЭШИРОВАНИЕМ) ---

@st.cache_data(ttl=5)
def load_local_movies():
    try:
        url = f"{SUPABASE_URL}/rest/v1/movies?select=*&order=id.asc"
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=5)
def load_local_reviews():
    try:
        url = f"{SUPABASE_URL}/rest/v1/reviews?select=*"
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=5)
def load_local_actions():
    try:
        url = f"{SUPABASE_URL}/rest/v1/user_actions?select=*"
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=5)
def load_local_quizzes():
    try:
        url = f"{SUPABASE_URL}/rest/v1/quizzes?select=*"
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=5)
def load_local_quiz_results():
    try:
        url = f"{SUPABASE_URL}/rest/v1/quiz_results?select=*"
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=5)
def load_local_requests():
    try:
        url = f"{SUPABASE_URL}/rest/v1/requests?select=*"
        response = requests.get(url, headers=HEADERS)
        return response.json() if response.status_code == 200 else []
    except:
        return []


def save_local_movie(movie_data):
    try:
        url = f"{SUPABASE_URL}/rest/v1/movies"
        payload = {
            "title": movie_data.get("title"),
            "category": movie_data.get("category"),
            "genre": movie_data.get("genre", ""),
            "folder": movie_data.get("folder", ""),
            "poster_url": movie_data.get("poster_url"),
            "trailer_url": movie_data.get("trailer_url"),
            "description": movie_data.get("description"),
            "recommended": movie_data.get("recommended", False),
            "for_kristina": movie_data.get("for_kristina", False)
        }
        requests.post(url, headers=HEADERS, json=payload)
        st.cache_data.clear()
    except:
        pass


def save_local_review(review_data):
    try:
        movie_id = review_data.get("movie_id")
        username = review_data.get("username")

        del_url = f"{SUPABASE_URL}/rest/v1/reviews?username=eq.{username}&movie_id=eq.{movie_id}"
        requests.delete(del_url, headers=HEADERS)

        url = f"{SUPABASE_URL}/rest/v1/reviews"
        payload = {
            "movie_id": movie_id,
            "username": username,
            "rating": int(review_data.get("rating")),
            "vibe": review_data.get("vibe"),
            "review_text": review_data.get("review_text")
        }
        requests.post(url, headers=HEADERS, json=payload)
        st.cache_data.clear()
    except:
        pass


def save_local_action(username, movie_id, status):
    try:
        delete_url = f"{SUPABASE_URL}/rest/v1/user_actions?username=eq.{username}&movie_id=eq.{movie_id}"
        requests.delete(delete_url, headers=HEADERS)

        if status:
            insert_url = f"{SUPABASE_URL}/rest/v1/user_actions"
            payload = {
                "username": username,
                "movie_id": movie_id,
                "status": status
            }
            requests.post(insert_url, headers=HEADERS, json=payload)
        st.cache_data.clear()
    except:
        pass


# --- ИНИЦИАЛИЗАЦИЯ СЕССИИ И НАВИГАЦИИ ---
if "user_role" not in st.session_state: st.session_state.user_role = None
if "login_target" not in st.session_state: st.session_state.login_target = None
if "nav_page" not in st.session_state: st.session_state.nav_page = "catalog"
if "random_movie" not in st.session_state: st.session_state.random_movie = None

# Синхронизация URL и состояния
if "movie_id" in st.query_params:
    st.session_state.selected_movie_id = st.query_params["movie_id"]
    st.session_state.current_page = "movie_view"
else:
    st.session_state.selected_movie_id = None
    st.session_state.current_page = st.session_state.nav_page

# 2. Кастомный CSS стиль
st.html("""
    <style>
    .stApp { background-color: #FAFAFA; color: #2B2B2B; }
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }

    /* Перевод плейсхолдера multiselect на русский */
    div[data-baseweb="select"] span[data-class="placeholder"] {
        font-size: 0 !important;
    }
    div[data-baseweb="select"] span[data-class="placeholder"]::after {
        content: "Выберите варианты..." !important;
        font-size: 14px !important;
        color: #757575 !important;
    }

    /* Кнопки */
    div.stButton > button {
        background-color: #E50914 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 900 !important;
        font-size: 14px !important;
        transition: 0.2s !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button p { color: #FFFFFF !important; font-weight: 900 !important; }
    div.stButton > button:hover {
        background-color: #B80710 !important;
        box-shadow: 0px 4px 10px rgba(229, 9, 20, 0.4) !important;
        transform: translateY(-1px);
    }

    .stSlider [data-baseweb="slider"] { background-color: #E50914 !important; }
    div[data-testid="stSlider"] [data-baseweb="typography"], 
    div[data-testid="stSlider"] span, 
    div[data-testid="stSlider"] div {
        color: #111111 !important; font-size: 16px !important; font-weight: 800 !important;
    }

    h1, h2, h3, h4 { color: #2B2B2B !important; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 700 !important; }

    /* Карточка фильма */
    .movie-card {
        background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px;
        padding: 15px; text-align: center; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05); transition: 0.3s;
        margin-bottom: 10px; position: relative;
    }
    .movie-card:hover {
        border-color: #E50914; box-shadow: 0px 6px 15px rgba(229, 9, 20, 0.15); transform: translateY(-2px);
    }
    .movie-card img {
        width: 100%;
        height: 260px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 8px;
    }

    .review-box {
        background-color: #FFFFFF; border-left: 5px solid #E50914; padding: 12px; border-radius: 4px; margin-bottom: 10px;
    }
    .stats-box-new {
        background-color: #FFFFFF; border: 1px solid #E0E0E0; border-left: 5px solid #E50914;
        padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .quiz-single-box {
        background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; padding: 15px; margin-bottom: 15px;
    }

    .achievement-card {
        background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 10px; padding: 15px; margin-bottom: 12px; box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
    }
    .achievement-card.earned {
        border: 1px solid #28A745; background-color: #F4FBF6;
    }
    </style>
""")

# ==========================================
# 🔐 ЭКРАН ВХОДА
# ==========================================
if st.session_state.user_role is None:
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.write("")
        st.html("<h1 style='text-align: center;'>🎬 Кино Room</h1>")
        st.html("<p style='text-align: center; color: #666; font-size: 16px;'>Добро пожаловать. Кто заходит?</p>")
        st.write("---")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🕶 Семён (Админ)", use_container_width=True):
                st.session_state.login_target = "Семён"
                st.rerun()
        with btn_col2:
            if st.button("🍿 Кристина", use_container_width=True):
                st.session_state.user_role = "Кристина"
                st.rerun()

        if st.session_state.login_target == "Семён":
            st.write("---")
            password = st.text_input("Введите секретный пароль:", type="password")
            if st.button("Войти как Администратор"):
                if password == "0105":
                    st.session_state.user_role = "Семён"
                    st.success("Доступ разрешен!")
                    st.rerun()
                else:
                    st.error("Неверный пароль!")

# ==========================================
# 🍿 ГЛАВНЫЙ ИНТЕРФЕЙС
# ==========================================
if st.session_state.user_role is not None:
    movies_list = load_local_movies()
    actions_list = load_local_actions()
    quizzes_list = load_local_quizzes()
    quiz_results = load_local_quiz_results()
    requests_list = load_local_requests()
    reviews_list = load_local_reviews()

    total_movies = len(movies_list)
    user_watched_ids = [str(a["movie_id"]) for a in actions_list if
                        a["username"] == st.session_state.user_role and a["status"] == "watched"]
    user_watched = len(user_watched_ids)
    user_watchlist_ids = [str(a["movie_id"]) for a in actions_list if
                          a["username"] == st.session_state.user_role and a["status"] == "watchlist"]
    user_watchlist = len(user_watchlist_ids)


    def render_movie_grid(movie_collection):
        if not movie_collection:
            st.info("В этой категории или по выбранным фильтрам пока ничего нет.")
            return

        chunks = [movie_collection[i:i + 3] for i in range(0, len(movie_collection), 3)]
        for chunk in chunks:
            cols = st.columns(3)
            for index, movie in enumerate(chunk):
                with cols[index]:
                    semen_status = next((a["status"] for a in actions_list if
                                         a["username"] == "Семён" and str(a["movie_id"]) == str(movie["id"])), None)
                    kristina_status = next((a["status"] for a in actions_list if
                                            a["username"] == "Кристина" and str(a["movie_id"]) == str(movie["id"])),
                                           None)

                    badges_html = "<div style='margin-top:6px; margin-bottom:6px; text-align:center;'>"
                    if semen_status == "watched":
                        badges_html += "<span style='background-color:#28A745; color:white; padding:2px 6px; border-radius:4px; font-size:11px; margin-right:3px;'>🕶 Сёма ✅</span>"
                    if kristina_status == "watched":
                        badges_html += "<span style='background-color:#E50914; color:white; padding:2px 6px; border-radius:4px; font-size:11px;'>🍿 Кристина ✅</span>"
                    badges_html += "</div>"

                    genre_str = movie.get("genre", "")
                    genre_badge = f"<div style='font-size:12px; color:#666; margin-top:2px;'>🎭 {genre_str}</div>" if genre_str else ""

                    folder_str = movie.get("folder", "")
                    folder_badge = f"<div style='font-size:11px; color:#E50914; font-weight:bold; margin-top:2px;'>📁 {folder_str}</div>" if folder_str else ""

                    is_rec = movie.get("recommended", False)
                    rec_badge = "<span style='position:absolute; top:10px; right:10px; background-color:#E50914; color:white; padding:3px 8px; border-radius:20px; font-size:11px; font-weight:bold;'>🔥 Топ</span>" if is_rec else ""

                    card_html = textwrap.dedent(f"""
                        <div class="movie-card">
                            {rec_badge}
                            <img src="{movie['poster_url']}">
                            <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:18px; font-weight: 700;">{movie['title']}</h3>
                            <span style="background-color:#2B2B2B; color:white; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:bold; display: inline-block;">{movie['category']}</span>
                            {genre_badge}
                            {folder_badge}
                            {badges_html}
                        </div>
                    """).strip()
                    st.html(card_html)

                    if st.button(f"Открыть «{movie['title']}»", key=f"id_move_{movie['id']}", use_container_width=True):
                        st.query_params["movie_id"] = movie['id']
                        st.rerun()

                    if st.session_state.user_role == "Семён":
                        c_adm1, c_adm2 = st.columns(2)
                        with c_adm1:
                            if is_rec:
                                if st.button("❌ -Реком.", key=f"rem_rec_{movie['id']}", use_container_width=True):
                                    requests.patch(f"{SUPABASE_URL}/rest/v1/movies?id=eq.{movie['id']}",
                                                   headers=HEADERS, json={"recommended": False})
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                if st.button("🔥 +Реком.", key=f"add_rec_{movie['id']}", use_container_width=True):
                                    requests.patch(f"{SUPABASE_URL}/rest/v1/movies?id=eq.{movie['id']}",
                                                   headers=HEADERS, json={"recommended": True})
                                    st.cache_data.clear()
                                    st.rerun()

                        with c_adm2:
                            is_kk = movie.get("for_kristina", False)
                            if is_kk:
                                if st.button("❌ -КК", key=f"rem_kk_{movie['id']}", use_container_width=True):
                                    requests.patch(f"{SUPABASE_URL}/rest/v1/movies?id=eq.{movie['id']}",
                                                   headers=HEADERS, json={"for_kristina": False})
                                    st.cache_data.clear()
                                    st.rerun()
                            else:
                                if st.button("🍿 +КК", key=f"add_kk_{movie['id']}", use_container_width=True):
                                    requests.patch(f"{SUPABASE_URL}/rest/v1/movies?id=eq.{movie['id']}",
                                                   headers=HEADERS, json={"for_kristina": True})
                                    st.cache_data.clear()
                                    st.rerun()


    # --- SIDEBAR NAV ---
    with st.sidebar:
        st.markdown(f"### 👤 Профиль: **{st.session_state.user_role}**")
        st.write("---")

        page_options = [
            "🌐 Общий каталог",
            "🍿 Кинотеатр Кристины",
            "🔥 Семён рекомендует",
            "👤 Моё пространство"
        ]

        mapping = {
            "catalog": "🌐 Общий каталог",
            "kristina_cinema": "🍿 Кинотеатр Кристины",
            "semen_recommend": "🔥 Семён рекомендует",
            "my_space": "👤 Моё пространство"
        }

        reverse_mapping = {v: k for k, v in mapping.items()}

        current_selection = mapping.get(st.session_state.nav_page, "🌐 Общий каталог")
        selected_page = st.radio("🧭 Навигация по сайту:", page_options, index=page_options.index(current_selection))

        new_nav = reverse_mapping[selected_page]
        if new_nav != st.session_state.nav_page:
            st.session_state.nav_page = new_nav
            if "movie_id" in st.query_params:
                del st.query_params["movie_id"]
            st.rerun()

        st.write("---")
        if st.button("🚪 Выйти из аккаунта", use_container_width=True):
            st.session_state.user_role = None
            st.session_state.login_target = None
            st.session_state.nav_page = "catalog"
            st.query_params.clear()
            st.rerun()


    def apply_filters(source_list):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            cat_filter = st.multiselect("Тип:", ["Фильм", "Сериал", "Мультфильм"])
        with col_f2:
            genre_filter = st.multiselect("Жанр:", POPULAR_GENRES)
        with col_f3:
            all_folders = list(set([m.get("folder") for m in source_list if m.get("folder")]))
            folder_filter = st.selectbox("Папка / Франшиза:", ["Все папки"] + all_folders)

        filtered = source_list
        if cat_filter:
            filtered = [m for m in filtered if m.get("category") in cat_filter]
        if genre_filter:
            filtered = [m for m in filtered if any(g.strip() in genre_filter for g in m.get("genre", "").split(","))]
        if folder_filter != "Все папки":
            filtered = [m for m in filtered if m.get("folder") == folder_filter]

        return filtered


    # --- СТРАНИЦА: ОБЩИЙ КАТАЛОГ ---
    if st.session_state.current_page == "catalog":
        st.html("<h1 style='margin-bottom: 0px;'>🌐 Общий каталог</h1>")
        st.write("Здесь собрана вся киноколлекция!")

        st.html(f"""
            <div class="stats-box-new">
                <span style="font-weight: bold; font-size: 15px; color: #2B2B2B;">📊 Прогресс просмотра:</span> 
                <span style="color: #E50914; font-weight: 800; font-size: 15px; margin-left: 5px;">🎬 Просмотрено {user_watched} из {total_movies} тайтлов</span>
            </div>
        """)

        st.subheader("🔍 Фильтры поиска")
        filtered_movies = apply_filters(movies_list)

        st.write("---")
        render_movie_grid(filtered_movies)

        if st.session_state.user_role == "Семён":
            st.write("---")
            st.markdown("### 🛠 Панель Семёна (Управление системой)")
            adm_tab1, adm_tab2, adm_tab3, adm_tab4 = st.tabs(
                ["🎬 Добавить фильм", "🧠 Создать Квиз", "🔔 Заявки", "✏️ Редактировать фильм"])

            with adm_tab1:
                with st.form("add_movie_form", clear_on_submit=True):
                    col_form1, col_form2 = st.columns(2)
                    with col_form1:
                        new_title = st.text_input("🎬 Название фильма/сериала:")
                        new_category = st.selectbox("📁 Категория:", ["Фильм", "Сериал", "Мультфильм"])
                        new_genres = st.multiselect("🎭 Жанры:", POPULAR_GENRES)
                        new_folder = st.text_input("📁 Группировка в папку (например: Звёздные войны):")
                        new_poster = st.text_input("🖼 Ссылка на картинку постера (URL):")
                    with col_form2:
                        new_trailer = st.text_input("🍿 Ссылка на трейлер (YouTube):")
                        new_description = st.text_area("📝 Краткое описание:")
                        col_chk1, col_chk2 = st.columns(2)
                        with col_chk1:
                            is_rec = st.checkbox("🔥 Сделать рекомендованным")
                        with col_chk2:
                            is_kk = st.checkbox("🍿 В Кинотеатр Кристины")

                    if st.form_submit_button("Сохранить и добавить в каталог"):
                        if new_title and new_description:
                            save_local_movie({
                                "title": new_title,
                                "category": new_category,
                                "genre": ", ".join(new_genres),
                                "folder": new_folder.strip(),
                                "poster_url": new_poster if new_poster else "https://via.placeholder.com/300x450?text=Нет+постера",
                                "trailer_url": new_trailer,
                                "description": new_description,
                                "recommended": is_rec,
                                "for_kristina": is_kk
                            })
                            st.success(f"🎬 «{new_title}» успешно добавлен!")
                            st.rerun()
                        else:
                            st.warning("Заполни Название и Описание!")

            with adm_tab2:
                st.markdown("#### Добавить вопрос к фильму")
                if not movies_list:
                    st.info("Сначала добавь фильмы!")
                else:
                    quiz_movie = st.selectbox("Для какого фильма вопрос?", [m["title"] for m in movies_list])
                    q_text = st.text_input("❓ Вопрос:")
                    ans_1 = st.text_input("Вариант А:")
                    ans_2 = st.text_input("Вариант Б:")
                    ans_3 = st.text_input("Вариант В:")
                    correct_ans = st.selectbox("Правильный вариант?", ["А", "Б", "В"])

                    if st.button("➕ Добавить вопрос в тест"):
                        if q_text and ans_1 and ans_2 and ans_3:
                            selected_movie_obj = next(m for m in movies_list if m["title"] == quiz_movie)
                            try:
                                url_quiz = f"{SUPABASE_URL}/rest/v1/quizzes"
                                payload_quiz = {
                                    "movie_id": selected_movie_obj["id"],
                                    "movie_title": quiz_movie,
                                    "question": q_text,
                                    "options": {"А": ans_1, "Б": ans_2, "В": ans_3},
                                    "correct": correct_ans
                                }
                                requests.post(url_quiz, headers=HEADERS, json=payload_quiz)
                                st.cache_data.clear()
                                st.success("🧠 Вопрос успешно добавлен в базу данных квизов!")
                                st.rerun()
                            except:
                                st.error("Ошибка сохранения квиза!")
                        else:
                            st.warning("Заполни все поля!")

            with adm_tab3:
                st.markdown("#### 📥 Пожелания Кристины")
                if not requests_list:
                    st.info("Пока новых заявок нет.")
                else:
                    for req in requests_list:
                        col_req1, col_req2 = st.columns([3, 1])
                        with col_req1:
                            st.warning(f"🎬 **{req['title']}** (Добавь по-братски!)")
                        with col_req2:
                            if st.button("❌ Удалить из списка", key=f"del_req_{req['id']}"):
                                requests.delete(f"{SUPABASE_URL}/rest/v1/requests?id=eq.{req['id']}", headers=HEADERS)
                                st.cache_data.clear()
                                st.rerun()

            with adm_tab4:
                st.markdown("#### ✏️ Настройки жанров и папок у существующих фильмов")
                if not movies_list:
                    st.info("В базе пока нет фильмов.")
                else:
                    movie_titles = [m["title"] for m in movies_list]
                    selected_title = st.selectbox("Выбери фильм для редактирования:", movie_titles)

                    target_movie = next((m for m in movies_list if m["title"] == selected_title), None)

                    if target_movie:
                        with st.form(f"edit_form_{target_movie['id']}"):
                            raw_genre = target_movie.get("genre") or ""
                            existing_genres = [g.strip() for g in raw_genre.split(",") if g.strip()]

                            default_genres = [g for g in existing_genres if g in POPULAR_GENRES]

                            edit_genres = st.multiselect("Жанры:", POPULAR_GENRES, default=default_genres)
                            edit_folder = st.text_input("Папка / Франшиза:", value=target_movie.get("folder") or "")

                            if st.form_submit_button("Сохранить изменения"):
                                updated_genres = ", ".join(edit_genres)
                                updated_folder = edit_folder.strip()

                                try:
                                    patch_url = f"{SUPABASE_URL}/rest/v1/movies?id=eq.{target_movie['id']}"
                                    res = requests.patch(
                                        patch_url,
                                        headers=HEADERS,
                                        json={"genre": updated_genres, "folder": updated_folder}
                                    )
                                    if res.status_code in [200, 204]:
                                        st.success(f"Обновлены данные для фильма «{target_movie['title']}»!")
                                        st.rerun()
                                    else:
                                        st.error("Ошибка при обновлении Supabase.")
                                except Exception as e:
                                    st.error(f"Не удалось отправить запрос: {e}")

    # --- СТРАНИЦА: КИНОТЕАТР КРИСТИНЫ ---
    elif st.session_state.current_page == "kristina_cinema":
        st.html("<h1 style='margin-bottom: 0px;'>🍿 Кинотеатр Кристины</h1>")
        st.write("Эксклюзивная подборка, составленная специально для Кристины! 💕")

        st.write("---")
        st.markdown("### 🎲 Не знаешь что глянуть?")
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            random_filter = st.selectbox("Категория рандома:", ["Всё", "Фильм", "Сериал", "Мультфильм"])
        with col_r2:
            st.write(" ")
            if st.button("✨ Сёма, выбери за меня!", use_container_width=True):
                kk_movies = [m for m in movies_list if m.get("for_kristina", False)]
                unwatched_movies = [m for m in kk_movies if str(m["id"]) not in user_watched_ids]
                if random_filter != "Всё":
                    unwatched_movies = [m for m in unwatched_movies if m.get("category") == random_filter]

                if unwatched_movies:
                    st.session_state.random_movie = random.choice(unwatched_movies)
                else:
                    st.session_state.random_movie = "empty"

        if st.session_state.random_movie:
            if st.session_state.random_movie == "empty":
                st.info("Ты посмотрела вообще всё в этой категории! Семён, пора добавить новинок!")
            else:
                rm = st.session_state.random_movie
                st.html(textwrap.dedent(f"""
                    <div style="background-color: #FFF; border: 2px solid #E50914; padding: 15px; border-radius: 8px; margin-top: 10px; display: flex; gap: 15px; align-items: center;">
                        <img src="{rm['poster_url']}" style="width: 80px; max-height: 120px; object-fit: cover; border-radius: 4px;">
                        <div>
                            <h4 style="margin: 0; color: #E50914;">🍿 Идеальный вариант для тебя: «{rm['title']}»</h4>
                            <p style="margin: 5px 0 0 0; font-size: 14px;"><b>Категория:</b> {rm['category']} | {rm['description'][:150]}...</p>
                        </div>
                    </div>
                """))
                if st.button(f"🚀 Открыть «{rm['title']}»", key="open_random_btn"):
                    st.query_params["movie_id"] = rm['id']
                    st.rerun()

        st.write("---")
        st.subheader("🔍 Фильтры подборки")
        kristina_movies = [m for m in movies_list if m.get("for_kristina", False)]
        filtered_kristina = apply_filters(kristina_movies)

        st.write("---")
        render_movie_grid(filtered_kristina)

    # --- РАЗДЕЛ СЕМЁН РЕКОМЕНДУЕТ ---
    elif st.session_state.current_page == "semen_recommend":
        st.html("<h1>🔥 Семён рекомендует</h1>")
        st.write("Специальный топчик тайтлов, подобранный Сёмой для первоочередного просмотра! 🍿")
        st.write("---")

        rec_movies = [m for m in movies_list if m.get("recommended", False)]
        render_movie_grid(rec_movies)

    # --- МОЁ ПРОСТРАНСТВО С АЧИВКАМИ ---
    elif st.session_state.current_page == "my_space":
        st.html(f"<h1>👤 Моё пространство: {st.session_state.user_role}</h1>")

        st.html(f"""
            <div class="stats-box-new">
                <span style="font-weight: bold; font-size: 15px; color: #2B2B2B;">📊 Твоя личная статистика:</span> 
                <span style="color: #28A745; font-weight: 800; font-size: 15px; margin-left: 10px;">🎬 Просмотрено: {user_watched}</span>
                <span style="color: #FFC107; font-weight: 800; font-size: 15px; margin-left: 15px;">📌 Хочу посмотреть: {user_watchlist}</span>
            </div>
        """)

        if st.session_state.user_role == "Кристина":
            with st.form("request_movie_form", clear_on_submit=True):
                st.markdown("#### 💌 Не нашла нужного фильма в каталоге?")
                req_title = st.text_input("Напиши название фильма/сериала, и Семён добавит его на сайт:")
                if st.form_submit_button("🚀 Отправить Семёну"):
                    if req_title.strip():
                        try:
                            url_req = f"{SUPABASE_URL}/rest/v1/requests"
                            requests.post(url_req, headers=HEADERS, json={"title": req_title.strip()})
                            st.cache_data.clear()
                            st.success("Заявка улетела Сёме! 😉")
                            st.rerun()
                        except:
                            st.error("Ошибка отправки заявки.")
                    else:
                        st.warning("Введи название!")

        st.write("---")

        tab_watched, tab_watchlist, tab_ratings, tab_reviews, tab_achievements = st.tabs([
            "🎬 Просмотрено", "📌 Хочу посмотреть", "⭐️ Мои оценки", "✍️ Мои рецензии", "🏆 Мои Ачивки"
        ])

        with tab_watched:
            watched_movies = [m for m in movies_list if str(m["id"]) in user_watched_ids]
            render_movie_grid(watched_movies)

        with tab_watchlist:
            wish_movies = [m for m in movies_list if str(m["id"]) in user_watchlist_ids]
            render_movie_grid(wish_movies)

        with tab_ratings:
            user_revs = [r for r in reviews_list if r["username"] == st.session_state.user_role]
            if not user_revs:
                st.info("Оценок нет.")
            else:
                for ur in user_revs:
                    m_title = next((m["title"] for m in movies_list if str(m["id"]) == str(ur["movie_id"])), "Удален")
                    v_badge = f" | Вайб: {ur['vibe']}" if "vibe" in ur and ur["vibe"] else ""
                    st.write(f"⭐️ **{ur['rating']}/10** — {m_title}{v_badge}")

        with tab_reviews:
            user_revs = [r for r in reviews_list if r["username"] == st.session_state.user_role]
            valid_reviews = [r for r in user_revs if r.get("review_text") and r["review_text"].strip()]
            if not valid_reviews:
                st.info("Рецензий нет.")
            else:
                for ur in valid_reviews:
                    m_title = next((m["title"] for m in movies_list if str(m["id"]) == str(ur["movie_id"])), "Удален")
                    st.html(f"""
                        <div class="review-box">
                            <strong>🎬 {m_title}</strong> — <span style="color:#E50914; font-weight:bold;">⭐️ {ur['rating']}/10</span>
                            <p style="margin-top:5px; margin-bottom:0px; font-style: italic;">"{ur['review_text']}"</p>
                        </div>
                    """)

        with tab_achievements:
            st.markdown("### 🏆 Достижения киномана")

            watched_movies_objs = [m for m in movies_list if str(m["id"]) in user_watched_ids]

            cnt_watch_film = len([m for m in watched_movies_objs if m["category"] == "Фильм"])
            cnt_watch_serial = len([m for m in watched_movies_objs if m["category"] == "Сериал"])
            cnt_watch_mult = len([m for m in watched_movies_objs if m["category"] == "Мультфильм"])
            cnt_watch_total = len(watched_movies_objs)

            user_all_reviews = [r for r in reviews_list if r["username"] == st.session_state.user_role]
            rated_movie_ids = list(set([str(r["movie_id"]) for r in user_all_reviews]))
            reviewed_movie_ids = list(
                set([str(r["movie_id"]) for r in user_all_reviews if
                     r.get("review_text") and r["review_text"].strip()]))

            rated_objs = [m for m in movies_list if str(m["id"]) in rated_movie_ids]
            cnt_rate_film = len([m for m in rated_objs if m["category"] == "Фильм"])
            cnt_rate_serial = len([m for m in rated_objs if m["category"] == "Сериал"])
            cnt_rate_mult = len([m for m in rated_objs if m["category"] == "Мультфильм"])
            cnt_rate_total = len(rated_objs)

            reviewed_objs = [m for m in movies_list if str(m["id"]) in reviewed_movie_ids]
            cnt_rev_film = len([m for m in reviewed_objs if m["category"] == "Фильм"])
            cnt_rev_serial = len([m for m in reviewed_objs if m["category"] == "Сериал"])
            cnt_rev_mult = len([m for m in reviewed_objs if m["category"] == "Мультфильм"])
            cnt_rev_total = len(reviewed_objs)

            achievements_config = [
                {"target": 1, "cur": cnt_watch_film, "name": "Первый сеанс", "desc": "Посмотреть 1 фильм",
                 "emoji": "🎥"},
                {"target": 3, "cur": cnt_watch_film, "name": "«Зритель с дивана»", "desc": "Посмотреть 3 фильма",
                 "emoji": "🛋"},
                {"target": 5, "cur": cnt_watch_film, "name": "Разогрев проектора", "desc": "Посмотреть 5 фильмов",
                 "emoji": "📽"},
                {"target": 7, "cur": cnt_watch_film, "name": "Вошла во вкус", "desc": "Посмотреть 7 фильмов",
                 "emoji": "😋"},
                {"target": 10, "cur": cnt_watch_film, "name": "«Смотрю лучше, чем сплю»",
                 "desc": "Посмотреть 10 фильмов", "emoji": "☕️"},
                {"target": 15, "cur": cnt_watch_film, "name": "Постоянный зритель", "desc": "Посмотреть 15 фильмов",
                 "emoji": "🎟"},
                {"target": 20, "cur": cnt_watch_film, "name": "«Золотая коллекция»", "desc": "Посмотреть 20 фильмов",
                 "emoji": "🏆"},
                {"target": 25, "cur": cnt_watch_film, "name": "Хранитель попкорна", "desc": "Посмотреть 25 фильмов",
                 "emoji": "🍿"},
                {"target": 30, "cur": cnt_watch_film, "name": "Легенда кинозала", "desc": "Посмотреть 30 фильмов",
                 "emoji": "👑"},

                {"target": 1, "cur": cnt_watch_serial, "name": "«Пилотный эпизод»", "desc": "Посмотреть 1 сериал",
                 "emoji": "📺"},
                {"target": 3, "cur": cnt_watch_serial, "name": "Ещё одну и спать", "desc": "Посмотреть 3 сериала",
                 "emoji": "🥱"},
                {"target": 5, "cur": cnt_watch_serial, "name": "Марафонец сезонов", "desc": "Посмотреть 5 сериалов",
                 "emoji": "🏃‍♀️"},
                {"target": 7, "cur": cnt_watch_serial, "name": "«Втянулся»", "desc": "Посмотреть 7 сериалов",
                 "emoji": "🧲"},
                {"target": 10, "cur": cnt_watch_serial, "name": "Спонсор бессонницы", "desc": "Посмотреть 10 сериалов",
                 "emoji": "🦉"},
                {"target": 15, "cur": cnt_watch_serial, "name": "«Королева сезонов»", "desc": "Посмотреть 15 сериалов",
                 "emoji": "💅"},

                {"target": 1, "cur": cnt_watch_mult, "name": "Возвращение в детство", "desc": "Посмотреть 1 мультфильм",
                 "emoji": "🧸"},
                {"target": 3, "cur": cnt_watch_mult, "name": "Друг мультгероев", "desc": "Посмотреть 3 мультфильма",
                 "emoji": "🎈"},
                {"target": 5, "cur": cnt_watch_mult, "name": "Любитель анимации", "desc": "Посмотреть 5 мультфильмов",
                 "emoji": "🎨"},
                {"target": 7, "cur": cnt_watch_mult, "name": "«Мультяшный фанат»", "desc": "Посмотреть 7 мультфильмов",
                 "emoji": "🍭"},
                {"target": 10, "cur": cnt_watch_mult, "name": "2D и 3D эксперт", "desc": "Посмотреть 10 мультфильмов",
                 "emoji": "🕶"},
                {"target": 15, "cur": cnt_watch_mult, "name": "Фанат Диснея", "desc": "Посмотреть 15 мультфильмов",
                 "emoji": "🏰"},
                {"target": 20, "cur": cnt_watch_mult, "name": "«Анимания»", "desc": "Посмотреть 20 мультфильмов",
                 "emoji": "⚡️"},
                {"target": 25, "cur": cnt_watch_mult, "name": "Мультяшный эксперт",
                 "desc": "Посмотреть 25 мультфильмов", "emoji": "💫"},
                {"target": 30, "cur": cnt_watch_mult, "name": "Повелитель рисовки",
                 "desc": "Посмотреть 30 мультфильмов", "emoji": "🔮"},

                {"target": 5, "cur": cnt_watch_total, "name": "«Киномарафонец»", "desc": "Посмотреть 5 тайтлов",
                 "emoji": "🧭"},
                {"target": 7, "cur": cnt_watch_total, "name": "«Кинолюбитель»", "desc": "Посмотреть 7 тайтлов",
                 "emoji": "❤️"},
                {"target": 10, "cur": cnt_watch_total, "name": "«Кинопутешественник»", "desc": "Посмотреть 10 тайтлов",
                 "emoji": "🌍"},
                {"target": 15, "cur": cnt_watch_total, "name": "Почетный гость Кинозала",
                 "desc": "Посмотреть 15 тайтлов", "emoji": "📜"},
                {"target": 20, "cur": cnt_watch_total, "name": "Хранитель пульта", "desc": "Посмотреть 20 тайтлов",
                 "emoji": "🎮"},
                {"target": 25, "cur": cnt_watch_total, "name": "«Друг режиссёра»", "desc": "Посмотреть 25 тайтлов",
                 "emoji": "🤝"},
                {"target": 30, "cur": cnt_watch_total, "name": "«Хранитель кадров»", "desc": "Посмотреть 30 тайтлов",
                 "emoji": "🗄"},
                {"target": 35, "cur": cnt_watch_total, "name": "Амбассадор Кинопоиска", "desc": "Посмотреть 35 тайтлов",
                 "emoji": "💎"},
                {"target": 40, "cur": cnt_watch_total, "name": "Покоритель экранов", "desc": "Посмотреть 40 тайтлов",
                 "emoji": "🚀"},
                {"target": 45, "cur": cnt_watch_total, "name": "Легенда просмотра", "desc": "Посмотреть 45 тайтлов",
                 "emoji": "🌠"},
                {"target": 50, "cur": cnt_watch_total, "name": "Живёт в кинозале", "desc": "Посмотреть 50 тайтлов",
                 "emoji": "🏠"},
                {"target": 55, "cur": cnt_watch_total, "name": "Спилберг нервно курит", "desc": "Посмотреть 55 тайтлов",
                 "emoji": "🚬"},
                {"target": 60, "cur": cnt_watch_total, "name": "«Властелин кинематографа»",
                 "desc": "Посмотреть 60 тайтлов", "emoji": "🧝‍♂️"},

                {"target": 1, "cur": cnt_rate_film, "name": "«Первый вердикт»", "desc": "Оценить 1 фильм",
                 "emoji": "⚖️"},
                {"target": 3, "cur": cnt_rate_film, "name": "Уже есть мнение", "desc": "Оценить 3 фильма",
                 "emoji": "🗣"},
                {"target": 5, "cur": cnt_rate_film, "name": "Оценщик кадров", "desc": "Оценить 5 фильмов",
                 "emoji": "📋"},
                {"target": 7, "cur": cnt_rate_film, "name": "Член жюри", "desc": "Оценить 7 фильмов", "emoji": "🧐"},
                {"target": 10, "cur": cnt_rate_film, "name": "Судья кинозала", "desc": "Оценить 10 фильмов",
                 "emoji": "🔨"},
                {"target": 15, "cur": cnt_rate_film, "name": "Раздающий звезды", "desc": "Оценить 15 фильмов",
                 "emoji": "✨"},
                {"target": 20, "cur": cnt_rate_film, "name": "Мастер рейтингов", "desc": "Оценить 20 фильмов",
                 "emoji": "📈"},
                {"target": 25, "cur": cnt_rate_film, "name": "Кинокритик", "desc": "Оценить 25 фильмов",
                 "emoji": "🕵️‍♀️"},
                {"target": 30, "cur": cnt_rate_film, "name": "«Властелин кинематографа»", "desc": "Оценить 30 фильмов",
                 "emoji": "🌋"},

                {"target": 1, "cur": cnt_rate_serial, "name": "Первый вердикт (Сериалы)", "desc": "Оценить 1 сериал",
                 "emoji": "⏳"},
                {"target": 3, "cur": cnt_rate_serial, "name": "«Сверхзритель»", "desc": "Оценить 3 сериала",
                 "emoji": "🦸‍♀️"},
                {"target": 5, "cur": cnt_rate_serial, "name": "Звездный марафон", "desc": "Оценить 5 сериалов",
                 "emoji": "🌌"},
                {"target": 7, "cur": cnt_rate_serial, "name": "Оценщик сезонов", "desc": "Оценить 7 сериалов",
                 "emoji": "📊"},
                {"target": 10, "cur": cnt_rate_serial, "name": "Знаток сериалов", "desc": "Оценить 10 сериалов",
                 "emoji": "🧠"},
                {"target": 15, "cur": cnt_rate_serial, "name": "Судья Netflix", "desc": "Оценить 15 сериалов",
                 "emoji": "🔴"},

                {"target": 1, "cur": cnt_rate_mult, "name": "Первое мнение", "desc": "Оценить 1 мультфильм",
                 "emoji": "👶"},
                {"target": 3, "cur": cnt_rate_mult, "name": "Добрый критик", "desc": "Оценить 3 мультфильма",
                 "emoji": "☀️"},
                {"target": 5, "cur": cnt_rate_mult, "name": "Звездочет мультяшек", "desc": "Оценить 5 мультфильмов",
                 "emoji": "🌠"},
                {"target": 7, "cur": cnt_rate_mult, "name": "Анимационное жюри", "desc": "Оценить 7 мультфильмов",
                 "emoji": "🦄"},
                {"target": 10, "cur": cnt_rate_mult, "name": "Знаток анимации", "desc": "Оценить 10 мультфильмов",
                 "emoji": "🤓"},
                {"target": 15, "cur": cnt_rate_mult, "name": "Мульткритик", "desc": "Оценить 15 мультфильмов",
                 "emoji": "✍️"},
                {"target": 20, "cur": cnt_rate_mult, "name": "Раздающий лайки", "desc": "Оценить 20 мультфильмов",
                 "emoji": "👍"},
                {"target": 25, "cur": cnt_rate_mult, "name": "Строгий, но справедливый",
                 "desc": "Оценить 25 мультфильмов", "emoji": "📐"},
                {"target": 30, "cur": cnt_rate_mult, "name": "Легендарный судья анимации",
                 "desc": "Оценить 30 мультфильмов", "emoji": "🐉"},

                {"target": 5, "cur": cnt_rate_total, "name": "Младший оценщик", "desc": "Оценить 5 тайтлов",
                 "emoji": "🌱"},
                {"target": 7, "cur": cnt_rate_total, "name": "Есть что сказать", "desc": "Оценить 7 тайтлов",
                 "emoji": "💬"},
                {"target": 10, "cur": cnt_rate_total, "name": "Уверенный критик", "desc": "Оценить 10 тайтлов",
                 "emoji": "🎙"},
                {"target": 15, "cur": cnt_rate_total, "name": "Формирователь вкуса", "desc": "Оценить 15 тайтлов",
                 "emoji": "🍏"},
                {"target": 20, "cur": cnt_rate_total, "name": "Куратор рейтингов", "desc": "Оценить 20 тайтлов",
                 "emoji": "💎"},
                {"target": 25, "cur": cnt_rate_total, "name": "Эксперт впечатлений", "desc": "Оценить 25 тайтлов",
                 "emoji": "🔮"},
                {"target": 30, "cur": cnt_rate_total, "name": "Неподкупное жюри", "desc": "Оценить 30 тайтлов",
                 "emoji": "🔒"},
                {"target": 35, "cur": cnt_rate_total, "name": "Профи оценок", "desc": "Оценить 35 тайтлов",
                 "emoji": "🎖"},
                {"target": 40, "cur": cnt_rate_total, "name": "Мастер вкуса", "desc": "Оценить 40 тайтлов",
                 "emoji": "🍒"},
                {"target": 45, "cur": cnt_rate_total, "name": "Энциклопедия оценок", "desc": "Оценить 45 тайтлов",
                 "emoji": "📚"},
                {"target": 50, "cur": cnt_rate_total, "name": "Абсолютный авторитет", "desc": "Оценить 50 тайтлов",
                 "emoji": "🔱"},
                {"target": 55, "cur": cnt_rate_total, "name": "Министерство культуры", "desc": "Оценить 55 тайтлов",
                 "emoji": "🏛"},
                {"target": 60, "cur": cnt_rate_total, "name": "Верховный суд кино", "desc": "Оценить 60 тайтлов",
                 "emoji": "🦅"},

                {"target": 1, "cur": cnt_rev_film, "name": "«Первое слово»", "desc": "Написать рецензию на 1 фильм",
                 "emoji": "✏️"},
                {"target": 3, "cur": cnt_rev_film, "name": "«Критик-любитель»", "desc": "Написать рецензию на 3 фильма",
                 "emoji": "📝"},
                {"target": 5, "cur": cnt_rev_film, "name": "«Вдумчивый зритель»",
                 "desc": "Написать рецензию на 5 фильмов", "emoji": "🤔"},
                {"target": 7, "cur": cnt_rev_film, "name": "Мастер слова", "desc": "Написать рецензию на 7 фильмов",
                 "emoji": "✒️"},
                {"target": 10, "cur": cnt_rev_film, "name": "Независимый эксперт",
                 "desc": "Написать рецензию на 10 фильмов", "emoji": "🕊"},
                {"target": 15, "cur": cnt_rev_film, "name": "«Голос кинозала»",
                 "desc": "Написать рецензию на 15 фильмов", "emoji": "📢"},
                {"target": 20, "cur": cnt_rev_film, "name": "«Острое перо»", "desc": "Написать рецензию на 20 фильмов",
                 "emoji": "🪶"},
                {"target": 25, "cur": cnt_rev_film, "name": "Голос народа", "desc": "Написать рецензию на 25 фильмов",
                 "emoji": "👥"},
                {"target": 30, "cur": cnt_rev_film, "name": "Гений мысли", "desc": "Написать рецензию на 30 фильмов",
                 "emoji": "💡"},

                {"target": 1, "cur": cnt_rev_serial, "name": "Первая заметка", "desc": "Написать рецензию на 1 сериал",
                 "emoji": "📓"},
                {"target": 3, "cur": cnt_rev_serial, "name": "Обзорщик сезонов",
                 "desc": "Написать рецензию на 3 сериала", "emoji": "🎞"},
                {"target": 5, "cur": cnt_rev_serial, "name": "Автор теорий", "desc": "Написать рецензию на 5 сериалов",
                 "emoji": "🕵️"},
                {"target": 7, "cur": cnt_rev_serial, "name": "Летописец сериалов",
                 "desc": "Написать рецензию на 7 сериалов", "emoji": "🗂"},
                {"target": 10, "cur": cnt_rev_serial, "name": "Ловец деталей",
                 "desc": "Написать рецензию на 10 сериалов", "emoji": "🔍"},
                {"target": 15, "cur": cnt_rev_serial, "name": "Повелитель обзоров",
                 "desc": "Написать рецензию на 15 сериалов", "emoji": "👑"},

                {"target": 1, "cur": cnt_rev_mult, "name": "Первое впечатление",
                 "desc": "Написать рецензию на 1 мультфильм", "emoji": "✨"},
                {"target": 3, "cur": cnt_rev_mult, "name": "Автор волшебных строк",
                 "desc": "Написать рецензию на 3 мультфильма", "emoji": "🪄"},
                {"target": 5, "cur": cnt_rev_mult, "name": "Мульт-обозреватель",
                 "desc": "Написать рецензию на 5 мультфильмов", "emoji": "🦊"},
                {"target": 7, "cur": cnt_rev_mult, "name": "Разбор рисовки",
                 "desc": "Написать рецензию на 7 мультфильмов", "emoji": "📐"},
                {"target": 10, "cur": cnt_rev_mult, "name": "Летописец мультмиров",
                 "desc": "Написать рецензию на 10 мультфильмов", "emoji": "🗺"},
                {"target": 15, "cur": cnt_rev_mult, "name": "Профессор анимации",
                 "desc": "Написать рецензию на 15 мультфильмов", "emoji": "🎓"},
                {"target": 20, "cur": cnt_rev_mult, "name": "Маг рецензий",
                 "desc": "Написать рецензию на 20 мультфильмов", "emoji": "🔮"},
                {"target": 25, "cur": cnt_rev_mult, "name": "Архивариус детства",
                 "desc": "Написать рецензию на 25 мультфильмов", "emoji": "🧸"},
                {"target": 30, "cur": cnt_rev_mult, "name": "Легенда анимации",
                 "desc": "Написать рецензию на 30 мультфильмов", "emoji": "🐉"},

                {"target": 5, "cur": cnt_rev_total, "name": "Начинающий автор",
                 "desc": "Написать рецензию на 5 тайтлов", "emoji": "✍️"},
                {"target": 7, "cur": cnt_rev_total, "name": "Любитель обзоров",
                 "desc": "Написать рецензию на 7 тайтлов", "emoji": "📂"},
                {"target": 10, "cur": cnt_rev_total, "name": "Аналитик с дивана",
                 "desc": "Написать рецензию на 10 тайтлов", "emoji": "🍿"},
                {"target": 15, "cur": cnt_rev_total, "name": "Киноблогер", "desc": "Написать рецензию на 15 тайтлов",
                 "emoji": "🤳"},
                {"target": 20, "cur": cnt_rev_total, "name": "Свободный микрофон",
                 "desc": "Написать рецензию на 20 тайтлов", "emoji": "🎙"},
                {"target": 25, "cur": cnt_rev_total, "name": "Повелитель текста",
                 "desc": "Написать рецензию на 25 тайтлов", "emoji": "📖"},
                {"target": 30, "cur": cnt_rev_total, "name": "Голос сообщества",
                 "desc": "Написать рецензию на 30 тайтлов", "emoji": "📣"},
                {"target": 35, "cur": cnt_rev_total, "name": "Мыслитель", "desc": "Написать рецензию на 35 тайтлов",
                 "emoji": "🧠"},
                {"target": 40, "cur": cnt_rev_total, "name": "Мастер пера", "desc": "Написать рецензию на 40 тайтлов",
                 "emoji": "🪶"},
                {"target": 45, "cur": cnt_rev_total, "name": "Главный редактор",
                 "desc": "Написать рецензию на 45 тайтлов", "emoji": "🏢"},
                {"target": 50, "cur": cnt_rev_total, "name": "Хранитель рецензий",
                 "desc": "Написать рецензию на 50 тайтлов", "emoji": "🏛"},
                {"target": 55, "cur": cnt_rev_total, "name": "Живая энциклопедия",
                 "desc": "Написать рецензию на 55 тайтлов", "emoji": "🦁"},
                {"target": 60, "cur": cnt_rev_total, "name": "Абсолютный обозреватель",
                 "desc": "Написать рецензию на 60 тайтлов", "emoji": "👑"}
            ]

            ach_sub_tab1, ach_sub_tab2 = st.tabs(["🎉 Полученные", "🌐 Все ачивки"])

            with ach_sub_tab1:
                earned_any = False
                for ach in achievements_config:
                    if ach["cur"] >= ach["target"]:
                        earned_any = True
                        st.html(f"""
                            <div class="achievement-card earned">
                                <h4 style="margin:0; color:#28A745;">{ach['emoji']} {ach['name']} <span style="font-size:12px; font-weight:normal;">[ПОЛУЧЕНО]</span></h4>
                                <p style="margin:5px 0 0 0; font-size:14px; color:#555;">{ach['desc']} (Выполнено: {ach['cur']}/{ach['target']})</p>
                            </div>
                        """)
                if not earned_any:
                    st.info("У тебя пока нет полученных ачивок. Время посмотреть первый фильм!")

            with ach_sub_tab2:
                for ach in achievements_config:
                    is_earned = ach["cur"] >= ach["target"]
                    progress = min(ach["cur"] / ach["target"], 1.0)

                    if is_earned:
                        st.html(f"""
                            <div class="achievement-card earned">
                                <h4 style="margin:0; color:#28A745;">{ach['emoji']} {ach['name']} <span style="font-size:12px; font-weight:normal;">[ПОЛУЧЕНО]</span></h4>
                                <p style="margin:5px 0 0 0; font-size:14px; color:#555;">{ach['desc']}</p>
                            </div>
                        """)
                        st.progress(progress)
                    else:
                        st.html(f"""
                            <div class="achievement-card">
                                <h4 style="margin:0; color:#2B2B2B;">{ach['emoji']} {ach['name']}</h4>
                                <p style="margin:5px 0 0 0; font-size:14px; color:#666;">{ach['desc']} — Прогресс: <b>{ach['cur']}</b> из <b>{ach['target']}</b></p>
                            </div>
                        """)
                        st.progress(progress)

    # --- СТРАНИЦА ПРОСМОТРА КАРТОЧКИ ФИЛЬМА ---
    if st.session_state.current_page == "movie_view" and st.session_state.selected_movie_id is not None:
        movie = next((m for m in movies_list if str(m["id"]) == str(st.session_state.selected_movie_id)), None)

        if movie:
            if st.button("⬅️ НАЗАД В КАТАЛОГ ФИЛЬМОВ", use_container_width=True):
                del st.query_params["movie_id"]
                st.rerun()

            st.write("---")
            st.html(f"<h1>🎬 {movie['title']}</h1>")

            meta_info = []
            if movie.get("genre"): meta_info.append(f"🎭 Жанр: **{movie['genre']}**")
            if movie.get("folder"): meta_info.append(f"📁 Папка: **{movie['folder']}**")
            if meta_info:
                st.markdown(" | ".join(meta_info))

            st.write("")

            col_view1, col_view2 = st.columns([1, 2])
            with col_view1:
                st.image(movie['poster_url'], use_container_width=True)
            with col_view2:
                st.markdown("### 📝 Описание фильма")
                st.write(movie['description'])
                st.write("---")

                st.markdown("### 🎯 Твой статус фильма")
                current_status = next((a["status"] for a in actions_list if
                                       a["username"] == st.session_state.user_role and str(a["movie_id"]) == str(
                                           movie["id"])),
                                      None)

                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if current_status == "watched":
                        st.success("✅ Просмотрено тобой")
                    else:
                        if st.button("🎬 Отметить просмотренным", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], "watched")
                            st.rerun()
                with col_btn2:
                    if current_status == "watchlist":
                        st.warning("📌 В планах на просмотр")
                    else:
                        if st.button("📌 Хочу посмотреть", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], "watchlist")
                            st.rerun()
                with col_btn3:
                    if current_status:
                        if st.button("❌ Сбросить статус", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], None)
                            st.rerun()

                st.write("---")
                if movie['trailer_url']:
                    st.html(f"### 🍿 <a href='{movie['trailer_url']}' target='_blank'>Смотреть трейлер на YouTube</a>")
                    if "youtube.com" in movie['trailer_url'] or "youtu.be" in movie['trailer_url']:
                        st.video(movie['trailer_url'])
                else:
                    st.info("Трейлер к этому фильму не добавлен.")

            st.write("---")

            # --- БЛОК ОТЗЫВОВ И РЕЦЕНЗИЙ ---
            st.markdown(f"### ✍️ Оставить рецензию на фильм «{movie['title']}»")

            rating = st.slider("Выбери оценку на шкале:", min_value=1, max_value=10, value=5)
            st.html(f"<h2>📈 Твоя оценка: <span style='color:#E50914; font-weight:900;'>⭐️ {rating} / 10</span></h2>")

            st.markdown("### 🌡️ Вайбометр")
            vibe_options = ["🥱 Выдержала до титров", "😢 Поплакала", "🌀 Ничего не поняла, но очень интересно",
                            "🔥 Полный треш", "✨ Вайбик"]
            selected_vibe = st.radio("Какое настроение оставил фильм?", vibe_options, horizontal=True)

            review_text = st.text_area("Напиши свои впечатления:")

            if st.button("Сохранить отзыв и оценку", use_container_width=True):
                save_local_review({"movie_id": movie["id"], "username": st.session_state.user_role, "rating": rating,
                                   "vibe": selected_vibe, "review_text": review_text})
                save_local_action(st.session_state.user_role, movie["id"], "watched")
                st.success("Рецензия успешно сохранена!")
                st.rerun()

            # --- ТЕСТЫ ПОД ОТЗЫВАМИ В КАРТОЧКЕ ФИЛЬМА ---
            movie_quizzes = [q for q in quizzes_list if str(q["movie_id"]) == str(movie["id"])]
            if movie_quizzes:
                st.write("---")
                st.markdown("### 🧠 Мини-тесты от Семёна по этому фильму:")

                for idx, mq in enumerate(movie_quizzes):
                    passed_mq = next((r for r in quiz_results if
                                      r["username"] == st.session_state.user_role and str(r["quiz_id"]) == str(
                                          mq["id"])), None)

                    st.html(f"""
                        <div class="quiz-single-box">
                            <span style="color:#E50914; font-weight:bold;">Вопрос #{idx + 1}:</span> {mq['question']}
                        </div>
                    """)

                    if passed_mq:
                        if passed_mq["is_correct"]:
                            st.success(f"Твой ответ '{passed_mq['user_answer']}' — Правильно! 🎉")
                        else:
                            st.error(
                                f"Твой ответ '{passed_mq['user_answer']}' — Неверно. Семён загадал вариант: {mq['correct']}")
                    else:
                        user_ans_mq = st.radio("Варианты:", [f"{k}: {v}" for k, v in mq["options"].items()],
                                               key=f"mq_card_ans_{mq['id']}")
                        if st.button("🎯 Ответить на вопрос", key=f"btn_mq_card_{mq['id']}"):
                            try:
                                url_res = f"{SUPABASE_URL}/rest/v1/quiz_results"
                                payload_res = {
                                    "username": st.session_state.user_role,
                                    "quiz_id": mq["id"],
                                    "user_answer": user_ans_mq[0],
                                    "is_correct": (user_ans_mq[0] == mq["correct"])
                                }
                                requests.post(url_res, headers=HEADERS, json=payload_res)
                                st.cache_data.clear()
                                st.rerun()
                            except:
                                st.error("Ошибка сохранения ответа!")

            st.write("---")
            st.markdown("### 💬 Рецензии зрителей")
            movie_reviews = [r for r in reviews_list if str(r["movie_id"]) == str(movie["id"])]

            if not movie_reviews:
                st.info("Отзывов пока нет.")
            else:
                for rev in movie_reviews:
                    vibe_str = f" | Настроение: <b>{rev.get('vibe', '')}</b>" if rev.get('vibe') else ""
                    st.html(f"""
                        <div class="review-box">
                            <strong>👤 {rev['username']}</strong> — <span style="color:#E50914; font-weight:bold;">⭐️ {rev['rating']}/10</span> {vibe_str}
                            <p style="margin-top:5px; margin-bottom:0px; color:#444!important;">{rev.get('review_text', '')}</p>
                        </div>
                    """)

# ==========================================
# 🛠 ТЕХПОДДЕРЖКА (ФУТЕР)
# ==========================================
st.write("---")
_, footer_col, _ = st.columns([1, 2, 1])
with footer_col:
    st.html("""
        <div style="text-align: center; color: #777777; font-size: 14px; margin-top: 10px; margin-bottom: 20px;">
            💡 Есть вопросы, пожелания или что-то не работает?<br>
            Пиши боту поддержки: 
            <a href="https://t.me/kinoroom132_bot" target="_blank" style="color: #E50914; font-weight: bold; text-decoration: none;">
                @kinoroom132_bot 🚀
            </a>
        </div>
    """)
