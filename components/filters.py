import streamlit as st

def render_filters(ops, dividends):
    st.markdown("### 🎛️ Filtri")

    # -------------------------
    # liste disponibili
    # -------------------------
    all_brokers = sorted(
        ops["Intermediario"].dropna().astype(str).str.strip().unique().tolist()
    )

    all_types = sorted(
        ops["Tipo"].dropna().astype(str).str.strip().unique().tolist()
    )

    # -------------------------
    # init state
    # -------------------------
    if "selected_brokers" not in st.session_state:
        st.session_state.selected_brokers = all_brokers

    if "selected_types" not in st.session_state:
        st.session_state.selected_types = all_types

    # -------------------------
    # widgets
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.multiselect(
            "Intermediari",
            options=all_brokers,
            default=st.session_state.selected_brokers,
            key="selected_brokers"
        )

    with col2:
        st.multiselect(
            "Tipo",
            options=all_types,
            default=st.session_state.selected_types,
            key="selected_types"
        )

    # =========================
    # FILTER OPS
    # =========================
    ops_filtered = ops.copy()

    if st.session_state.selected_brokers:
        ops_filtered = ops_filtered[
            ops_filtered["Intermediario"].astype(str).str.strip().isin(
                st.session_state.selected_brokers
            )
        ]

    if st.session_state.selected_types:
        ops_filtered = ops_filtered[
            ops_filtered["Tipo"].astype(str).str.strip().isin(
                st.session_state.selected_types
            )
        ]

    ops_filtered = ops_filtered.copy()

    # =========================
    # FILTER DIVIDENDS
    # =========================
    if dividends is not None and not dividends.empty:
        ops_ids = (
            ops_filtered["ID"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.replace(".0", "", regex=False)
        )

        dividends_filtered = dividends.copy()
        dividends_filtered["ID"] = (
            dividends_filtered["ID"]
            .astype(str)
            .str.strip()
            .str.replace(".0", "", regex=False)
        )

        dividends_filtered = dividends_filtered[
            dividends_filtered["ID"].isin(ops_ids)
        ].copy()
    else:
        dividends_filtered = dividends

    # =========================
    # CONTEXT ✅
    # =========================
    filter_context = {
        "ops": ops_filtered,
        "dividends": dividends_filtered,
        "tickers": sorted(ops_filtered["Ticker"].dropna().unique().tolist()),
        "brokers": st.session_state.selected_brokers,
        "types": st.session_state.selected_types,
    }

    return filter_context
