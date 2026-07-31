import streamlit as st
import json
import os
import random

# 1. Настройка страницы
st.set_page_config(
    page_title="Кино Room",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# НАЗВАНИЯ ВСЕХ ФАЙЛОВ БАЗЫ ДАННЫХ (LOCAL JSON / FALLBACK)
DB_FILE = "movies.json"
REVIEWS_FILE = "reviews.json"
ACTIONS_FILE = "user_actions.json"
QUIZZES_FILE = "quizzes.json"
QUIZ_RESULTS_FILE = "quiz_results.json"
REQUESTS_FILE = "requests.json"


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ / БАЗОЙ ---
def load_json(filename):
    if not os.path.exists(filename): return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Быстрые обертки
def load_local_movies(): return load_json(DB_FILE)


def load_local_reviews(): return load_json(REVIEWS_FILE)


def load_local_actions(): return load_json(ACTIONS_FILE)


def load_local_quizzes(): return load_json(QUIZZES_FILE)


def load_local_quiz_results(): return load_json(QUIZ_RESULTS_FILE)


def load_local_requests(): return load_json(REQUESTS_FILE)


def save_local_movie(movie_data):
    movies = load_local_movies()
    if "id" not in movie_data or not movie_data["id"]:
        movie_data["id"] = max([m["id"] for m in movies], default=0) + 1
    movie_data["recommended"] = movie_data.get("recommended", False)
    movie_data["genre"] = movie_data.get("genre", "Без жанра")

    # Редактирование или добавление
    existing_idx = next((i for i, m in enumerate(movies) if m["id"] == movie_data["id"]), None)
    if existing_idx is not None:
        movies[existing_idx] = movie_data
    else:
        movies.append(movie_data)

    save_json(DB_FILE, movies)


def save_local_review(review_data):
    reviews = load_local_reviews()
    reviews.append(review_data)
    save_json(REVIEWS_FILE, reviews)


def save_local_action(username, movie_id, status):
    actions = load_local_actions()
    actions = [a for a in actions if
               not (a["username"] == username and a["movie_id"] == movie_id and a["status"] == status)]
    if status:
        actions.append({"username": username, "movie_id": movie_id, "status": status})
    save_json(ACTIONS_FILE, actions)


# --- СИНХРОНИЗАЦИЯ URL ---
if "movie_id" in st.query_params:
    try:
        st.session_state.selected_movie_id = int(st.query_params["movie_id"])
        st.session_state.current_page = "movie_view"
    except:
        st.session_state.current_page = "catalog"
        st.session_state.selected_movie_id = None
else:
    if "nav_page" in st.session_state:
        st.session_state.current_page = st.session_state.nav_page
    else:
        st.session_state.current_page = "catalog"
    st.session_state.selected_movie_id = None

# --- ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if "user_role" not in st.session_state: st.session_state.user_role = None
if "login_target" not in st.session_state: st.session_state.login_target = None
if "nav_page" not in st.session_state: st.session_state.nav_page = "catalog"
if "random_movie" not in st.session_state: st.session_state.random_movie = None

# 2. Кастомный CSS стиль (включая русификацию плейсхолдеров)
st.markdown("""
    <style>
    .stApp { background-color: #FAFAFA; color: #2B2B2B; }
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }

    /* Перевод плейсхолдера Choose options */
    div[data-baseweb="select"] span {
        font-size: 0px !important;
    }
    div[data-baseweb="select"] span::after {
        content: "Выберите значение...";
        font-size: 14px !important;
        color: #666;
    }

    /* Кнопки */
    div.stButton > button {
        background-color: #E50914 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        transition: 0.2s !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1) !important;
    }
    div.stButton > button p { color: #FFFFFF !important; font-weight: 800 !important; }
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

    .movie-card {
        background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px;
        padding: 15px; text-align: center; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05); transition: 0.3s;
        margin-bottom: 10px; position: relative; min-height: 480px; display: flex; flex-direction: column; justify: space-between;
    }
    .movie-card:hover {
        border-color: #E50914; box-shadow: 0px 6px 15px rgba(229, 9, 20, 0.15); transform: translateY(-2px);
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
""", unsafe_allow_html=True)

# ==========================================
# 🔐 ЭКРАН ВХОДА
# ==========================================
if st.session_state.user_role is None:
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.write("")
        st.markdown("<h1 style='text-align: center;'>🎬 Кино Room</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666; font-size: 16px;'>Добро пожаловать. Кто заходит?</p>",
                    unsafe_allow_html=True)
        st.write("---")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🕶 Семён (Админ)", use_container_width=True):
                st.session_state.login_target = "Семён";
                st.rerun()
        with btn_col2:
            if st.button("🍿 Кристина", use_container_width=True):
                st.session_state.user_role = "Кристина";
                st.rerun()

        if st.session_state.login_target == "Семён":
            st.write("---")
            password = st.text_input("Введите секретный пароль:", type="password")
            if st.button("Войти как Администратор"):
                if password == "0105":
                    st.session_state.user_role = "Семён"
                    st.success("Доступ разрешен!");
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
    user_watched_ids = [a["movie_id"] for a in actions_list if
                        a["username"] == st.session_state.user_role and a["status"] == "watched"]
    user_watched = len(user_watched_ids)
    user_watchlist_ids = [a["movie_id"] for a in actions_list if
                          a["username"] == st.session_state.user_role and a["status"] == "watchlist"]
    user_watchlist = len(user_watchlist_ids)

    kk_movie_ids = [a["movie_id"] for a in actions_list if a["status"] == "kristina_cinema"]

    with st.sidebar:
        st.markdown(f"### 👤 Профиль: **{st.session_state.user_role}**")
        st.write("---")

        page = st.radio("🧭 Навигация по сайту:",
                        ["🏠 Главный каталог", "🔥 Семён рекомендует", "🍿 Кинотеатр Кристины", "👤 Моё пространство"])
        if page == "🏠 Главный каталог":
            st.session_state.nav_page = "catalog"
        elif page == "🔥 Семён рекомендует":
            st.session_state.nav_page = "semen_recommend"
        elif page == "🍿 Кинотеатр Кристины":
            st.session_state.nav_page = "kk_cinema"
        else:
            st.session_state.nav_page = "my_space"

        st.write("---")
        if st.button("🚪 Выйти из аккаунта", use_container_width=True):
            st.session_state.user_role = None;
            st.session_state.login_target = None
            st.session_state.nav_page = "catalog";
            st.query_params.clear();
            st.rerun()

    if "movie_id" not in st.query_params:
        st.session_state.current_page = st.session_state.nav_page

    # --- СТРАНИЦА КАТАЛОГА ---
    if st.session_state.current_page == "catalog":
        st.markdown("<h1 style='margin-bottom: 0px;'>🎬 Кино Room</h1>", unsafe_allow_html=True)
        st.write(f"Рады видеть тебя, {st.session_state.user_role}! Время выбрать хорошее кино.")

        st.markdown(f"""
            <div class="stats-box-new">
                <span style="font-weight: bold; font-size: 15px; color: #2B2B2B;">📊 Прогресс просмотра:</span> 
                <span style="color: #E50914; font-weight: 800; font-size: 15px; margin-left: 5px;">🎬 Просмотрено {user_watched} из {total_movies} тайтлов</span>
            </div>
        """, unsafe_allow_html=True)

        # --- ФИЛЬТРЫ И РАНДОМ ---
        st.write("---")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            filter_cat = st.selectbox("Тип:", ["Все", "Фильм", "Сериал", "Мультфильм"])
        with f_col2:
            all_genres = list(set([m.get("genre", "Без жанра") for m in movies_list]))
            filter_genre = st.selectbox("Жанр:", ["Все"] + all_genres)

        filtered_movies = movies_list
        if filter_cat != "Все":
            filtered_movies = [m for m in filtered_movies if m["category"] == filter_cat]
        if filter_genre != "Все":
            filtered_movies = [m for m in filtered_movies if m.get("genre") == filter_genre]

        st.markdown("### 🎲 Рандомайзер")
        if st.button("✨ Сёма, выбери за меня!", use_container_width=True):
            unwatched_movies = [m for m in filtered_movies if m["id"] not in user_watched_ids]
            if unwatched_movies:
                st.session_state.random_movie = random.choice(unwatched_movies)
            else:
                st.session_state.random_movie = "empty"

        if st.session_state.random_movie:
            if st.session_state.random_movie == "empty":
                st.info("Ты посмотрела вообще всё по этим фильтрам! Семён, пора добавить новинок!")
            else:
                rm = st.session_state.random_movie
                st.markdown(f"""
                    <div style="background-color: #FFF; border: 2px solid #E50914; padding: 15px; border-radius: 8px; margin-top: 10px; display: flex; gap: 15px; align-items: center;">
                        <img src="{rm['poster_url']}" style="width: 80px; height: 120px; object-fit: cover; border-radius: 4px;">
                        <div>
                            <h4 style="margin: 0; color: #E50914;">🍿 Идеальный вариант: «{rm['title']}»</h4>
                            <p style="margin: 5px 0 0 0; font-size: 14px;"><b>Категория:</b> {rm['category']} | <b>Жанр:</b> {rm.get('genre', 'Разное')}</p>
                            <p style="margin: 5px 0 0 0; font-size: 13px; color: #555;">{rm['description'][:120]}...</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🚀 Открыть «{rm['title']}»", key="open_random_btn"):
                    st.query_params["movie_id"] = rm['id'];
                    st.rerun()

        st.write("---")
        st.subheader("🍿 Наш Каталог")

        if not filtered_movies:
            st.info("Ничего не найдено по выбранным фильтрам.")
        else:
            chunks = [filtered_movies[i:i + 3] for i in range(0, len(filtered_movies), 3)]
            for chunk in chunks:
                cols = st.columns(3)
                for index, movie in enumerate(chunk):
                    with cols[index]:
                        m_status = next((a["status"] for a in actions_list if
                                         a["username"] == st.session_state.user_role and a["movie_id"] == movie["id"]),
                                        None)
                        status_badge = ""
                        if m_status == "watched":
                            status_badge = "<br><span style='background-color:#28A745; color:white; padding:2px 6px; border-radius:4px; font-size:11px;'>✅ Просмотрено</span>"
                        elif m_status == "watchlist":
                            status_badge = "<br><span style='background-color:#FFC107; color:black; padding:2px 6px; border-radius:4px; font-size:11px;'>📌 В планах</span>"

                        is_rec = movie.get("recommended", False)
                        rec_badge = "<span style='position:absolute; top:10px; right:10px; background-color:#E50914; color:white; padding:3px 8px; border-radius:20px; font-size:11px; font-weight:bold;'>🔥 Рекомендую</span>" if is_rec else ""
                        is_kk = movie["id"] in kk_movie_ids
                        kk_badge = "<span style='position:absolute; top:10px; left:10px; background-color:#6f42c1; color:white; padding:3px 8px; border-radius:20px; font-size:11px; font-weight:bold;'>🍿 КК</span>" if is_kk else ""

                        # Исправлено отображение HTML для карточки!
                        st.markdown(f"""
                            <div class="movie-card">
                                {rec_badge}
                                {kk_badge}
                                <img src="{movie['poster_url']}" style="width:100%; height:320px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:18px; text-align:center;">{movie['title']}</h3>
                                <div>
                                    <span style="background-color:#E50914; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:bold;">{movie['category']}</span>
                                    <span style="background-color:#6c757d; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:bold; margin-left:3px;">{movie.get('genre', 'Кино')}</span>
                                    {status_badge}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        if st.button(f"Открыть «{movie['title']}»", key=f"id_move_{movie['id']}",
                                     use_container_width=True):
                            st.query_params["movie_id"] = movie['id'];
                            st.rerun()

                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            if st.session_state.user_role == "Семён":
                                if is_rec:
                                    if st.button("❌ -Реком.", key=f"rem_rec_{movie['id']}", use_container_width=True):
                                        movie["recommended"] = False
                                        save_local_movie(movie);
                                        st.rerun()
                                else:
                                    if st.button("🔥 +Реком.", key=f"add_rec_{movie['id']}", use_container_width=True):
                                        movie["recommended"] = True
                                        save_local_movie(movie);
                                        st.rerun()
                        with btn_c2:
                            # ФИКС КНОПКИ +КК
                            if is_kk:
                                if st.button("🍿 -КК", key=f"rem_kk_{movie['id']}", use_container_width=True):
                                    save_local_action("Кристина", movie["id"], None)
                                    st.rerun()
                            else:
                                if st.button("🍿 +КК", key=f"add_kk_{movie['id']}", use_container_width=True):
                                    save_local_action("Кристина", movie["id"], "kristina_cinema")
                                    st.rerun()

        # --- ПАНЕЛЬ СЕМЁНА (АДМИНКА) ---
        if st.session_state.user_role == "Семён":
            st.write("---")
            st.markdown("### 🛠 Панель Семёна (Управление системой)")
            adm_tab1, adm_tab2, adm_tab3, adm_tab4 = st.tabs(
                ["🎬 Добавить фильм", "⚙️ Редактирование фильмов", "🧠 Создать Вопрос Квиза", "🔔 Заявки от Кристины"])

            with adm_tab1:
                with st.form("add_movie_form", clear_on_submit=True):
                    col_form1, col_form2 = st.columns(2)
                    with col_form1:
                        new_title = st.text_input("🎬 Название фильма/сериала:")
                        new_category = st.selectbox("📁 Категория:", ["Фильм", "Сериал", "Мультфильм"])
                        new_genre = st.text_input("🏷 Жанр (например: Боевик, Комедия, Драма):")
                        new_poster = st.text_input("🖼 Ссылка на картинку постера (URL):")
                    with col_form2:
                        new_trailer = st.text_input("🍿 Ссылка на трейлер (YouTube):")
                        new_description = st.text_area("📝 Краткое описание:")
                    if st.form_submit_button("Сохранить и добавить в каталог"):
                        if new_title and new_description:
                            save_local_movie({
                                "title": new_title,
                                "category": new_category,
                                "genre": new_genre if new_genre else "Кино",
                                "poster_url": new_poster if new_poster else "https://via.placeholder.com/300x450?text=Нет+постера",
                                "trailer_url": new_trailer,
                                "description": new_description,
                                "recommended": False
                            })
                            st.success(f"🎬 «{new_title}» успешно добавлен!");
                            st.rerun()
                        else:
                            st.warning("Заполни Название и Описание!")

            with adm_tab2:
                st.markdown("#### Настройка жанров и данных у добавленных фильмов")
                if not movies_list:
                    st.info("Каталог пуст.")
                else:
                    selected_edit_title = st.selectbox("Выбери фильм для редактирования:",
                                                       [m["title"] for m in movies_list])
                    edit_m = next(m for m in movies_list if m["title"] == selected_edit_title)

                    with st.form("edit_movie_form"):
                        e_title = st.text_input("Название:", value=edit_m["title"])
                        e_cat = st.selectbox("Категория:", ["Фильм", "Сериал", "Мультфильм"],
                                             index=["Фильм", "Сериал", "Мультфильм"].index(
                                                 edit_m.get("category", "Фильм")))
                        e_genre = st.text_input("Жанр:", value=edit_m.get("genre", ""))
                        e_poster = st.text_input("Ссылка на постер:", value=edit_m.get("poster_url", ""))
                        e_trailer = st.text_input("Ссылка на трейлер:", value=edit_m.get("trailer_url", ""))
                        e_desc = st.text_area("Описание:", value=edit_m.get("description", ""))

                        if st.form_submit_button("Сохранить изменения"):
                            edit_m["title"] = e_title
                            edit_m["category"] = e_cat
                            edit_m["genre"] = e_genre
                            edit_m["poster_url"] = e_poster
                            edit_m["trailer_url"] = e_trailer
                            edit_m["description"] = e_desc
                            save_local_movie(edit_m)
                            st.success("Фильм успешно обновлен!");
                            st.rerun()

            with adm_tab3:
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
                            current_quizzes = load_local_quizzes()
                            current_quizzes.append({
                                "id": len(current_quizzes) + 1,
                                "movie_id": selected_movie_obj["id"],
                                "movie_title": quiz_movie,
                                "question": q_text,
                                "options": {"А": ans_1, "Б": ans_2, "В": ans_3},
                                "correct": correct_ans
                            })
                            save_json(QUIZZES_FILE, current_quizzes)
                            st.success("🧠 Вопрос успешно добавлен!");
                            st.rerun()
                        else:
                            st.warning("Заполни все поля!")

            with adm_tab4:
                st.markdown("#### 📥 Пожелания Кристины")
                if not requests_list:
                    st.info("Пока новых заявок нет.")
                else:
                    for i, req in enumerate(requests_list):
                        col_req1, col_req2 = st.columns([3, 1])
                        with col_req1:
                            st.warning(f"🎬 **{req['title']}** (Добавь по-братски!)")
                        with col_req2:
                            if st.button("❌ Удалить", key=f"del_req_{i}"):
                                requests_list.pop(i)
                                save_json(REQUESTS_FILE, requests_list)
                                st.rerun()

    # --- РАЗДЕЛ СЕМЁН РЕКОМЕНДУЕТ ---
    elif st.session_state.current_page == "semen_recommend":
        st.markdown("<h1>🔥 Семён рекомендует</h1>", unsafe_allow_html=True)
        st.write("Специальный топчик тайтлов, подобранный Сёмой для первоочередного просмотра! 🍿")
        st.write("---")

        rec_movies = [m for m in movies_list if m.get("recommended", False)]
        if not rec_movies:
            st.info("Семён пока не добавил сюда ни одного фильма.")
        else:
            r_chunks = [rec_movies[i:i + 3] for i in range(0, len(rec_movies), 3)]
            for r_chunk in r_chunks:
                r_cols = st.columns(3)
                for r_idx, r_movie in enumerate(r_chunk):
                    with r_cols[r_idx]:
                        st.markdown(f"""
                            <div class="movie-card">
                                <img src="{r_movie['poster_url']}" style="width:100%; height:320px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:18px; text-align:center;">{r_movie['title']}</h3>
                                <div>
                                    <span style="background-color:#E50914; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:bold;">{r_movie['category']}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Открыть «{r_movie['title']}»", key=f"rec_page_btn_{r_movie['id']}",
                                     use_container_width=True):
                            st.query_params["movie_id"] = r_movie['id'];
                            st.rerun()

    # --- РАЗДЕЛ КИНОТЕАТР КРИСТИНЫ ---
    elif st.session_state.current_page == "kk_cinema":
        st.markdown("<h1>🍿 Кинотеатр Кристины</h1>", unsafe_allow_html=True)
        st.write("Особая папочка избранных фильмов Кристины!")
        st.write("---")

        kk_movies = [m for m in movies_list if m["id"] in kk_movie_ids]
        if not kk_movies:
            st.info("В папку КК пока ничего не добавлено.")
        else:
            kk_chunks = [kk_movies[i:i + 3] for i in range(0, len(kk_movies), 3)]
            for kk_chunk in kk_chunks:
                kk_cols = st.columns(3)
                for kk_idx, kk_movie in enumerate(kk_chunk):
                    with kk_cols[kk_idx]:
                        st.markdown(f"""
                            <div class="movie-card">
                                <img src="{kk_movie['poster_url']}" style="width:100%; height:320px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:18px; text-align:center;">{kk_movie['title']}</h3>
                                <div>
                                    <span style="background-color:#6f42c1; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:bold;">🍿 Кинотеатр Кристины</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Открыть «{kk_movie['title']}»", key=f"kk_page_btn_{kk_movie['id']}",
                                     use_container_width=True):
                            st.query_params["movie_id"] = kk_movie['id'];
                            st.rerun()

    # --- МОЁ ПРОСТРАНСТВО С АЧИВКАМИ ---
    elif st.session_state.current_page == "my_space":
        st.markdown(f"<h1>👤 Моё пространство: {st.session_state.user_role}</h1>", unsafe_allow_html=True)

        st.markdown(f"""
            <div class="stats-box-new">
                <span style="font-weight: bold; font-size: 15px; color: #2B2B2B;">📊 Твоя личная статистика:</span> 
                <span style="color: #28A745; font-weight: 800; font-size: 15px; margin-left: 10px;">🎬 Просмотрено: {user_watched}</span>
                <span style="color: #FFC107; font-weight: 800; font-size: 15px; margin-left: 15px;">📌 Хочу посмотреть: {user_watchlist}</span>
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.user_role == "Кристина":
            with st.form("request_movie_form", clear_on_submit=True):
                st.markdown("#### 💌 Не нашла нужного фильма в каталоге?")
                req_title = st.text_input("Напиши название фильма/сериала, и Семён добавит его на сайт:")
                if st.form_submit_button("🚀 Отправить Семёну"):
                    if req_title.strip():
                        requests_list.append({"title": req_title.strip()})
                        save_json(REQUESTS_FILE, requests_list)
                        st.success("Заявка улетела Сёме! 😉")
                    else:
                        st.warning("Введи название!")

        st.write("---")

        tab_watched, tab_watchlist, tab_ratings, tab_reviews, tab_achievements = st.tabs([
            "🎬 Просмотрено", "📌 Хочу посмотреть", "⭐️ Мои оценки", "✍️ Мои рецензии", "🏆 Мои Ачивки"
        ])

        with tab_watched:
            watched_movies = [m for m in movies_list if m["id"] in user_watched_ids]
            if not watched_movies:
                st.info("У тебя пока нет просмотренных фильмов.")
            else:
                w_chunks = [watched_movies[i:i + 3] for i in range(0, len(watched_movies), 3)]
                for w_chunk in w_chunks:
                    w_cols = st.columns(3)
                    for w_idx, w_movie in enumerate(w_chunk):
                        with w_cols[w_idx]:
                            st.markdown(f"""
                                <div class="movie-card">
                                    <img src="{w_movie['poster_url']}" style="width:100%; height:320px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                    <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:18px; text-align:center;">{w_movie['title']}</h3>
                                    <span style="background-color:#28A745; color:white; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:bold;">✅ Просмотрено</span>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button(f"Открыть фильм «{w_movie['title']}»", key=f"my_wat_{w_movie['id']}",
                                         use_container_width=True):
                                st.query_params["movie_id"] = w_movie['id'];
                                st.rerun()

        with tab_watchlist:
            wish_movies = [m for m in movies_list if m["id"] in user_watchlist_ids]
            if not wish_movies:
                st.info("Твой список 'Хочу посмотреть' пуст.")
            else:
                wl_chunks = [wish_movies[i:i + 3] for i in range(0, len(wish_movies), 3)]
                for wl_chunk in wl_chunks:
                    wl_cols = st.columns(3)
                    for wl_idx, wl_movie in enumerate(wl_chunk):
                        with wl_cols[wl_idx]:
                            st.markdown(f"""
                                <div class="movie-card">
                                    <img src="{wl_movie['poster_url']}" style="width:100%; height:320px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                    <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:18px; text-align:center;">{wl_movie['title']}</h3>
                                    <span style="background-color:#FFC107; color:black; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:bold;">📌 В планах</span>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button(f"Открыть фильм «{wl_movie['title']}»", key=f"my_wish_{wl_movie['id']}",
                                         use_container_width=True):
                                st.query_params["movie_id"] = wl_movie['id'];
                                st.rerun()

        with tab_ratings:
            user_revs = [r for r in reviews_list if r["username"] == st.session_state.user_role]
            if not user_revs:
                st.info("Оценок нет.")
            else:
                for ur in user_revs:
                    m_title = next((m["title"] for m in movies_list if m["id"] == ur["movie_id"]), "Удален")
                    v_badge = f" | Вайб: {ur['vibe']}" if "vibe" in ur and ur["vibe"] else ""
                    st.write(f"⭐️ **{ur['rating']}/10** — {m_title}{v_badge}")

        with tab_reviews:
            user_revs = [r for r in reviews_list if r["username"] == st.session_state.user_role]
            if not user_revs or len([r for r in user_revs if r["review_text"].strip()]) == 0:
                st.info("Рецензий нет.")
            else:
                for ur in user_revs:
                    if ur["review_text"].strip():
                        m_title = next((m["title"] for m in movies_list if m["id"] == ur["movie_id"]), "Удален")
                        st.markdown(f"""
                            <div class="review-box">
                                <strong>🎬 {m_title}</strong> — <span style="color:#E50914; font-weight:bold;">⭐️ {ur['rating']}/10</span>
                                <p style="margin-top:5px; margin-bottom:0px; font-style: italic;">"{ur['review_text']}"</p>
                            </div>
                        """, unsafe_allow_html=True)

        with tab_achievements:
            st.markdown("### 🏆 Достижения киномана")

            watched_movies_objs = [m for m in movies_list if m["id"] in user_watched_ids]

            cnt_watch_film = len([m for m in watched_movies_objs if m["category"] == "Фильм"])
            cnt_watch_serial = len([m for m in watched_movies_objs if m["category"] == "Сериал"])
            cnt_watch_mult = len([m for m in watched_movies_objs if m["category"] == "Мультфильм"])
            cnt_watch_total = len(watched_movies_objs)

            user_all_reviews = [r for r in reviews_list if r["username"] == st.session_state.user_role]
            rated_movie_ids = list(set([r["movie_id"] for r in user_all_reviews]))
            reviewed_movie_ids = list(set([r["movie_id"] for r in user_all_reviews if r["review_text"].strip()]))

            rated_objs = [m for m in movies_list if m["id"] in rated_movie_ids]
            cnt_rate_film = len([m for m in rated_objs if m["category"] == "Фильм"])
            cnt_rate_serial = len([m for m in rated_objs if m["category"] == "Сериал"])
            cnt_rate_mult = len([m for m in rated_objs if m["category"] == "Мультфильм"])
            cnt_rate_total = len(rated_objs)

            reviewed_objs = [m for m in movies_list if m["id"] in reviewed_movie_ids]
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
                {"target": 10, "cur": cnt_watch_film, "name": "«Смотрю лучше, чем сплю»",
                 "desc": "Посмотреть 10 фильмов", "emoji": "☕️"},
                {"target": 1, "cur": cnt_watch_serial, "name": "«Пилотный эпизод»", "desc": "Посмотреть 1 сериал",
                 "emoji": "📺"},
                {"target": 5, "cur": cnt_watch_serial, "name": "Марафонец сезонов", "desc": "Посмотреть 5 сериалов",
                 "emoji": "🏃‍♀️"},
                {"target": 1, "cur": cnt_watch_mult, "name": "Возвращение в детство", "desc": "Посмотреть 1 мультфильм",
                 "emoji": "🧸"},
                {"target": 5, "cur": cnt_watch_total, "name": "«Киномарафонец»", "desc": "Посмотреть 5 тайтлов",
                 "emoji": "🧭"},
                {"target": 1, "cur": cnt_rate_film, "name": "«Первый вердикт»", "desc": "Оценить 1 фильм",
                 "emoji": "⚖️"},
                {"target": 1, "cur": cnt_rev_film, "name": "«Первое слово»", "desc": "Написать рецензию на 1 фильм",
                 "emoji": "✏️"}
            ]

            ach_sub_tab1, ach_sub_tab2 = st.tabs(["🎉 Полученные", "🌐 Все ачивки"])

            with ach_sub_tab1:
                earned_any = False
                for ach in achievements_config:
                    if ach["cur"] >= ach["target"]:
                        earned_any = True
                        st.markdown(f"""
                            <div class="achievement-card earned">
                                <h4 style="margin:0; color:#28A745;">{ach['emoji']} {ach['name']} <span style="font-size:12px; font-weight:normal;">[ПОЛУЧЕНО]</span></h4>
                                <p style="margin:5px 0 0 0; font-size:14px; color:#555;">{ach['desc']} (Выполнено: {ach['cur']}/{ach['target']})</p>
                            </div>
                        """, unsafe_allow_html=True)
                if not earned_any:
                    st.info("У тебя пока нет полученных ачивок. Время посмотреть первый фильм!")

            with ach_sub_tab2:
                for ach in achievements_config:
                    is_earned = ach["cur"] >= ach["target"]
                    progress = min(ach["cur"] / ach["target"], 1.0)

                    if is_earned:
                        st.markdown(f"""
                            <div class="achievement-card earned">
                                <h4 style="margin:0; color:#28A745;">{ach['emoji']} {ach['name']} <span style="font-size:12px; font-weight:normal;">[ПОЛУЧЕНО]</span></h4>
                                <p style="margin:5px 0 0 0; font-size:14px; color:#555;">{ach['desc']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class="achievement-card">
                                <h4 style="margin:0; color:#2B2B2B;">{ach['emoji']} {ach['name']}</h4>
                                <p style="margin:5px 0 0 0; font-size:14px; color:#666;">{ach['desc']} — Прогресс: <b>{ach['cur']}</b> из <b>{ach['target']}</b></p>
                            </div>
                        """, unsafe_allow_html=True)
                    st.progress(progress)

    # --- СТРАНИЦА ПРОСМОТРА КАРТОЧКИ ФИЛЬМА ---
    if st.session_state.current_page == "movie_view" and st.session_state.selected_movie_id is not None:
        movie = next((m for m in movies_list if m["id"] == st.session_state.selected_movie_id), None)

        if movie:
            if st.button("⬅️ НАЗАД В КАТАЛОГ ФИЛЬМОВ", use_container_width=True):
                st.query_params.clear();
                st.rerun()

            st.write("---")
            st.markdown(f"<h1>🎬 {movie['title']}</h1>", unsafe_allow_html=True)
            st.write("")

            col_view1, col_view2 = st.columns([1, 2])
            with col_view1:
                st.image(movie['poster_url'], use_container_width=True)
            with col_view2:
                st.markdown("### 📝 Описание фильма")
                st.write(movie['description'])
                st.write(f"**Категория:** {movie.get('category', 'Фильм')} | **Жанр:** {movie.get('genre', 'Кино')}")
                st.write("---")

                st.markdown("### 🎯 Твой статус фильма")
                current_status = next((a["status"] for a in actions_list if
                                       a["username"] == st.session_state.user_role and a["movie_id"] == movie["id"]),
                                      None)

                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if current_status == "watched":
                        st.success("✅ Просмотрено тобой")
                    else:
                        if st.button("🎬 Отметить просмотренным", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], "watched");
                            st.rerun()
                with col_btn2:
                    if current_status == "watchlist":
                        st.warning("📌 В планах на просмотр")
                    else:
                        if st.button("📌 Хочу посмотреть", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], "watchlist");
                            st.rerun()
                with col_btn3:
                    if current_status:
                        if st.button("❌ Сбросить статус", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], None);
                            st.rerun()

                st.write("---")
                if movie.get('trailer_url'):
                    st.markdown(f"### 🍿 [Смотреть трейлер на YouTube]({movie['trailer_url']})")
                    if "youtube.com" in movie['trailer_url'] or "youtu.be" in movie['trailer_url']:
                        st.video(movie['trailer_url'])
                else:
                    st.info("Трейлер к этому фильму не добавлен.")

            st.write("---")

            # --- БЛОК ОТЗЫВОВ И РЕЦЕНЗИЙ ---
            st.markdown(f"### ✍️ Оставить рецензию на фильм «{movie['title']}»")

            rating = st.slider("Выбери оценку на шкале:", min_value=1, max_value=10, value=5)
            st.markdown(f"## 📈 Твоя оценка: <span style='color:#E50914; font-weight:900;'>⭐️ {rating} / 10</span>",
                        unsafe_allow_html=True)

            st.markdown("### 🌡️ Вайбометр")
            vibe_options = ["🥱 Выдержала до титров", "😢 Поплакала", "🌀 Ничего не поняла, но очень интересно",
                            "🔥 Полный треш", "✨ Вайбик"]
            selected_vibe = st.radio("Какое настроение оставил фильм?", vibe_options, horizontal=True)

            review_text = st.text_area("Напиши свои впечатления:")

            if st.button("Сохранить отзыв и оценку", use_container_width=True):
                save_local_review({"movie_id": movie["id"], "username": st.session_state.user_role, "rating": rating,
                                   "vibe": selected_vibe, "review_text": review_text})
                save_local_action(st.session_state.user_role, movie["id"], "watched")
                st.success("Рецензия успешно сохранена!");
                st.rerun()

            # --- ТЕСТЫ ПОД ОТЗЫВАМИ В КАРТОЧКЕ ФИЛЬМА ---
            movie_quizzes = [q for q in quizzes_list if q["movie_id"] == movie["id"]]
            if movie_quizzes:
                st.write("---")
                st.markdown("### 🧠 Мини-тесты от Семёна по этому фильму:")

                for idx, mq in enumerate(movie_quizzes):
                    passed_mq = next((r for r in quiz_results if
                                      r["username"] == st.session_state.user_role and r["quiz_id"] == mq["id"]), None)

                    st.markdown(f"""
                        <div class="quiz-single-box">
                            <span style="color:#E50914; font-weight:bold;">Вопрос #{idx + 1}:</span> {mq['question']}
                        </div>
                    """, unsafe_allow_html=True)

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
                            quiz_results.append({
                                "username": st.session_state.user_role,
                                "quiz_id": mq["id"],
                                "user_answer": user_ans_mq[0],
                                "is_correct": (user_ans_mq[0] == mq["correct"])
                            })
                            save_json(QUIZ_RESULTS_FILE, quiz_results)
                            st.rerun()

            st.write("---")
            st.markdown("### 💬 Рецензии зрителей")
            movie_reviews = [r for r in reviews_list if r["movie_id"] == movie["id"]]

            if not movie_reviews:
                st.info("Отзывов пока нет.")
            else:
                for rev in movie_reviews:
                    vibe_str = f" | Настроение: <b>{rev['vibe']}</b>" if "vibe" in rev else ""
                    st.markdown(f"""
                        <div class="review-box">
                            <strong>👤 {rev['username']}</strong> — <span style="color:#E50914; font-weight:bold;">⭐️ {rev['rating']}/10</span> {vibe_str}
                            <p style="margin-top:5px; margin-bottom:0px; color:#444!important;">{rev['review_text']}</p>
                        </div>
                    """, unsafe_allow_html=True)

    # --- ФУТЕР ---
    st.write("---")
    st.markdown("""
        <div style="text-align: center; color: #777777; font-size: 14px; margin-top: 10px; margin-bottom: 20px;">
            💡 Есть вопросы, пожелания или что-то не работает?<br>
            Пиши администратору: 
            <a href="https://t.me/SemenMag" target="_blank" style="color: #E50914; font-weight: bold; text-decoration: none;">
                @SemenMag 🚀
            </a>
        </div>
    """, unsafe_allow_html=True)
