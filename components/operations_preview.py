import streamlit as st

def render_operations_preview(ops_enriched):
    with st.expander("Anteprima operazioni", expanded=False):

        st.caption("Vista sintetica delle operazioni filtrate")

        show_full = st.checkbox("Mostra tutte le colonne", value=False)

        if show_full:
            st.dataframe(ops_enriched, use_container_width=True)
        else:
            cols = [
                "Data",
                "Ticker",
                "Intermediario",
                "Tipo",
                "Quantita",
                "Prezzo",
                "AvgCostBefore",
                "RealizedTradePL",
            ]

            cols = [c for c in cols if c in ops_enriched.columns]

            def highlight_sell(val):
                try:
                    return "color: red" if float(val) < 0 else ""
                except:
                    return ""

            st.dataframe(
                ops_enriched[cols]
                .sort_values("Data", ascending=False)
                .style
                .format({
                    "Prezzo": "{:,.2f}",
                    "AvgCostBefore": "{:,.2f}",
                    "RealizedTradePL": "€ {:,.2f}"
                })
                .applymap(highlight_sell, subset=["Quantita"]),
                use_container_width=True
            )
