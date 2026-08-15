import streamlit as st
from utils.i18n import t

def render_filters(ops, dividends):
    st.markdown(t("filters_title"))

    # -------------------------
    # liste disponibili
    # -------------------------
    all_brokers = sorted(
        ops["Intermediario"].dropna().astype(str).str.strip().unique().tolist()
    )

    all_types = sorted(
        ops["Tipo"].dropna().astype(str).str.strip().unique().tolist()
    )
    
    selected_types = st.session_state.get("selected_types", all_types)
    
    ops["OperationLabel"] = (
        ops["ID"].astype(str).str.replace(".0", "", regex=False)
        + " - "
        + ops["Nome"].fillna("").astype(str).str.strip()
    )
    
    ops_for_operations = ops.copy()
    
    if selected_types and len(selected_types) < len(all_types):
        ops_for_operations = ops_for_operations[
            ops_for_operations["Tipo"]
            .astype(str)
            .str.strip()
            .isin(selected_types)
        ]
    
    all_operations = sorted(
        ops_for_operations["OperationLabel"]
        .dropna()
        .unique()
        .tolist()
    )
    # -------------------------
    # init state (safe)
    # -------------------------
    if "selected_brokers" not in st.session_state:
        st.session_state.selected_brokers = all_brokers

    if "selected_types" not in st.session_state:
        st.session_state.selected_types = all_types

    if "selected_operations" not in st.session_state:
        st.session_state.selected_operations = all_operations
        
    if "only_active" not in st.session_state:
        st.session_state.only_active = False

    # ✅ FIX: tieni solo valori ancora validi
    st.session_state.selected_brokers = [
        b for b in st.session_state.selected_brokers if b in all_brokers
    ]

    st.session_state.selected_types = [
        t_ for t_ in st.session_state.selected_types if t_ in all_types
    ]

    st.session_state.selected_operations = [
        op for op in st.session_state.selected_operations if op in all_operations
    ]
    # -------------------------
    # widgets
    # -------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.multiselect(
            t("filter_brokers"),
            options=all_brokers,
            default=st.session_state.selected_brokers,
            key="selected_brokers"
        )

    with col2:
        st.multiselect(
            t("filter_types"),
            options=all_types,
            default=st.session_state.selected_types,
            key="selected_types"
        )

    with col3:
        st.multiselect(
            t("filter_operations"),
            options=all_operations,
            default=st.session_state.selected_operations,
            key="selected_operations"
        )
        
    st.toggle(
        t("filter_active_only"),
        key="only_active"
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

    if st.session_state.selected_operations:
        ops_filtered = ops_filtered[
            ops_filtered["OperationLabel"].isin(
                st.session_state.selected_operations
            )
        ]
    if st.session_state.only_active:
        
        active_ids = (
            ops.assign(
                Quantita=pd.to_numeric(
                    ops["Quantita"],
                    errors="coerce"
                ).fillna(0)
            )
            .groupby("ID")["Quantita"]
            .sum()
            .loc[lambda s: s != 0]
            .index
        )
    
        ops_filtered = ops_filtered[
            ops_filtered["ID"].isin(active_ids)
        ]
        
    ops_filtered = ops_filtered.copy()

    # =========================
    # ✅ FEEDBACK FILTRI (fix quote bug)
    # =========================
    active_filters = []

    if set(st.session_state.selected_brokers) != set(all_brokers):
        active_filters.append(
            f"{t('filter_brokers')} ({', '.join(st.session_state.selected_brokers)})"
        )

    if set(st.session_state.selected_types) != set(all_types):
        active_filters.append(
            f"{t('filter_types')} ({', '.join(st.session_state.selected_types)})"
        )
    
    if set(st.session_state.selected_operations) != set(all_operations):
        active_filters.append(
            f"{t('filter_operations')} ({len(st.session_state.selected_operations)}/{len(all_operations)})"
        )
    if st.session_state.only_active:
        active_filters.append(
            t("filter_active_only")
        )
        
    if active_filters:
        st.caption(f"{t('active_filters')}: {', '.join(active_filters)}")

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

    if dividends is not None and not dividends.empty:
        if dividends_filtered is not None and dividends_filtered.empty:
            st.caption(t("no_dividends_filtered"))

    # =========================
    # CONTEXT ✅
    # =========================
    filter_context = {
        "ops": ops_filtered,
        "dividends": dividends_filtered,
        "tickers": sorted(ops_filtered["Ticker"].dropna().unique().tolist()),
        "brokers": st.session_state.selected_brokers,
        "types": st.session_state.selected_types,
        "operations": st.session_state.selected_operations,
        "only_active": st.session_state.only_active,
    }

    return filter_context
