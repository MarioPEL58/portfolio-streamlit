import streamlit as st

from utils.i18n import t
from utils.auth import change_password

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
