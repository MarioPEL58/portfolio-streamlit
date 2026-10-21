import streamlit as st
import os

from config.config import load_config
from utils.i18n import init_language, t

from utils.auth import (
    init_session,
    login,
    signup,
    logout,
    is_logged,
    reset_password,
    change_password,
    set_recovery_session,
    get_profile,
)

# ✅ CONFIG BASE
CONFIG = load_config()
ENV = os.getenv("ENV", "DEV")

env_cfg = CONFIG["env"][ENV]

# ✅ ⚠️ SEMPRE PRIMA DI QUALSIASI st.sidebar
st.set_page_config(
    page_title=env_cfg["title"],
    page_icon=env_cfg["icon"],
    layout="wide"
)

# ✅ ORA puoi usare Streamlit
LANG = init_language(CONFIG)

# ==== UI ==========
init_session()

params = st.query_params

recovery_mode = (
    params.get("type") == "recovery"
)

if recovery_mode:
    
    access_token = params.get("access_token")
    refresh_token = params.get("refresh_token")
    
    success, error = set_recovery_session(
        access_token,
        refresh_token
    )
    
    # st.write("SESSION:",success)
    
    if error:
        st.error(error)
        
    st.title(
        t("reset_password_title")
    )

    new_password = st.text_input(
        t("new_password"),
        type="password"
    )

    confirm_password = st.text_input(
        t("confirm_password"),
        type="password"
    )

    if st.button(
        t("change_password")
    ):

        if new_password != confirm_password:

            st.warning(
                t("password_mismatch")
            )

        else:
            success, error = change_password(
                new_password
            )
            if success:
    
                st.success(
                    t("password_changed")
                )
                st.info(
                    t("login_with_new_password")
                )
            else:
    
                st.error(error)
            
    st.stop()

st.title(t("login_page_title"))

if is_logged():

    profile = get_profile()
    
    st.success(
        t("login_authenticated")
    )

    st.write(
         f"📧 {st.session_state.user_email}"
    )
    if profile:
        if profile["language"] == "it":
            lang_text = "🇮🇹 Italiano"
        else:
            lang_text = "🇬🇧 English"
            
        role_map = {
            "free": "🆓 Free",
            "premium": "⭐ Premium",
            "admin": "👑 Admin",
        }    
        st.write(f"🏷️ Role: {role_map.get(profile['role'], profile['role'])}")
        st.write(f"🌐 Language: {lang_text}")
        
    if st.button(
        t("logout_button")
    ):

        logout()
        st.rerun()
        
    st.markdown("---")

    st.subheader(
        t("change_password")
    )

    new_password = st.text_input(
        t("new_password"),
        type="password"
    )

    confirm_password = st.text_input(
        t("confirm_password"),
        type="password"
    )

    if st.button(
        t("change_password")
    ):

        if not new_password:

            st.warning(
                t("password_required")
            )

        elif new_password != confirm_password:

            st.warning(
                t("password_mismatch")
            )

        else:

            success, error = change_password(
                new_password
            )

            if success:

                st.success(
                    t("password_changed")
                )

            else:

                st.error(error)

    st.markdown("---")

else:

    email = st.text_input(
        t("login_email")
    )

    password = st.text_input(
        t("login_password"),
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:
        
        if st.button(t("login_button")):
        
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
                        and "timed out" in error.lower()
                    ):
                
                        st.warning(
                            t("login_timeout")
                        )
                    elif (
                        error
                        and "Invalid login credentials" in error
                    ):
        
                        st.warning(
                            f"{t('login_invalid_credentials')}\n\n"
                            f"{t('login_register_hint')}"
                        )
                    elif (
                        error
                        and "Email not confirmed" in error
                    ):
                    
                        st.warning(
                            f"{t('login_email_not_verified')}\n\n"
                            f"{t('signup_check_spam')}"
                        )
                        
                    else:
        
                        st.error(error)

    with col2:

        if st.button(t("signup_button")):

            success, message = signup(
                email,
                password
            )
            
            if success:
            
                if message == "confirm_email":
            
                    st.success(
                        t("signup_success")
                    )
            
                    st.caption(
                        t("signup_check_spam")
                    )
            
            else:
            
                st.error(message)
                
    st.markdown("---")
    
    if st.button(
        t("reset_password")
    ):
        
        if not email:
            
            st.warning(
                t("login_email_required")
            )
        
        else:
            
            success, error = reset_password(
                email
            )
            
            if success:
                
                st.success(
                    t("reset_password_sent")
                )
            
            else:
                
                st.error(error)

st.success(t("login_registration_info_title"))
st.caption(t("login_registration_info"))
st.markdown("---")
st.caption(
    f"**{t('login_privacy_title')}**\n\n"
    f"{t('login_privacy_info')}"
)
