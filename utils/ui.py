import streamlit as st

def title_with_tooltip(title: str, tooltip: str, level: int = 16):
    """
    Mostra un titolo con tooltip stile 'fintech' (icona ? con hover).

    Args:
        title: testo del titolo (es. t("beta_title"))
        tooltip: testo del tooltip (es. t("beta_description"))
        level: dimensione font (default 16px)
    """

    st.markdown(
        f"""
        <span style="font-size:{level}px; font-weight:bold">
            {title}
            <span title="{tooltip}" 
                  style="
                    cursor: help;
                    margin-left: 6px;
                    color: #9CA3AF;
                    border: 1px solid #9CA3AF;
                    border-radius: 50%;
                    padding: 1px 6px;
                    font-size: 11px;
                    display: inline-block;
                    line-height: 1;
                  ">
                ?
            </span>
        </span>
        """,
        unsafe_allow_html=True
    )
