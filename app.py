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

    /* Кнопки */
    div.stButton > button {
        background-color: #E50914 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 900 !important;
        font-size: 15px !important;
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
        color: #111111 !important;
        font-size: 16px !important; font-weight: 800 !important;
    }

    h1, h2, h3, h4 { color: #2B2B2B !important; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 700 !important; }
    
    .movie-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0; border-radius: 12px;
        padding: 15px; text-align: center; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.05); transition: 0.3s;
        margin-bottom: 10px; position: relative;
    }
    .movie-card:hover {
        border-color: #E50914;
        box-shadow: 0px 6px 15px rgba(229, 9, 20, 0.15); transform: translateY(-2px);
    }

    .review-box {
        background-color: #FFFFFF; border-left: 5px solid #E50914;
        padding: 12px; border-radius: 4px; margin-bottom: 10px;
    }
    .stats-box-new {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0; border-left: 5px solid #E50914;
        padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    }
    .quiz-single-box {
        background-color: #FFFFFF; border: 1px solid #E0E0E0;
        border-radius: 8px; padding: 15px; margin-bottom: 15px;
    }
    
    .achievement-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0; border-radius: 10px; padding: 15px; margin-bottom: 12px; box-shadow: 0px 2px 4px rgba(0,0,0,0.02);
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
        st.markdown("<p style='text-align: center; color: #666; font-size: 16px;'>Добро пожаловать. Кто заходит?</p>", unsafe_allow_html=True)
        st.write("---")

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🕶 Семён (Админ)", use_container_width=True):
                st.session_state.login_target = "Семён"; st.rerun()
        with btn_col2:
            if st.button("🍿 Кристина", use_container_width=True):
                st.session_state.user_role = "Кристина"; st.rerun()

        if st.session_state.login_target == "Семён":
            st.write("---")
            password = st.text_input("Введите секретный пароль:", type="password")
            if st.button("Войти как Администратор"):
                if password == "0105":  # Пароль из старого рабочего кода
                    st.session_state.user_role = "Семён"
                    st.success("Доступ разрешен!")
                    st.rerun()
                else: st.error("Неверный пароль!")

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
    user_watched_ids = [a["movie_id"] for a in actions_list if a["username"] == st.session_state.user_role and a["status"] == "watched"]
    user_watched = len(user_watched_ids)
    user_watchlist_ids = [a["movie_id"] for a in actions_list if a["username"] == st.session_state.user_role and a["status"] == "watchlist"]
    user_watchlist = len(user_watchlist_ids)

    with st.sidebar:
        st.markdown(f"### 👤 Профиль: **{st.session_state.user_role}**")
        st.write("---")
        
        page = st.radio("🧭 Навигация по сайту:", ["🏠 Главный каталог", "🔥 Семён рекомендует", "👤 Моё Пространство"])
        if page == "🏠 Главный каталог": st.session_state.nav_page = "catalog"
        elif page == "🔥 Семён рекомендует": st.session_state.nav_page = "semen_recommend"
        else: st.session_state.nav_page = "my_space"
            
        st.write("---")
        if st.button("🚪 Выйти из аккаунта", use_container_width=True):
            st.session_state.user_role = None
            st.session_state.login_target = None
            st.session_state.nav_page = "catalog"
            st.query_params.clear()
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
                
                if unwatched_movies: st.session_state.random_movie = random.choice(unwatched_movies)
                else: st.session_state.random_movie = "empty"

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
                    st.query_params["movie_id"] = rm['id']
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
                        m_status = next((a["status"] for a in actions_list if a["username"] == st.session_state.user_role and a["movie_id"] == movie["id"]), None)
                        status_badge = ""
                        if m_status == "watched": 
                            status_badge = "<br><span style='background-color:#28A745; color:white; padding:2px 6px; border-radius:4px; font-size:11px;'>✅ Просмотрено</span>"
                        elif m_status == "watchlist": 
                            status_badge = "<br><span style='background-color:#FFC107; color:black; padding:2px 6px; border-radius:4px; font-size:11px;'>📌 В планах</span>"

                        is_rec = movie.get("recommended", False)
                        rec_badge = "<span style='position:absolute; top:10px; right:10px; background-color:#E50914; color:white; padding:3px 8px; border-radius:20px; font-size:11px; font-weight:bold;'>🔥 Рекомендую</span>" if is_rec else ""

                        # --- РАСЧЕТ ОЦЕНКИ И ВАЙБОМЕТРА НА ЛЕТУ ИЗ SUPABASE ---
                        movie_reviews = [r for r in reviews_list if r["movie_id"] == movie["id"]]
                        if movie_reviews:
                            avg_rating = sum(float(r["rating"]) for r in movie_reviews) / len(movie_reviews)
                            rating_str = f"{avg_rating:.1f}/10"
                        else:
                            rating_str = "—"
                        
                        vibes_set = {r["vibe"] for r in movie_reviews if "vibe" in r and r["vibe"]}
                        vibe_str = ", ".join(list(vibes_set)) if vibes_set else "Пока не определен"

                        # Защита от кривой верстки картинок
                        p_url = str(movie.get('poster_url', '')).strip().replace('\n', '').replace('\r', '')
                        if not p_url or not p_url.startswith("http"):
                            p_url = "https://via.placeholder.com/300x450?text=Нет+постера"

                        st.markdown(f"""
                            <div class="movie-card" style="position:relative; background-color:#FFFFFF; padding:15px; border-radius:12px; border:1px solid #E0E0E0; margin-bottom:10px; text-align:center; box-shadow:0px 4px 6px rgba(0,0,0,0.05);">
                                {rec_badge}
                                <img src="{p_url}" style="width:100%; max-height:380px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:20px; text-align:center;">{movie['title']}</h3>
                                <div style="margin-bottom: 10px;">
                                    <span style="background-color:#E50914; color:white; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:bold;">{movie['category']}</span>
                                    {status_badge}
                                </div>
                                <div style="background-color:#F8F9FA; padding:10px; border-radius:8px; margin-top:10px; font-size:13px; text-align:left; color:#2B2B2B; border:1px solid #EAEAEA;">
                                    <div style="margin-bottom: 4px;"><b>⭐ Средняя оценка:</b> <span style="color:#E50914; font-weight:bold;">{rating_str}</span></div>
                                    <div><b>🔮 Вайбометр:</b> <span style="font-style:italic; color:#555;">{vibe_str}</span></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        if st.button(f"Открыть «{movie['title']}»", key=f"id_move_{movie['id']}", use_container_width=True):
                            st.query_params["movie_id"] = movie['id']
                            st.rerun()
                        
                        if st.session_state.user_role == "Семён":
                            if is_rec:
                                if st.button("❌ Убрать из рекомендаций", key=f"rem_rec_{movie['id']}", use_container_width=True):
                                    supabase.table("movies").update({"recommended": False}).eq("id", movie["id"]).execute()
                                    st.rerun()
                            else:
                                if st.button("⭐️ Сделать рекомендованным", key=f"add_rec_{movie['id']}", use_container_width=True):
                                    supabase.table("movies").update({"recommended": True}).eq("id", movie["id"]).execute()
                                    st.rerun()

        # --- ПАНЕЛЬ СЕМЁНА ---
        if st.session_state.user_role == "Семён":
            st.write("---")
            st.markdown("### 🛠 Панель Семёна (Управление системой)")
            adm_tab1, adm_tab2, adm_tab3 = st.tabs(["🎬 Добавить фильм", "🧠 Создать Вопрос Квиза", "🔔 Заявки от Кристины"])
            
            with adm_tab1:
                with st.form(key="add_movie_form", clear_on_submit=True):
                    new_title = st.text_input("🎬 Название тайтла:")
                    new_category = st.selectbox("Тип:", ["Фильм", "Сериал", "Мультфильм"])
                    new_poster = st.text_input("🖼️ Ссылка на постер:")
                    new_trailer = st.text_input("🍿 Ссылка на трейлер (YouTube):")
                    new_description = st.text_area("📝 Описание фильма:")
                    if st.form_submit_button("Добавить фильм в систему"):
                        if new_title and new_description:
                            save_local_movie({
                                "title": new_title,
                                "category": new_category,
                                "poster_url": new_poster,
                                "trailer_url": new_trailer,
                                "description": new_description,
                                "recommended": False
                            })
                            st.success(f"Фильм «{new_title}» успешно сохранен в Supabase!")
                            st.rerun()
                        else: st.error("Заполни название и описание!")

            with adm_tab2:
                with st.form("add_quiz_form", clear_on_submit=True):
                    q_text = st.text_input("❓ Текст каверзного вопроса:")
                    opt_a = st.text_input("Вариант A:")
                    opt_b = st.text_input("Вариант B:")
                    opt_c = st.text_input("Вариант C:")
                    opt_d = st.text_input("Вариант D:")
                    q_correct = st.selectbox("Правильный ответ (Буква):", ["A", "B", "C", "D"])
                    if st.form_submit_button("Создать вопрос квиза"):
                        if q_text and opt_a and opt_b:
                            supabase.table("quizzes").insert({
                                "question": q_text,
                                "options": {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d},
                                "correct": q_correct
                            }).execute()
                            st.success("Новый вопрос квиза добавлен в базу!")
                            st.rerun()

            with adm_tab3:
                if not requests_list:
                    st.info("Новых запросов на добавление фильмов пока нет.")
                else:
                    for req in requests_list:
                        with st.container():
                            st.markdown(f"**🎬 {req['movie_title']}** ({req['category']})")
                            st.write(f"💬 Комментарий: {req.get('comment', 'Нет')}")
                            col_req1, col_req2 = st.columns(2)
                            with col_req1:
                                if st.button("🗑 Удалить заявку", key=f"del_req_{req['id']}"):
                                    supabase.table("requests").delete().eq("id", req["id"]).execute()
                                    st.rerun()
                            st.write("---")

    # --- СТРАНИЦА: СЕМЁН РЕКОМЕНДУЕТ ---
    elif st.session_state.current_page == "semen_recommend":
        st.markdown("<h1>🔥 Семён рекомендует</h1>", unsafe_allow_html=True)
        st.write("Здесь собраны шедевры кинематографа, лично отобранные Семёном!")
        st.write("---")
        
        rec_movies = [m for m in movies_list if m.get("recommended", False)]
        if not rec_movies:
            st.info("Семён пока не выделил ни одного фильма. Скоро здесь будет жарко!")
        else:
            chunks_rec = [rec_movies[i:i + 3] for i in range(0, len(rec_movies), 3)]
            for chunk in chunks_rec:
                cols = st.columns(3)
                for index, r_movie in enumerate(chunk):
                    with cols[index]:
                        m_status = next((a["status"] for a in actions_list if a["username"] == st.session_state.user_role and a["movie_id"] == r_movie["id"]), None)
                        status_badge = ""
                        if m_status == "watched": 
                            status_badge = "<br><span style='background-color:#28A745; color:white; padding:2px 6px; border-radius:4px; font-size:11px;'>✅ Просмотрено</span>"
                        elif m_status == "watchlist": 
                            status_badge = "<br><span style='background-color:#FFC107; color:black; padding:2px 6px; border-radius:4px; font-size:11px;'>📌 В планах</span>"

                        # Точно такой же расчет средних данных и вайбометра для страницы рекомендаций
                        movie_reviews = [r for r in reviews_list if r["movie_id"] == r_movie["id"]]
                        if movie_reviews:
                            avg_rating = sum(float(r["rating"]) for r in movie_reviews) / len(movie_reviews)
                            rating_str = f"{avg_rating:.1f}/10"
                        else:
                            rating_str = "—"
                        
                        vibes_set = {r["vibe"] for r in movie_reviews if "vibe" in r and r["vibe"]}
                        vibe_str = ", ".join(list(vibes_set)) if vibes_set else "Пока не определен"

                        p_url = str(r_movie.get('poster_url', '')).strip().replace('\n', '').replace('\r', '')
                        if not p_url or not p_url.startswith("http"):
                            p_url = "https://via.placeholder.com/300x450?text=Нет+постера"

                        st.markdown(f"""
                            <div class="movie-card" style="position:relative; background-color:#FFFFFF; padding:15px; border-radius:12px; border:1px solid #E0E0E0; margin-bottom:10px; text-align:center; box-shadow:0px 4px 6px rgba(0,0,0,0.05);">
                                <img src="{p_url}" style="width:100%; max-height:380px; object-fit:cover; border-radius:8px; margin-bottom:10px;">
                                <h3 style="color:#2B2B2B !important; margin: 5px 0; font-size:20px; text-align:center;">{r_movie['title']}</h3>
                                <div style="margin-bottom: 10px;">
                                    <span style="background-color:#E50914; color:white; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:bold;">{r_movie['category']}</span>
                                    {status_badge}
                                </div>
                                <div style="background-color:#F8F9FA; padding:10px; border-radius:8px; margin-top:10px; font-size:13px; text-align:left; color:#2B2B2B; border:1px solid #EAEAEA;">
                                    <div style="margin-bottom: 4px;"><b>⭐ Средняя оценка:</b> <span style="color:#E50914; font-weight:bold;">{rating_str}</span></div>
                                    <div><b>🔮 Вайбометр:</b> <span style="font-style:italic; color:#555;">{vibe_str}</span></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        if st.button(f"Погрузиться в «{r_movie['title']}»", key=f"rec_btn_{r_movie['id']}", use_container_width=True):
                            st.query_params["movie_id"] = r_movie['id']
                            st.rerun()

    # --- СТРАНИЦА: МОЁ ПРОСТРАНСТВО ---
    elif st.session_state.current_page == "my_space":
        st.markdown(f"<h1>👤 Моё Пространство: {st.session_state.user_role}</h1>", unsafe_allow_html=True)
        
        tab_space1, tab_space2, tab_space3 = st.tabs(["📊 Аналитика и Списки", "🏆 Мои Достижения", "💡 Предложить фильм"])
        
        with tab_space1:
            st.markdown("### 📌 Твой список отслеживания")
            w_movies = [m for m in movies_list if m["id"] in user_watchlist_ids]
            if not w_movies: st.info("В планах пока пусто. Добавляй фильмы кнопкой «Хочу посмотреть» на странице фильма!")
            else:
                for wm in w_movies:
                    st.write(f"🔹 **{wm['title']}** — {wm['category']}")
            
            st.write("---")
            st.markdown("### 🍿 Уже просмотрено тобой")
            hd_movies = [m for m in movies_list if m["id"] in user_watched_ids]
            if not hd_movies: st.info("Ты еще не отметила ни одного просмотренного фильма.")
            else:
                for hm in hd_movies:
                    st.write(f"✅ **{hm['title']}** — {hm['category']}")

        with tab_space2:
            st.markdown("### 🎖 Система Твоих Ачивок")
            
            # Логика расчета достижений
            ach_1 = user_watched >= 1
            ach_5 = user_watched >= 5
            ach_10 = user_watched >= 10
            ach_quiz = any(r["username"] == st.session_state.user_role for r in quiz_results)

            st.markdown(f"""
                <div class="achievement-card {'earned' if ach_1 else ''}">
                    <h4>{'🟢' if ach_1 else '🔒'} Первый шаг в киномир</h4>
                    <p>Посмотреть 1 любой фильм на платформе Кино Room.</p>
                </div>
                <div class="achievement-card {'earned' if ach_5 else ''}">
                    <h4>{'🟢' if ach_5 else '🔒'} Киноман среднего уровня</h4>
                    <p>Посмотреть 5 различных тайтлов.</p>
                </div>
                <div class="achievement-card {'earned' if ach_10 else ''}">
                    <h4>{'🟢' if ach_10 else '🔒'} Безумный Поглотитель Попкорна</h4>
                    <p>Посмотреть 10 фильмов или сериалов.</p>
                </div>
                <div class="achievement-card {'earned' if ach_quiz else ''}">
                    <h4>{'🟢' if ach_quiz else '🔒'} Интеллектуал</h4>
                    <p>Ответить хотя бы на один интерактивный вопрос квиза.</p>
                </div>
            """, unsafe_allow_html=True)

        with tab_space3:
            st.markdown("### ✉️ Отправить запрос Семёну на добавление фильма")
            with st.form("req_movie_form", clear_on_submit=True):
                r_title = st.text_input("🎬 Название фильма, которого тебе не хватает:")
                r_cat = st.selectbox("Категория тайтла:", ["Фильм", "Сериал", "Мультфильм"])
                r_comment = st.text_area("💬 Комментарий (почему Сёма должен его добавить):")
                if st.form_submit_button("Отправить запрос администратору"):
                    if r_title:
                        supabase.table("requests").insert({
                            "movie_title": r_title,
                            "category": r_cat,
                            "comment": r_comment
                        }).execute()
                        st.success(f"Заявка на фильм «{r_title}» успешно доставлена Семёну!")
                    else: st.error("Напиши название фильма!")

    # --- СТРАНИЦА ПРОСМОТРА ФИЛЬМА ---
    elif st.session_state.current_page == "movie_view" and st.session_state.selected_movie_id is not None:
        movie = next((m for m in movies_list if m["id"] == st.session_state.selected_movie_id), None)
        
        if not movie:
            st.error("Фильм не найден в нашей базе данных!")
            if st.button("⬅️ Назад в каталог"):
                st.query_params.clear()
                st.rerun()
        else:
            col_back, _ = st.columns([1, 5])
            with col_back:
                if st.button("⬅️ Назад", use_container_width=True):
                    st.query_params.clear()
                    st.rerun()

            st.write("")
            col_info1, col_info2 = st.columns([1, 2])
            
            with col_info1:
                p_url = str(movie.get('poster_url', '')).strip().replace('\n', '').replace('\r', '')
                if not p_url or not p_url.startswith("http"):
                    p_url = "https://via.placeholder.com/300x450?text=Нет+постера"
                st.image(p_url, use_container_width=True)
            
            with col_info2:
                st.title(movie["title"])
                st.subheader(f"📁 Категория: {movie['category']}")
                st.write("---")
                st.markdown(f"### 📝 Описание фильма:\n{movie['description']}")
                st.write("---")

                # Управление статусами просмотра
                m_status = next((a["status"] for a in actions_list if a["username"] == st.session_state.user_role and a["movie_id"] == movie["id"]), None)
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if m_status == "watched":
                        st.success("✅ Ты посмотрела этот фильм")
                    else:
                        if st.button("🎬 Отметить как просмотренный", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], "watched")
                            st.rerun()
                with col_btn2:
                    if m_status == "watchlist":
                        st.info("📌 Фильм находится в планах")
                    else:
                        if st.button("💖 Хочу посмотреть (В планы)", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], "watchlist")
                            st.rerun()
                with col_btn3:
                    if m_status:
                        if st.button("❌ Сбросить статус фильма", use_container_width=True):
                            save_local_action(st.session_state.user_role, movie["id"], None)
                            st.rerun()

            st.write("---")
            if movie.get("trailer_url"):
                st.markdown("### 🍿 Официальный Трейлер фильма")
                try: st.video(movie["trailer_url"])
                except: st.warning("Не удалось загрузить плеер трейлера. Проверь ссылку!")
            
            st.write("---")
            st.markdown("### ✍️ Оставить свою рецензию")
            with st.form("add_review_form", clear_on_submit=True):
                r_rating = st.slider("Твоя личная оценка фильма:", 1, 10, 8)
                r_vibe = st.text_input("🔮 Вайбометр (Какое настроение у фильма в паре слов?):", placeholder="Например: Уютный, Стеклянный, На подумать")
                r_text = st.text_area("💬 Твоя полноценная рецензия на фильм:")
                if st.form_submit_button("Опубликовать отзыв"):
                    if r_text:
                        save_local_review({
                            "movie_id": movie["id"],
                            "username": st.session_state.user_role,
                            "rating": int(r_rating),
                            "vibe": r_vibe.strip(),
                            "review_text": r_text
                        })
                        st.success("Твоя рецензия добавлена в облако Supabase!")
                        st.rerun()
                    else: st.error("Напиши хотя бы пару предложений отзыва!")

            # КВИЗЫ ДЛЯ ФИЛЬМА
            movie_quizzes = [q for q in quizzes_list if q.get("movie_id") == movie["id"] or q.get("id") == movie["id"]]
            if movie_quizzes:
                st.write("---")
                st.markdown("### 🧠 Интерактивный Квиз по фильму")
                for mq in movie_quizzes:
                    st.write(f"**Вопрос:** {mq['question']}")
                    user_ans_mq = st.radio("Выбери правильный вариант:", [f"{k}: {v}" for k, v in mq["options"].items()], key=f"quiz_radio_{mq['id']}")
                    if st.button("🎯 Ответить на вопрос", key=f"quiz_btn_{mq['id']}"):
                        supabase.table("quiz_results").insert({
                            "username": st.session_state.user_role,
                            "quiz_id": mq["id"],
                            "user_answer": user_ans_mq[0],
                            "is_correct": (user_ans_mq[0] == mq["correct"])
                        }).execute()
                        st.rerun()

            st.write("---")
            st.markdown("### 💬 Рецензии зрителей")
            movie_reviews = [r for r in reviews_list if r["movie_id"] == movie["id"]]
            if not movie_reviews:
                st.info("Отзывов пока нет.")
            else:
                for rev in movie_reviews:
                    # ПОЛНОСТЬЮ ВОССТАНОВЛЕННАЯ СТРОКА С НАСТРОЕНИЕМ ИЗ СТАРОГО КОДА
                    vibe_str = f" | Настроение: <b>{rev['vibe']}</b>" if "vibe" in rev and rev['vibe'] else ""
                    st.markdown(
                        f"""<div class="review-box"><strong>👤 {rev['username']}</strong> — <span style='color:#E50914;'>⭐️ {rev['rating']}/10</span>{vibe_str}<p style="margin-top:5px; color:#333;">{rev['review_text']}</p></div>""",
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
            <a href="https://t.me/SemenMag" target="_blank" style="color: #E50914; text-decoration: none; font-weight: bold;">@SemenMag</a>
        </div>
    """, unsafe_allow_html=True)
