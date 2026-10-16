import streamlit as st

from supabase import Client, create_client


# =====================================================
# SUPABASE CLIENT
# =====================================================

@st.cache_resource
def get_supabase() -> Client:

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


# =====================================================
# SESSION STATE
# =====================================================

def init_session():

    defaults = {
        "logged_in": False,
        "user": None,
        "user_id": None,
        "user_email": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =====================================================
# LOGIN
# =====================================================

def login(
    email: str,
    password: str
) -> tuple[bool, str | None]:

    supabase = get_supabase()

    try:

        result = supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        st.session_state.logged_in = True
        st.session_state.user = result.user
        st.session_state.user_id = result.user.id
        st.session_state.user_email = result.user.email

        return True, None

    except Exception as e:

        return False, str(e)


# =====================================================
# REGISTRAZIONE
# =====================================================

def signup(email: str, password: str) -> bool:

    supabase = get_supabase()

    try:

        supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

        st.success(
            "Utente registrato. Controlla la mail di conferma."
        )

        return True

    except Exception as e:

        st.error(
            f"Registrazione fallita: {e}"
        )

        return False


# =====================================================
# LOGOUT
# =====================================================

def logout():

    try:

        get_supabase().auth.sign_out()

    except Exception:
        pass

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.user_email = None


# =====================================================
# INFO UTENTE
# =====================================================

def is_logged() -> bool:

    return st.session_state.get(
        "logged_in",
        False
    )


def get_user_email():

    return st.session_state.get(
        "user_email"
    )


def get_user_id():

    return st.session_state.get(
        "user_id"
    )


# =====================================================
# PROTEZIONE PAGINE
# =====================================================

def require_login():

    if not is_logged():

        st.warning(
            "🔒 Area riservata agli utenti registrati."
        )

        st.info(
            "Effettua il login per accedere alla Frontiera Efficiente."
        )

        st.stop()


# =====================================================
# SIDEBAR UTENTE
# =====================================================

def render_user_sidebar():

    if is_logged():

        st.sidebar.success(
            f"👤 {get_user_email()}"
        )

        if st.sidebar.button(
            "🚪 Logout",
            width="stretch"
        ):

            logout()
            st.rerun()

    else:

        st.sidebar.info(
            "👤 Ospite"
        )
