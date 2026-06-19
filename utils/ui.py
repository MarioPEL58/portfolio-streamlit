import streamlit as st

def title_with_tooltip(title: str, tooltip: str, level: int = 16):

    st.markdown(
        f"""
        <span style="font-size:{level}px; font-weight:bold">
            {title}
            <span title="{tooltip}" 
                  style="
                    cursor: help;
                    margin-left: 8px;
                    color: #9CA3AF;
                    border: 1px solid #9CA3AF;
                    border-radius: 50%;
                    width: 16px;
                    height: 16px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 11px;
                  ">
                ?
            </span>
        </span>
        """,
        unsafe_allow_html=True
    )
