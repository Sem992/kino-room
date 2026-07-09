import streamlit as st
import random
from supabase import create_client, Client

# 1. Настройка страницы
st.set_page_config(
    page_title="Кино Room",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 🔑 ПОДКЛЮЧЕНИЕ К SUPABASE
# Замени 'ТВОЙ_URL_ИЗ_ШАГА_3' и 'ТВОЙ_KEY_ИЗ_ШАГА_3' на свои!
# =========================================================
SUPABASE_URL = "https://cmlxeafxjgjsaotzkwbn.supabase.co"
SUPABASE_KEY = "sb_publishable_cS46YQuO8d64KEQlS2PnHg__qFLdFcb"


@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase()


# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ SUPABASE ---
def load_local_movies():
    res = supabase.table("movies").select("*").order("id").execute()
    return res.data if res.data else []


def load_local_reviews():
    res = supabase.table("reviews").select("*").execute()
    return res.data if res.data else []


def load_local_actions():
    res = supabase.table("user_actions").select("*").execute()
    return res.data if res.data else []


def load_local_quizzes():
    res = supabase.table("quizzes").select("*").execute()
    return res.data if res.data else []


def load_local_quiz_results():
    res = supabase.table("quiz_results").select("*").execute()
    return res.data if res.data else []


def load_local_requests():
    res = supabase.table("requests").select("*").execute()
    return res.data if res.data else []


def save_local_movie(movie_data):
    supabase.table("movies").insert(movie_data).execute()


def save_local_review(review_data):
    supabase.table("reviews").insert(review_data).execute()


def save_local_action(username, movie_id, status):
    # Удаляем старый статус, если он был
    supabase.table("user_actions").delete().eq("username", username).eq("movie_id", movie_id).execute()
    if status:
        # Пишем новый
        supabase.table("user_actions").insert({"username": username, "movie_id": movie_id, "status": status}).execute()


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

# 2. Кастомный CSS стиль
st.markdown("""
    <style>
    .stApp { background-color: #FAFAFA; color: #2B2B2B; }
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }

    div.stButton > button {
        background-color: #E50914 !important; color: #FFFFFF !important;
        border: none !important; border-radius: 8px !important;
        padding: 10px 20px !important; font-weight: 900 !important;
        font-size: 15px !important; transition: 0.2s !important;
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

    .movie-card {
        background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px;
        padding: 15px; text-align: center; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05); transition: 0.3s;
        margin-bottom: 10px; position: relative;
    }
    .movie-card:hover {
        border-color: #E50914; box-shadow: 0px 6px 15px rgba(229, 9, 20, 0.15); transform: translateY(-2px);
    }

    .review-box { background-color: #FFFFFF; border-left: 5px solid #E50914; padding: 12px; border-radius: 4px; margin-bottom: 10px; }
    .stats-box-new { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-left: 5px solid #E50914; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 2px 5px rgba(0,0,0,0.05); }
    .quiz-single-box { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
    .achievement-card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 10px; padding: 15px; margin-bottom: 12px; box-shadow: 0px 2px 4px rgba(0,0,0,0.02); }
    .achievement-card.earned { border: 1px solid #28A745; background-color: #F4FBF6; }
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

    with st.sidebar:
        st.markdown(f"### 👤 Профиль: **{st.session_state.user_role}**")
        st.write("---")

        page = st.radio("🧭 Навигация по сайту:", ["🏠 Главный каталог", "🔥 Семён рекомендует", "👤 Моё Пространство"])
        if page == "🏠 Главный каталог":
            st.session_state.nav_page = "catalog"
        elif page == "🔥 Семён рекомендует":
            st.session_state.nav_page = "semen_recommend"
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

        st.write("---")
        st.markdown("### 🎲 Не знаешь что глянуть?")
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            random_filter = st.selectbox("Категория рандома:", ["Всё", "Фильм", "Сериал", "Мультфильм"])
        with col_r2:
            st.write(" ")
            if st.button("✨ Сёма, выбери за меня!", use_container_width=True):
                unwatched_movies = [m for m in movies_list if m["id"] not in user_watched_ids]
                if random_filter != "Всё":
                    unwatched_movies = [m for m in unwatched_movies if m["category"] == random_filter]

                if unwatched_movies:
                    st.session_state.random_movie = random.choice(unwatched_movies)
                else:
                    st.session_state.random_movie = "empty"

        if st.session_state.random_movie:
            if st.session_state.random_movie == "empty":
                st.info("Ты посмотрела вообще всё в этой категории! Семён, пора добавить новинок!")
            else:
                rm = st.session_state.random_movie
                st.markdown(f"""
                    <div style="background-color: #FFF; border: 2px solid #E50914; padding: 15px; border-radius: 8px; margin-top: 10px; display: flex; gap: 15px; align-items: center;">
                        <img src="{rm['poster_url']}" style="width: 80px; max-height: 120px; object-fit: cover; border-radius: 4px;">
                        <div>
                            <h4 style="margin: 0; color: #E50914;">🍿 Идеальный вариант для тебя: «{rm['title']}»</h4>
                            <p style="margin: 5px 0 0 0; font-size: 14px;"><b>Категория:</b> {rm['category']} | {rm['description'][:150]}...</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🚀 Открыть «{rm['title']}»", key="open_random_btn"):
                    st.query_params["movie_id"] = rm['id'];
                    st.rerun()

        st.write("---")
        st.subheader("🍿 Наш Каталог")

        if not movies_list:
            st.info("Каталог пока пуст.")
        else:
            chunks = [movies_list[i:i + 3] for i in range(0, len(movies_list), 3)]
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

                        st.markdown(f"""
                            <div class="movie-card">
                                {rec_badge}
                                <img src="{movie['poster_url']}" style="width:100%; max-height:380px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:20px; text-align:center;">{movie['title']}</h3>
                                <span style="background-color:#E50914; color:white; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:bold;">{movie['category']}</span>
                                {status_badge}
                            </div>
                        """, unsafe_allow_html=True)

                        if st.button(f"Открыть «{movie['title']}»", key=f"id_move_{movie['id']}",
                                     use_container_width=True):
                            st.query_params["movie_id"] = movie['id'];
                            st.rerun()

                        if st.session_state.user_role == "Семён":
                            if is_rec:
                                if st.button("❌ Убрать из рекомендаций", key=f"rem_rec_{movie['id']}",
                                             use_container_width=True):
                                    supabase.table("movies").update({"recommended": False}).eq("id",
                                                                                               movie["id"]).execute()
                                    st.rerun()
                            else:
                                if st.button("⭐️ Сделать рекомендованным", key=f"add_rec_{movie['id']}",
                                             use_container_width=True):
                                    supabase.table("movies").update({"recommended": True}).eq("id",
                                                                                              movie["id"]).execute()
                                    st.rerun()

        # --- ПАНЕЛЬ СЕМЁНА ---
        if st.session_state.user_role == "Семён":
            st.write("---")
            st.markdown("### 🛠 Панель Семёна (Управление системой)")
            adm_tab1, adm_tab2, adm_tab3 = st.tabs(
                ["🎬 Добавить фильм", "🧠 Создать Вопрос Квиза", "🔔 Заявки от Кристины"])

            with adm_tab1:
                with st.form("add_movie_form", clear_on_submit=True):
                    col_form1, col_form2 = st.columns(2)
                    with col_form1:
                        new_title = st.text_input("🎬 Название фильма/сериала:")
                        new_category = st.selectbox("📁 Категория:", ["Фильм", "Сериал", "Мультфильм"])
                        new_poster = st.text_input("🖼 Ссылка на картинку постера (URL):")
                    with col_form2:
                        new_trailer = st.text_input("🍿 Ссылка на трейлер (YouTube):")
                        new_description = st.text_area("📝 Краткое описание:")
                    if st.form_submit_button("Сохранить и добавить в каталог"):
                        if new_title and new_description:
                            save_local_movie({"title": new_title, "category": new_category,
                                              "poster_url": new_poster if new_poster else "https://via.placeholder.com/300x450?text=Нет+постера",
                                              "trailer_url": new_trailer, "description": new_description,
                                              "recommended": False})
                            st.success(f"🎬 «{new_title}» успешно добавлен!");
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
                            supabase.table("quizzes").insert({
                                "movie_id": selected_movie_obj["id"],
                                "movie_title": quiz_movie,
                                "question": q_text,
                                "options": {"А": ans_1, "Б": ans_2, "В": ans_3},
                                "correct": correct_ans
                            }).execute()
                            st.success("🧠 Вопрос успешно добавлен к тесту!");
                            st.rerun()
                        else:
                            st.warning("Заполни все поля!")

            with adm_tab3:
                st.markdown("#### 📥 Пожелания Кристины")
                if not requests_list:
                    st.info("Пока новых заявок нет.")
                else:
                    for i, req in enumerate(requests_list):
                        col_req1, col_req2 = st.columns([3, 1])
                        with col_req1:
                            st.warning(f"🎬 **{req['title']}**")
                        with col_req2:
                            if st.button("❌ Удалить из списка", key=f"del_req_{req['id']}"):
                                supabase.table("requests").delete().eq("id", req["id"]).execute()
                                st.rerun()

    # --- РАЗДЕЛ СЕМЁН РЕКОМЕНДУЕТ ---
    elif st.session_state.current_page == "semen_recommend":
        st.markdown("<h1>🔥 Семён рекомендует</h1>", unsafe_allow_html=True)
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
                        m_status = next((a["status"] for a in actions_list if
                                         a["username"] == st.session_state.user_role and a["movie_id"] == r_movie[
                                             "id"]), None)
                        status_badge = ""
                        if m_status == "watched":
                            status_badge = "<br><span style='background-color:#28A745; color:white; padding:2px 6px; border-radius:4px; font-size:11px;'>✅ Просмотрено</span>"
                        elif m_status == "watchlist":
                            status_badge = "<br><span style='background-color:#FFC107; color:black; padding:2px 6px; border-radius:4px; font-size:11px;'>📌 В планах</span>"

                        st.markdown(f"""
                            <div class="movie-card">
                                <img src="{r_movie['poster_url']}" style="width:100%; max-height:380px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:20px; text-align:center;">{r_movie['title']}</h3>
                                <span style="background-color:#E50914; color:white; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:bold;">{r_movie['category']}</span>
                                {status_badge}
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Открыть «{r_movie['title']}»", key=f"rec_page_btn_{r_movie['id']}",
                                     use_container_width=True):
                            st.query_params["movie_id"] = r_movie['id'];
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
                        supabase.table("requests").insert({"title": req_title.strip()}).execute()
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
                                    <img src="{w_movie['poster_url']}" style="width:100%; max-height:380px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                    <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:20px; text-align:center;">{w_movie['title']}</h3>
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
                                    <img src="{wl_movie['poster_url']}" style="width:100%; max-height:380px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                    <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:20px; text-align:center;">{wl_movie['title']}</h3>
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

            # РАСЧЕТ СТАТИСТИКИ
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
                # --- ПОСМОТРЕТЬ ФИЛЬМЫ ---
                {"target": 1, "cur": cnt_watch_film, "name": "Первый сеанс", "desc": "Посмотреть 1 фильм", "emoji": "🎥"},
                {"target": 3, "cur": cnt_watch_film, "name": "Зритель с дивана", "desc": "Посмотреть 3 фильма", "emoji": "🛋️"},
                {"target": 5, "cur": cnt_watch_film, "name": "Разогрев проектора", "desc": "Посмотреть 5 фильмов", "emoji": "📽️"},
                {"target": 7, "cur": cnt_watch_film, "name": "Вошла во вкус", "desc": "Посмотреть 7 фильмов", "emoji": "😋"},
                {"target": 10, "cur": cnt_watch_film, "name": "Смотрю лучше, чем сплю", "desc": "Посмотреть 10 фильмов", "emoji": "🍿"},
                {"target": 15, "cur": cnt_watch_film, "name": "Постоянный зритель", "desc": "Посмотреть 15 фильмов", "emoji": "🎟️"},
                {"target": 20, "cur": cnt_watch_film, "name": "Золотая коллекция", "desc": "Посмотреть 20 фильмов", "emoji": "🏆"},
                {"target": 25, "cur": cnt_watch_film, "name": "Хранитель попкорна", "desc": "Посмотреть 25 фильмов", "emoji": "🍿"},
                {"target": 30, "cur": cnt_watch_film, "name": "Легенда кинозала", "desc": "Посмотреть 30 фильмов", "emoji": "👑"},

                # --- ПОСМОТРЕТЬ СЕРИАЛЫ ---
                {"target": 1, "cur": cnt_watch_serial, "name": "Пилотный эпизод", "desc": "Посмотреть 1 сериал", "emoji": "📺"},
                {"target": 3, "cur": cnt_watch_serial, "name": "Ещё одну и спать", "desc": "Посмотреть 3 сериала", "emoji": "🥱"},
                {"target": 5, "cur": cnt_watch_serial, "name": "Марафонец сезонов", "desc": "Посмотреть 5 сериалов", "emoji": "🏃‍♂️"},
                {"target": 7, "cur": cnt_watch_serial, "name": "Втянулся", "desc": "Посмотреть 7 сериалов", "emoji": "👀"},
                {"target": 10, "cur": cnt_watch_serial, "name": "Спонсор бессонницы", "desc": "Посмотреть 10 сериалов", "emoji": "☕"},
                {"target": 15, "cur": cnt_watch_serial, "name": "Королева сезонов", "desc": "Посмотреть 15 сериалов", "emoji": "👑"},

                # --- ПОСМОТРЕТЬ МУЛЬТФИЛЬМЫ ---
                {"target": 1, "cur": cnt_watch_mult, "name": "Возвращение в детство", "desc": "Посмотреть 1 мультфильм", "emoji": "🧸"},
                {"target": 3, "cur": cnt_watch_mult, "name": "Друг мультгероев", "desc": "Посмотреть 3 мультфильма", "emoji": "🎈"},
                {"target": 5, "cur": cnt_watch_mult, "name": "Любитель анимации", "desc": "Посмотреть 5 мультфильмов", "emoji": "🎨"},
                {"target": 7, "cur": cnt_watch_mult, "name": "Мультяшный фанат", "desc": "Посмотреть 7 мультфильмов", "emoji": "🍕"},
                {"target": 10, "cur": cnt_watch_mult, "name": "2D и 3D эксперт", "desc": "Посмотреть 10 мультфильмов", "emoji": "👓"},
                {"target": 15, "cur": cnt_watch_mult, "name": "Фанат Диснея", "desc": "Посмотреть 15 мультфильмов", "emoji": "🏰"},
                {"target": 20, "cur": cnt_watch_mult, "name": "Анимания", "desc": "Посмотреть 20 мультфильмов", "emoji": "🎡"},
                {"target": 25, "cur": cnt_watch_mult, "name": "Мультяшный эксперт", "desc": "Посмотреть 25 мультфильмов", "emoji": "🔮"},
                {"target": 30, "cur": cnt_watch_mult, "name": "Повелитель рисовки", "desc": "Посмотреть 30 мультфильмов", "emoji": "🪄"},

                # --- ПОСМОТРЕТЬ ТАЙТЛЫ (ВСЕГО) ---
                {"target": 5, "cur": cnt_watch_total, "name": "Киномарафонец", "desc": "Посмотреть 5 тайтлов всего", "emoji": "🧭"},
                {"target": 7, "cur": cnt_watch_total, "name": "Кинолюбитель", "desc": "Посмотреть 7 тайтлов всего", "emoji": "❤️"},
                {"target": 10, "cur": cnt_watch_total, "name": "Кинопутешественник", "desc": "Посмотреть 10 тайтлов всего", "emoji": "🌍"},
                {"target": 15, "cur": cnt_watch_total, "name": "Почетный гость Кинозала", "desc": "Посмотреть 15 тайтлов всего", "emoji": "🥂"},
                {"target": 20, "cur": cnt_watch_total, "name": "Хранитель пульта", "desc": "Посмотреть 20 тайтлов всего", "emoji": "🎮"},
                {"target": 25, "cur": cnt_watch_total, "name": "Друг режиссёра", "desc": "Посмотреть 25 тайтлов всего", "emoji": "🎬"},
                {"target": 30, "cur": cnt_watch_total, "name": "Хранитель кадров", "desc": "Посмотреть 30 тайтлов всего", "emoji": "🎞️"},
                {"target": 35, "cur": cnt_watch_total, "name": "Амбассадор Кинопоиска", "desc": "Посмотреть 35 тайтлов всего", "emoji": "🦊"},
                {"target": 40, "cur": cnt_watch_total, "name": "Покоритель экранов", "desc": "Посмотреть 40 тайтлов всего", "emoji": "🚀"},
                {"target": 45, "cur": cnt_watch_total, "name": "Легенда просмотра", "desc": "Посмотреть 45 тайтлов всего", "emoji": "🌟"},
                {"target": 50, "cur": cnt_watch_total, "name": "Живёт в кинозале", "desc": "Посмотреть 50 тайтлов всего", "emoji": "🏠"},
                {"target": 55, "cur": cnt_watch_total, "name": "Спилберг нервно курит", "desc": "Посмотреть 55 тайтлов всего", "emoji": "🚬"},
                {"target": 60, "cur": cnt_watch_total, "name": "Властелин тайтлов", "desc": "Посмотреть 60 тайтлов всего", "emoji": "🌋"},

                # --- ОЦЕНИТЬ ФИЛЬМЫ ---
                {"target": 1, "cur": cnt_rate_film, "name": "Первый вердикт", "desc": "Оценить 1 фильм", "emoji": "⚖️"},
                {"target": 3, "cur": cnt_rate_film, "name": "Уже есть мнение", "desc": "Оценить 3 фильма", "emoji": "💬"},
                {"target": 5, "cur": cnt_rate_film, "name": "Оценщик кадров", "desc": "Оценить 5 фильмов", "emoji": "🔎"},
                {"target": 7, "cur": cnt_rate_film, "name": "Член жюри", "desc": "Оценить 7 фильмов", "emoji": "👔"},
                {"target": 10, "cur": cnt_rate_film, "name": "Судья кинозала", "desc": "Оценить 10 фильмов", "emoji": "👨‍⚖️"},
                {"target": 15, "cur": cnt_rate_film, "name": "Раздающий звезды", "desc": "Оценить 15 фильмов", "emoji": "✨"},
                {"target": 20, "cur": cnt_rate_film, "name": "Мастер рейтингов", "desc": "Оценить 20 фильмов", "emoji": "📊"},
                {"target": 25, "cur": cnt_rate_film, "name": "Кинокритик", "desc": "Оценить 25 фильмов", "emoji": "📰"},
                {"target": 30, "cur": cnt_rate_film, "name": "Властелин тайтлов", "desc": "Оценить 30 фильмов", "emoji": "🔮"},

                # --- ОЦЕНИТЬ СЕРИАЛЫ ---
                {"target": 1, "cur": cnt_rate_serial, "name": "Первый вердикт (Сериалы)", "desc": "Оценить 1 сериал", "emoji": "📝"},
                {"target": 3, "cur": cnt_rate_serial, "name": "Сверхзритель", "desc": "Оценить 3 сериала", "emoji": "⚡"},
                {"target": 5, "cur": cnt_rate_serial, "name": "Звездный марафон", "desc": "Оценить 5 сериалов", "emoji": "🌠"},
                {"target": 7, "cur": cnt_rate_serial, "name": "Оценщик сезонов", "desc": "Оценить 7 сериалов", "emoji": "🍂"},
                {"target": 10, "cur": cnt_rate_serial, "name": "Знаток сериалов", "desc": "Оценить 10 сериалов", "emoji": "🎓"},
                {"target": 15, "cur": cnt_rate_serial, "name": "Судья Netflix", "desc": "Оценить 15 сериалов", "emoji": "🔴"},

                # --- ОЦЕНИТЬ МУЛЬТФИЛЬМЫ ---
                {"target": 1, "cur": cnt_rate_mult, "name": "Первое мнение", "desc": "Оценить 1 мультфильм", "emoji": "👶"},
                {"target": 3, "cur": cnt_rate_mult, "name": "Добрый критик", "desc": "Оценить 3 мультфильма", "emoji": "😇"},
                {"target": 5, "cur": cnt_rate_mult, "name": "Звездочет мультяшек", "desc": "Оценить 5 мультфильмов", "emoji": "🔭"},
                {"target": 7, "cur": cnt_rate_mult, "name": "Анимационное жюри", "desc": "Оценить 7 мультфильмов", "emoji": "🎪"},
                {"target": 10, "cur": cnt_rate_mult, "name": "Знаток анимации", "desc": "Оценить 10 мультфильмов", "emoji": "📚"},
                {"target": 15, "cur": cnt_rate_mult, "name": "Мульткритик", "desc": "Оценить 15 мультфильмов", "emoji": "🦹"},
                {"target": 20, "cur": cnt_rate_mult, "name": "Раздающий лайки", "desc": "Оценить 20 мультфильмов", "emoji": "👍"},
                {"target": 25, "cur": cnt_rate_mult, "name": "Строгий, но справедливый", "desc": "Оценить 25 мультфильмов", "emoji": "📐"},
                {"target": 30, "cur": cnt_rate_mult, "name": "Легендарный судья анимации", "desc": "Оценить 30 мультфильмов", "emoji": "🏛️"},

                # --- ОЦЕНИТЬ ТАЙТЛЫ (ВСЕГО) ---
                {"target": 5, "cur": cnt_rate_total, "name": "Младший оценщик", "desc": "Оценить 5 тайтлов всего", "emoji": "🐣"},
                {"target": 7, "cur": cnt_rate_total, "name": "Есть что сказать", "desc": "Оценить 7 тайтлов всего", "emoji": "🗣️"},
                {"target": 10, "cur": cnt_rate_total, "name": "Уверенный критик", "desc": "Оценить 10 тайтлов всего", "emoji": "😎"},
                {"target": 15, "cur": cnt_rate_total, "name": "Формирователь вкуса", "desc": "Оценить 15 тайтлов всего", "emoji": "🍷"},
                {"target": 20, "cur": cnt_rate_total, "name": "Куратор рейтингов", "desc": "Оценить 20 тайтлов всего", "emoji": "🗂️"},
                {"target": 25, "cur": cnt_rate_total, "name": "Эксперт впечатлений", "desc": "Оценить 25 тайтлов всего", "emoji": "🗺️"},
                {"target": 30, "cur": cnt_rate_total, "name": "Неподкупное жюри", "desc": "Оценить 30 тайтлов всего", "emoji": "🔒"},
                {"target": 35, "cur": cnt_rate_total, "name": "Профи оценок", "desc": "Оценить 35 тайтлов всего", "emoji": "💎"},
                {"target": 40, "cur": cnt_rate_total, "name": "Мастер вкуса", "desc": "Оценить 40 тайтлов всего", "emoji": "👑"},
                {"target": 45, "cur": cnt_rate_total, "name": "Энциклопедия оценок", "desc": "Оценить 45 тайтлов всего", "emoji": "📖"},
                {"target": 50, "cur": cnt_rate_total, "name": "Абсолютный авторитет", "desc": "Оценить 50 тайтлов всего", "emoji": "🔱"},
                {"target": 55, "cur": cnt_rate_total, "name": "Министерство культуры", "desc": "Оценить 55 тайтлов всего", "emoji": "🏛️"},
                {"target": 60, "cur": cnt_rate_total, "name": "Верховный суд тайтлов", "desc": "Оценить 60 тайтлов всего", "emoji": "⚖️"},

                # --- НАПИСАТЬ РЕЦЕНЗИЮ НА ФИЛЬМЫ ---
                {"target": 1, "cur": cnt_rev_film, "name": "Первое слово", "desc": "Написать рецензию на 1 фильм", "emoji": "✍️"},
                {"target": 3, "cur": cnt_rev_film, "name": "Критик-любитель", "desc": "Написать рецензию на 3 фильма", "emoji": "📒"},
                {"target": 5, "cur": cnt_rev_film, "name": "Вдумчивый зритель", "desc": "Написать рецензию на 5 фильмов", "emoji": "🤔"},
                {"target": 7, "cur": cnt_rev_film, "name": "Мастер слова", "desc": "Написать рецензию на 7 фильмов", "emoji": "✒️"},
                {"target": 10, "cur": cnt_rev_film, "name": "Независимый эксперт", "desc": "Написать рецензию на 10 фильмов", "emoji": "🦅"},
                {"target": 15, "cur": cnt_rev_film, "name": "Голос кинозала", "desc": "Написать рецензию на 15 фильмов", "emoji": "📢"},
                {"target": 20, "cur": cnt_rev_film, "name": "Острое перо", "desc": "Написать рецензию на 20 фильмов", "emoji": "🪶"},
                {"target": 25, "cur": cnt_rev_film, "name": "Голос народа", "desc": "Написать рецензию на 25 фильмов", "emoji": "👥"},
                {"target": 30, "cur": cnt_rev_film, "name": "Гений мысли", "desc": "Написать рецензию на 30 фильмов", "emoji": "🧠"},

                # --- НАПИСАТЬ РЕЦЕНЗИЮ НА СЕРИАЛЫ ---
                {"target": 1, "cur": cnt_rev_serial, "name": "Первая заметка", "desc": "Написать рецензию на 1 сериал", "emoji": "📌"},
                {"target": 3, "cur": cnt_rev_serial, "name": "Обзорщик сезонов", "desc": "Написать рецензию на 3 сериала", "emoji": "🍁"},
                {"target": 5, "cur": cnt_rev_serial, "name": "Автор теорий", "desc": "Написать рецензию на 5 сериалов", "emoji": "💡"},
                {"target": 7, "cur": cnt_rev_serial, "name": "Летописец сериалов", "desc": "Написать рецензию на 7 сериалов", "emoji": "📜"},
                {"target": 10, "cur": cnt_rev_serial, "name": "Ловец деталей", "desc": "Написать рецензию на 10 сериалов", "emoji": "🔍"},
                {"target": 15, "cur": cnt_rev_serial, "name": "Повелитель обзоров", "desc": "Написать рецензию на 15 сериалов", "emoji": "👑"},

                # --- НАПИСАТЬ РЕЦЕНЗИЮ НА МУЛЬТФИЛЬМЫ ---
                {"target": 1, "cur": cnt_rev_mult, "name": "Первое впечатление", "desc": "Написать рецензию на 1 мультфильм", "emoji": "🍿"},
                {"target": 3, "cur": cnt_rev_mult, "name": "Автор волшебных строк", "desc": "Написать рецензию на 3 мультфильма", "emoji": "✨"},
                {"target": 5, "cur": cnt_rev_mult, "name": "Мульт-обозреватель", "desc": "Написать рецензию на 5 мультфильмов", "emoji": "🎬"},
                {"target": 7, "cur": cnt_rev_mult, "name": "Разбор рисовки", "desc": "Написать рецензию на 7 мультфильмов", "emoji": "🎨"},
                {"target": 10, "cur": cnt_rev_mult, "name": "Летописец мультмиров", "desc": "Написать рецензию на 10 мультфильмов", "emoji": "🗺️"},
                {"target": 15, "cur": cnt_rev_mult, "name": "Профессор анимации", "desc": "Написать рецензию на 15 мультфильмов", "emoji": "🎓"},
                {"target": 20, "cur": cnt_rev_mult, "name": "Маг рецензий", "desc": "Написать рецензию на 20 мультфильмов", "emoji": "🧙‍♂️"},
                {"target": 25, "cur": cnt_rev_mult, "name": "Архивариус детства", "desc": "Написать рецензию на 25 мультфильмов", "emoji": "🗄️"},
                {"target": 30, "cur": cnt_rev_mult, "name": "Легенда анимации", "desc": "Написать рецензию на 30 мультфильмов", "emoji": "🦄"},

                # --- НАПИСАТЬ РЕЦЕНЗИЮ НА ТАЙТЛЫ (ВСЕГО) ---
                {"target": 5, "cur": cnt_rev_total, "name": "Начинающий автор", "desc": "Написать рецензию на 5 тайтлов всего", "emoji": "✍️"},
                {"target": 7, "cur": cnt_rev_total, "name": "Любитель обзоров", "desc": "Написать рецензию на 7 тайтлов всего", "emoji": "📂"},
                {"target": 10, "cur": cnt_rev_total, "name": "Аналитик с дивана", "desc": "Написать рецензию на 10 тайтлов всего", "emoji": "🛋️"},
                {"target": 15, "cur": cnt_rev_total, "name": "Киноблогер", "desc": "Написать рецензию на 15 тайтлов всего", "emoji": "📸"},
                {"target": 20, "cur": cnt_rev_total, "name": "Свободный микрофон", "desc": "Написать рецензию на 20 тайтлов всего", "emoji": "🎙️"},
                {"target": 25, "cur": cnt_rev_total, "name": "Повелитель текста", "desc": "Написать рецензию на 25 тайтлов всего", "emoji": "⌨️"},
                {"target": 30, "cur": cnt_rev_total, "name": "Голос сообщества", "desc": "Написать рецензию на 30 тайтлов всего", "emoji": "📣"},
                {"target": 35, "cur": cnt_rev_total, "name": "Мыслитель", "desc": "Написать рецензию на 35 тайтлов всего", "emoji": "💭"},
                {"target": 40, "cur": cnt_rev_total, "name": "Мастер пера", "desc": "Написать рецензию на 40 тайтлов всего", "emoji": "🪶"},
                {"target": 45, "cur": cnt_rev_total, "name": "Главный редактор", "desc": "Написать рецензию на 45 тайтлов всего", "emoji": "💼"},
                {"target": 50, "cur": cnt_rev_total, "name": "Хранитель рецензий", "desc": "Написать рецензию на 50 тайтлов всего", "emoji": "📦"},
                {"target": 55, "cur": cnt_rev_total, "name": "Живая энциклопедия", "desc": "Написать рецензию на 55 тайтлов всего", "emoji": "🧬"},
                {"target": 60, "cur": cnt_rev_total, "name": "Абсолютный обозреватель тайтлов", "desc": "Написать рецензию на 60 тайтлов всего", "emoji": "🌌"},
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
                                <p style="margin:5px 0 0 0; font-size:14px; color:#555;">{ach['desc']} ( Выполнено: {ach['cur']}/{ach['target']} )</p>
                            </div>
                        """, unsafe_allow_html=True)
                if not earned_any: st.info("У тебя пока нет полученных ачивок.")

            with ach_sub_tab2:
                for ach in achievements_config:
                    is_earned = ach["cur"] >= ach["target"]
                    progress = min(ach["cur"] / ach["target"], 1.0)
                    if is_earned:
                        st.markdown(
                            f"""<div class="achievement-card earned"><h4 style="margin:0; color:#28A745;">{ach['emoji']} {ach['name']}</h4></div>""",
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f"""<div class="achievement-card"><h4 style="margin:0; color:#2B2B2B;">{ach['emoji']} {ach['name']}</h4><p style="margin:5px 0 0 0; font-size:14px; color:#666;">{ach['desc']}</p></div>""",
                            unsafe_allow_html=True)
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

            col_view1, col_view2 = st.columns([1, 2])
            with col_view1:
                st.image(movie['poster_url'], use_container_width=True)
            with col_view2:
                st.markdown("### 📝 Описание фильма")
                st.write(movie['description'])
                st.write("---")

                st.markdown("### 🎯 Твой статус фильма")
                current_status = next((a["status"] for a in actions_list if
                                       a["username"] == st.session_state.user_role and a["movie_id"] == movie["id"]),
                                      None)

                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if current_status == "watched":
                        st.success("✅ Просмотрено")
                    else:
                        if st.button("🎬 Отметить просмотренным", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], "watched");
                            st.rerun()
                with col_btn2:
                    if current_status == "watchlist":
                        st.warning("📌 В планах")
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
                if movie['trailer_url']:
                    st.markdown(f"### 🍿 [Смотреть трейлер на YouTube]({movie['trailer_url']})")
                    if "youtube.com" in movie['trailer_url'] or "youtu.be" in movie['trailer_url']: st.video(
                        movie['trailer_url'])

            st.write("---")
            st.markdown(f"### ✍️ Оставить рецензию на фильм «{movie['title']}»")
            rating = st.slider("Выбери оценку:", min_value=1, max_value=10, value=5)
            selected_vibe = st.radio("Вайб:", ["🥱 Уснула", "😢 Поплакала", "🔥 Топчик", "✨ Вайбик"], horizontal=True)
            review_text = st.text_area("Впечатления:")

            if st.button("Сохранить отзыв", use_container_width=True):
                save_local_review({"movie_id": movie["id"], "username": st.session_state.user_role, "rating": rating,
                                   "vibe": selected_vibe, "review_text": review_text})
                save_local_action(st.session_state.user_role, movie["id"], "watched")
                st.success("Сохранено!");
                st.rerun()

            # --- ТЕСТЫ ПОД ОТЗЫВАМИ ---
            movie_quizzes = [q for q in quizzes_list if q["movie_id"] == movie["id"]]
            if movie_quizzes:
                st.write("---")
                st.markdown("### 🧠 Мини-тесты от Семёна:")
                for idx, mq in enumerate(movie_quizzes):
                    passed_mq = next((r for r in quiz_results if
                                      r["username"] == st.session_state.user_role and r["quiz_id"] == mq["id"]), None)
                    st.markdown(f"""<div class="quiz-single-box"><b>Вопрос #{idx + 1}:</b> {mq['question']}</div>""",
                                unsafe_allow_html=True)
                    if passed_mq:
                        if passed_mq["is_correct"]:
                            st.success(f"Правильно! 🎉")
                        else:
                            st.error(f"Неверно. Правильно: {mq['correct']}")
                    else:
                        user_ans_mq = st.radio("Варианты:", [f"{k}: {v}" for k, v in mq["options"].items()],
                                               key=f"mq_card_ans_{mq['id']}")
                        if st.button("🎯 Ответить", key=f"btn_mq_card_{mq['id']}"):
                            supabase.table("quiz_results").insert(
                                {"username": st.session_state.user_role, "quiz_id": mq["id"],
                                 "user_answer": user_ans_mq[0],
                                 "is_correct": (user_ans_mq[0] == mq["correct"])}).execute()
                            st.rerun()

            st.write("---")
            st.markdown("### 💬 Рецензии зрителей")
            movie_reviews = [r for r in reviews_list if r["movie_id"] == movie["id"]]
            if not movie_reviews:
                st.info("Отзывов пока нет.")
            else:
                for rev in movie_reviews:
                    st.markdown(
                        f"""<div class="review-box"><strong>👤 {rev['username']}</strong> — <span style='color:#E50914;'>⭐️ {rev['rating']}/10</span><p>{rev['review_text']}</p></div>""",
                        unsafe_allow_html=True)

# ==========================================
# 🛠 ТЕХПОДДЕРЖКА (ФУТЕР)
# ==========================================
st.write("---")
_, footer_col, _ = st.columns([1, 2, 1])
with footer_col:
    st.markdown("""
        <div style="text-align: center; color: #777777; font-size: 14px; margin-top: 10px; margin-bottom: 20px;">
            💡 Есть вопросы, пожелания или что-то не работает?<br>
            Пиши администратору: 
            <a href="https://t.me/SemenMag" target="_blank" style="color: #E50914; font-weight: bold; text-decoration: none;">
                @SemenMag 🚀
            </a>
        </div>
    """, unsafe_allow_html=True)
