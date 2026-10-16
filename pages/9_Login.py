import streamlit as st

from utils.i18n import t

from utils.auth import (
    init_session,
    login,
    signup,
    logout,
    is_logged
)

init_session()

st.title("🔑 Login")

if is_logged():

    st.success("Utente autenticato")

    st.write(
        st.session_state.user.email
    )

    if st.button("Logout"):

        logout()
        st.rerun()

else:

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:
        
        if st.button("Login"):
        
            if not email or not password:
        
                st.warning(
                    t("login_missing_credentials")
                )
        
            else:
        
                success, error = login(
                    email,
                    password
                )
        
                if success:
        
                    st.rerun()
        
                else:
        
                    if (
                        error
                        and "Invalid login credentials" in error
                    ):
        
                        st.warning(
                            f"{t('login_invalid_credentials')}\n\n"
                            f"{t('login_register_hint')}"
                        )
        
                    else:
        
                        st.error(error)

    with col2:

        if st.button("Registrati"):

            signup(
                email,
                password
            )
