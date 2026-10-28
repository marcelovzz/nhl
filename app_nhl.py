"""
app_nhl.py
Aplicación principal Streamlit — "TERMINAL SHARP: NHL QUANT".
Integra:
- Carga automática con respaldo en disco ('nhl_stats.xlsx') y uploader opcional.
- Selector de fecha diaria ('st.date_input') y botones rápidos [◀ Ayer] [Hoy] [Mañana ▶].
- Pestañas: "🏒 Cartelera & Momios en Vivo" y "📈 Auditoría & Calibración".
- Exportación de predicciones a Excel (.xlsx) en memoria mediante io.BytesIO.
"""

import io
import os
from datetime import date, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import streamlit as st

from engine_nhl import (
    DEFAULT_HFA_GOALS,
    DEFAULT_MC_ITERATIONS,
    analyze_game,
    build_predictions_export_df,
)
from setup_data import (
    COLUMNS as REQUIRED_COLUMNS,
    NHL_DEFAULT_FILENAME,
    ensure_nhl_stats_excel,
    read_excel_safe,
    write_xlsx_bytes,
)
from styles_nhl import inject_cyberpunk_styles, render_game_card, render_header_banner
from sync_espn_nhl import fetch_nhl_scoreboard, format_date_yyyymmdd, get_demo_slate

st.set_page_config(
    page_title="TERMINAL SHARP: NHL QUANT",
    page_icon="🏒",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_cyberpunk_styles()


def load_team_stats(uploaded_file: Any = None) -> pd.DataFrame:
    """
    Carga el archivo 'nhl_stats.xlsx' desde el uploader si fue provisto,
    o automáticamente desde el respaldo en disco (generándolo con setup_data si no existe).
    """
    if uploaded_file is not None:
        try:
            df_up = read_excel_safe(uploaded_file)
            missing = [c for c in REQUIRED_COLUMNS if c not in df_up.columns]
            if not missing:
                return df_up
            st.sidebar.warning(f"El archivo subido no contiene las columnas: {missing}. Usando base en disco.")
        except Exception as exc:
            st.sidebar.error(f"Error leyendo Excel subido: {exc}. Usando base en disco.")

    if not os.path.exists(NHL_DEFAULT_FILENAME):
        ensure_nhl_stats_excel(NHL_DEFAULT_FILENAME)

    return read_excel_safe(NHL_DEFAULT_FILENAME)


def export_excel_bytes(predictions_df: pd.DataFrame, stats_df: pd.DataFrame) -> bytes:
    """Genera un archivo Excel (.xlsx) en memoria con io.BytesIO incluyendo Predicciones y Base de Equipos."""
    buffer = io.BytesIO(
        write_xlsx_bytes(
            {
                "Predicciones_NHL_Quant": predictions_df,
                "NHL_Stats_32_Teams": stats_df,
            }
        )
    )
    buffer.seek(0)
    return buffer.getvalue()


def main() -> None:
    # Inicializar estado de fecha seleccionada
    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = date.today()

    # -------------------------------------------------------------------------
    # SIDEBAR: CONFIGURACIÓN, BASE DE DATOS Y PARÁMETROS DEL MOTOR
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### ⚙️ CONTROL QUANT NHL")
        st.caption("Base de Datos de 32 Franquicias & Goalies")

        disk_exists = os.path.exists(NHL_DEFAULT_FILENAME)
        if not disk_exists:
            ensure_nhl_stats_excel(NHL_DEFAULT_FILENAME)
            disk_exists = True

        st.success(f"💾 Respaldo activo: `{NHL_DEFAULT_FILENAME}`")

        uploaded_excel = st.file_uploader(
            "📂 Cargar `nhl_stats.xlsx` personalizado (Opcional)",
            type=["xlsx"],
            help="Si no subes ningún archivo, la terminal utiliza automáticamente 'nhl_stats.xlsx' en la raíz.",
        )

        stats_df = load_team_stats(uploaded_excel)

        st.markdown("---")
        st.markdown("### 🧮 PARÁMETROS DEL MOTOR")
        hfa_goals = st.slider(
            "Ventaja de Localía (HFA Goles)",
            min_value=0.00,
            max_value=0.60,
            value=float(DEFAULT_HFA_GOALS),
            step=0.02,
            help="Ajuste diferencial de goles esperados para el equipo local (~+0.28 en NHL).",
        )
        mc_sims = st.select_slider(
            "Iteraciones Monte Carlo (OT/SO)",
            options=[1000, 2500, 5000, 10000],
            value=DEFAULT_MC_ITERATIONS,
            help="Número de simulaciones por partido para resolver 3v3 Overtime y Shootout.",
        )
        ev_threshold = st.slider(
            "Umbral Mínimo Señal +EV (%)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            help="Porcentaje mínimo de Valor Esperado para encender el badge verde neón.",
        )
        use_demo_if_empty = st.checkbox(
            "Activar cartelera Demo si no hay juegos en la fecha",
            value=True,
            help="Muestra 4 partidos de prueba (2 pre-partido y 2 finalizados) cuando ESPN devuelve 0 juegos.",
        )

        with st.expander("🥅 Editar Porteros Titulares / Stats"):
            edited_stats_df = st.data_editor(
                stats_df,
                use_container_width=True,
                num_rows="fixed",
                key="nhl_stats_editor",
            )
            if st.button("💾 Guardar cambios en `nhl_stats.xlsx`", use_container_width=True):
                xlsx_data = write_xlsx_bytes({"NHL_Stats": edited_stats_df})
                with open(NHL_DEFAULT_FILENAME, "wb") as f:
                    f.write(xlsx_data)
                st.toast("Base de datos nhl_stats.xlsx actualizada en disco.", icon="✅")
            stats_df = edited_stats_df

    # -------------------------------------------------------------------------
    # NAVEGACIÓN DE FECHA: [◀ Ayer] [Hoy] [Mañana ▶] + st.date_input
    # -------------------------------------------------------------------------
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1.1, 1.1, 1.1, 2.2, 2.5])

    with nav_col1:
        if st.button("◀ Ayer", use_container_width=True):
            st.session_state["selected_date"] = st.session_state["selected_date"] - timedelta(days=1)
            st.rerun()

    with nav_col2:
        if st.button("Hoy", use_container_width=True):
            st.session_state["selected_date"] = date.today()
            st.rerun()

    with nav_col3:
        if st.button("Mañana ▶", use_container_width=True):
            st.session_state["selected_date"] = st.session_state["selected_date"] + timedelta(days=1)
            st.rerun()

    with nav_col4:
        picked_date = st.date_input(
            "📅 Fecha de Cartelera NHL",
            value=st.session_state["selected_date"],
            label_visibility="collapsed",
        )
        if picked_date != st.session_state["selected_date"]:
            st.session_state["selected_date"] = picked_date
            st.rerun()

    active_date: date = st.session_state["selected_date"]
    date_yyyymmdd = format_date_yyyymmdd(active_date)

    # -------------------------------------------------------------------------
    # INGESTA DE DATOS ESPN + EJECUCIÓN DEL MOTOR CUANTITATIVO
    # -------------------------------------------------------------------------
    with st.spinner(f"Sincronizando cartelera y momios NHL con ESPN ({date_yyyymmdd})..."):
        espn_data = fetch_nhl_scoreboard(active_date)

    raw_games = espn_data.get("games", [])
    is_demo_mode = False

    if not raw_games and use_demo_if_empty:
        raw_games = get_demo_slate(active_date)
        is_demo_mode = True

    analyzed_games: List[Dict[str, Any]] = [
        analyze_game(
            game=g,
            stats_df=stats_df,
            hfa_goals=hfa_goals,
            n_sims=mc_sims,
            ev_threshold=ev_threshold,
        )
        for g in raw_games
    ]

    export_df = build_predictions_export_df(analyzed_games)

    # Botón de exportación a Excel (.xlsx) en la barra superior
    with nav_col5:
        if not export_df.empty:
            excel_bytes = export_excel_bytes(export_df, stats_df)
            st.download_button(
                label="📥 Exportar Predicciones (.xlsx)",
                data=excel_bytes,
                file_name=f"nhl_quant_sharp_{date_yyyymmdd}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    total_sharp_signals = sum(len(g["positive_ev_signals"]) for g in analyzed_games)
    render_header_banner(
        date_label=active_date.strftime("%Y-%m-%d"),
        total_games=len(analyzed_games),
        sharp_signals_count=total_sharp_signals,
    )

    if espn_data.get("error"):
        st.warning(f"⚠️ {espn_data['error']}")
    if is_demo_mode:
        st.info(
            f"ℹ️ ESPN no reporta partidos oficiales programados para `{date_yyyymmdd}`. "
            "Visualizando **Cartelera Demo de Calibración** (puedes cambiar la fecha o desactivarla en la barra lateral)."
        )

    # -------------------------------------------------------------------------
    # PESTAÑAS PRINCIPALES
    # -------------------------------------------------------------------------
    tab_live, tab_audit = st.tabs(
        [
            "🏒 Cartelera & Momios en Vivo",
            "📈 Auditoría & Calibración",
        ]
    )

    # =========================================================================
    # PESTAÑA 1: CARTELERA & MOMIOS EN VIVO
    # =========================================================================
    with tab_live:
        if not analyzed_games:
            st.warning("No se encontraron partidos para la fecha seleccionada.")
        else:
            # KPIs rápidos de la jornada
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            avg_proj_goals = float(np.mean([g["proj_total_goals"] for g in analyzed_games]))
            avg_ot_prob = float(np.mean([g["prob_ot_pct"] for g in analyzed_games]))
            top_pick = max(analyzed_games, key=lambda x: x["best_bet"]["ev_pct"])["best_bet"]

            kpi1.metric("Partidos Analizados", f"{len(analyzed_games)}")
            kpi2.metric("Promedio Goles Proy. (MC)", f"{avg_proj_goals:.2f} goles")
            kpi3.metric("Prob. Media de Overtime (3v3)", f"{avg_ot_prob:.1f}%")
            kpi4.metric(
                "Mejor Oportunidad (+EV)",
                f"{top_pick['selection']} ({top_pick['mkt_odds']:.2f})",
                f"{top_pick['ev_pct']:+.2f}% EV",
            )

            st.markdown("#### 🎯 Tarjetas Cuantitativas por Partido")
            for g in analyzed_games:
                render_game_card(g, ev_threshold=ev_threshold)

            with st.expander("📊 Desglose de Totales Alternativos (5.5 / 6.0 / 6.5) & Tabla Maestra"):
                alt_rows = []
                for g in analyzed_games:
                    alt = g["alt_totals"]
                    alt_rows.append(
                        {
                            "Partido": f"{g['away_abbr']} @ {g['home_abbr']}",
                            "Total Proy MC": g["proj_total_goals"],
                            "Over 5.5 (%)": alt[5.5]["p_over"],
                            "Cuota Justa O5.5": alt[5.5]["fair_over"],
                            "Over 6.0 (%)": alt[6.0]["p_over"],
                            "Push 6.0 (%)": alt[6.0]["p_push"],
                            "Cuota Justa O6.0": alt[6.0]["fair_over"],
                            "Over 6.5 (%)": alt[6.5]["p_over"],
                            "Cuota Justa O6.5": alt[6.5]["fair_over"],
                        }
                    )
                st.dataframe(pd.DataFrame(alt_rows), use_container_width=True, hide_index=True)
                st.markdown("##### 📋 Resumen Ejecutivo de Predicciones")
                st.dataframe(export_df, use_container_width=True, hide_index=True)

    # =========================================================================
    # PESTAÑA 2: AUDITORÍA & CALIBRACIÓN POST-PARTIDO
    # =========================================================================
    with tab_audit:
        st.markdown("#### 📈 Auditoría Post-Partido & Calibración Probabilística")
        st.caption(
            "Evalúa automáticamente los partidos finalizados (`Final` / `Final/OT` / `Final/SO`) "
            "comparando las probabilidades Bivariadas Poisson + Monte Carlo contra el marcador oficial de ESPN."
        )

        completed_games = [g for g in analyzed_games if g.get("audit", {}).get("has_result")]

        if not completed_games:
            st.info(
                "🕒 Aún no hay partidos finalizados en la fecha seleccionada. "
                "Usa el botón **◀ Ayer** para auditar resultados cerrados o activa la cartelera Demo."
            )
        else:
            brier_scores = [g["audit"]["brier_score"] for g in completed_games]
            log_losses = [g["audit"]["log_loss"] for g in completed_games]
            mae_totals = [g["audit"]["total_abs_error"] for g in completed_games]
            ml_hits = [1 if g["audit"]["ml_hit"] else 0 for g in completed_games]
            pnl_list = [g["audit"]["best_bet_pnl_u"] for g in completed_games]

            a_col1, a_col2, a_col3, a_col4, a_col5 = st.columns(5)
            a_col1.metric("Partidos Finalizados", f"{len(completed_games)}")
            a_col2.metric("Acierto Favorito ML", f"{np.mean(ml_hits) * 100:.1f}%")
            a_col3.metric("Brier Score Medio", f"{np.mean(brier_scores):.4f}", help="Menor es mejor (0.25 es azar).")
            a_col4.metric("MAE Total Goles", f"{np.mean(mae_totals):.2f} goles")
            a_col5.metric(
                "PnL Picks Sharp (1u)",
                f"{np.sum(pnl_list):+.2f} u",
                delta=f"ROI {(np.sum(pnl_list) / len(completed_games)) * 100:+.1f}%",
            )

            audit_table = []
            for g in completed_games:
                au = g["audit"]
                bb = g["best_bet"]
                audit_table.append(
                    {
                        "Partido": f"{g['away_abbr']} @ {g['home_abbr']}",
                        "Marcador Oficial": au["actual_score_str"],
                        "Proyección Goles MC": f"{g['proj_away_goals']:.2f} - {g['proj_home_goals']:.2f} (Tot {g['proj_total_goals']:.2f})",
                        "Prob. ML (Vis / Loc)": f"{g['prob_away_ml_pct']:.1f}% / {g['prob_home_ml_pct']:.1f}%",
                        "Pick Principal": f"{bb['selection']} @ {bb['mkt_odds']:.2f} ({bb['ev_pct']:+.1f}% EV)",
                        "Estado Pick": au["best_bet_status"],
                        "PnL (u)": au["best_bet_pnl_u"],
                        "Brier Score": au["brier_score"],
                        "Log Loss": au["log_loss"],
                        "Error Total Goles": au["total_abs_error"],
                    }
                )

            st.dataframe(pd.DataFrame(audit_table), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🏛️ Power Ratings de las 32 Franquicias NHL (`nhl_stats.xlsx`)")
        power_df = stats_df.copy()
        power_df["Net_xG_Diff"] = (power_df["xGF_Game"] - power_df["xGA_Game"]).round(2)
        power_df["Net_Goal_Diff"] = (power_df["Goals_For_Game"] - power_df["Goals_Against_Game"]).round(2)
        power_df = power_df.sort_values(by="Net_xG_Diff", ascending=False).reset_index(drop=True)
        st.dataframe(power_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
