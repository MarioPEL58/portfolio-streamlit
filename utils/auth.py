import streamlit as st

from supabase import create_client


# ==================================
# CLIENT SUPABASE
# ==================================

@st.cache_resource
def get_supabase():

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


# ==================================
# SESSIONE
# ==================================

def init_session():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "user" not in st.session_state:
        st.session_state.user = None


# ==================================
# LOGIN
# ==================================

def login(email, password):

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

        return True

    except Exception as e:

        st.error(f"Login fallito: {e}")

        return False


# ==================================
# REGISTRAZIONE
# ==================================

def signup(email, password):

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


# ==================================
# LOGOUT
# ==================================

def logout():

    try:

        supabase = get_supabase()

        supabase.auth.sign_out()

    except:
        pass

    st.session_state.logged_in = False
    st.session_state.user = None


# ==================================
# UTENTE LOGGATO ?
# ==================================

def is_logged():

    return st.session_state.get(
        "logged_in",
        False
    )


# ==================================
# PROTEZIONE PAGINA
# ==================================

def require_login():

    if not is_logged():

        st.warning(
            "Effettua il login per accedere a questa pagina."
        )

        st.stop()
