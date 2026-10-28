"""
app_nhl.py
Aplicación principal Streamlit — "TERMINAL SHARP: NHL QUANT".
Interfaz visual idéntica a 'TERMINAL SHARP: NFL QUANT':
- Configuración de página en ancho completo: st.set_page_config(layout="wide", page_title="TERMINAL SHARP: NHL QUANT").
- Rejilla estricta de 3 columnas (col1, col2, col3 = st.columns(3)) formando una matriz limpia (3x3).
- Todas las llamadas a st.markdown() que renderizan tarjetas HTML incluyen explícitamente unsafe_allow_html=True
  y strings HTML sin indentación de 4 espacios para evitar bloques de código Markdown.
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
from styles_nhl import (
    build_game_card_html,
    build_header_banner_html,
    inject_cyberpunk_styles,
)
from sync_espn_nhl import fetch_nhl_scoreboard, format_date_yyyymmdd, get_demo_slate

st.set_page_config(
    layout="wide",
    page_title="TERMINAL SHARP: NHL QUANT",
    page_icon="🏒",
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


def render_card_in_column(g: Dict[str, Any], hfa_goals: float, ev_threshold: float) -> None:
    """
    Imprime el bloque HTML de la tarjeta del partido en Streamlit con unsafe_allow_html=True
    y sin indentaciones de 4 espacios, seguido del expander de análisis detallado.
    """
    card_html = build_game_card_html(g, hfa_goals=hfa_goals, ev_threshold=ev_threshold)
    st.markdown(card_html, unsafe_allow_html=True)

    away = g["away_abbr"]
    home = g["home_abbr"]
    bb = g["best_bet"]

    with st.expander("ANÁLISIS DETALLADO →", expanded=False):
        detail_lines = [
            f"<div><b>⚡ Simulación Monte Carlo ({g.get('prob_ot_pct', 0):.1f}% prob. 3v3 OT | {g.get('prob_so_pct', 0):.1f}% Shootout)</b></div>",
            f"<div>• <b>Goles Esperados Regulación (60m):</b> <code>{away} {g['lambda_away_reg']:.2f}</code> vs <code>{home} {g['lambda_home_reg']:.2f}</code></div>",
            f"<div>• <b>Moneyline (Sin Empate):</b></div>",
            f"<div>&nbsp;&nbsp;◦ <code>{away} ML</code>: Prob <b>{g['prob_away_ml_pct']:.1f}%</b> | Justa <b>{g['fair_away_ml']:.2f}</b> | Mkt <b>{g['away_ml_dec']:.2f}</b> (<code>EV {g['ev_away_ml']:+.1f}%</code>)</div>",
            f"<div>&nbsp;&nbsp;◦ <code>{home} ML</code>: Prob <b>{g['prob_home_ml_pct']:.1f}%</b> | Justa <b>{g['fair_home_ml']:.2f}</b> | Mkt <b>{g['home_ml_dec']:.2f}</b> (<code>EV {g['ev_home_ml']:+.1f}%</code>)</div>",
            f"<div>• <b>Puck Line (+1.5 / -1.5):</b></div>",
            f"<div>&nbsp;&nbsp;◦ <code>{away} {g['away_pl_line']:+.1f}</code>: Prob <b>{g['prob_away_pl_pct']:.1f}%</b> | Justa <b>{g['fair_away_pl']:.2f}</b> | Mkt <b>{g['away_pl_dec']:.2f}</b> (<code>EV {g['ev_away_pl']:+.1f}%</code>)</div>",
            f"<div>&nbsp;&nbsp;◦ <code>{home} {g['home_pl_line']:+.1f}</code>: Prob <b>{g['prob_home_pl_pct']:.1f}%</b> | Justa <b>{g['fair_home_pl']:.2f}</b> | Mkt <b>{g['home_pl_dec']:.2f}</b> (<code>EV {g['ev_home_pl']:+.1f}%</code>)</div>",
            f"<div>• <b>Totales (Línea {g['total_line']:.1f}):</b></div>",
            f"<div>&nbsp;&nbsp;◦ <code>OVER {g['total_line']:.1f}</code>: Prob <b>{g['prob_over_pct']:.1f}%</b> | Justa <b>{g['fair_over']:.2f}</b> | Mkt <b>{g['over_dec']:.2f}</b> (<code>EV {g['ev_over']:+.1f}%</code>)</div>",
            f"<div>&nbsp;&nbsp;◦ <code>UNDER {g['total_line']:.1f}</code>: Prob <b>{g['prob_under_pct']:.1f}%</b> | Justa <b>{g['fair_under']:.2f}</b> | Mkt <b>{g['under_dec']:.2f}</b> (<code>EV {g['ev_under']:+.1f}%</code>)</div>",
            f"<div>• <b>Quarter-Kelly Stake Sugerido ({bb['selection']}):</b> <code>{bb['kelly_pct']:.2f}%</code> de banca</div>",
        ]
        st.markdown("\n".join(detail_lines), unsafe_allow_html=True)


def main() -> None:
    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = date.today()

    # -------------------------------------------------------------------------
    # SIDEBAR: CONFIGURACIÓN, BASE DE DATOS Y PARÁMETROS DEL MOTOR
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("<h3>⚙️ CONTROL QUANT NHL</h3>", unsafe_allow_html=True)
        st.caption("Base de Datos de 32 Franquicias & Goalies")

        if not os.path.exists(NHL_DEFAULT_FILENAME):
            ensure_nhl_stats_excel(NHL_DEFAULT_FILENAME)

        st.success(f"💾 Respaldo activo: `{NHL_DEFAULT_FILENAME}`")

        uploaded_excel = st.file_uploader(
            "📂 Cargar `nhl_stats.xlsx` personalizado (Opcional)",
            type=["xlsx"],
            help="Si no subes ningún archivo, la terminal utiliza automáticamente 'nhl_stats.xlsx' en la raíz.",
        )

        stats_df = load_team_stats(uploaded_excel)

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("<h3>🧮 PARÁMETROS PUCK-ENGINE</h3>", unsafe_allow_html=True)
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
            help="Porcentaje mínimo de Valor Esperado para activar el badge verde neón.",
        )
        use_demo_if_empty = st.checkbox(
            "Activar cartelera Demo (3x3) si no hay juegos",
            value=True,
            help="Muestra 9 partidos de demostración en matriz 3x3 cuando ESPN devuelve 0 juegos en la fecha.",
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

    total_sharp_signals = sum(1 for g in analyzed_games if g["best_bet"]["ev_pct"] >= ev_threshold)
    banner_html = build_header_banner_html(
        date_label=active_date.strftime("%Y-%m-%d"),
        total_games=len(analyzed_games),
        sharp_signals_count=total_sharp_signals,
    )
    st.markdown(banner_html, unsafe_allow_html=True)

    if espn_data.get("error"):
        st.warning(f"⚠️ {espn_data['error']}")
    if is_demo_mode:
        st.caption(
            f"ℹ️ Sin juegos oficiales en ESPN para `{date_yyyymmdd}` — "
            "Mostrando matriz 3x3 de calibración (puedes cambiar la fecha o desactivar el modo Demo en el panel lateral)."
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
    # PESTAÑA 1: CARTELERA & MOMIOS EN VIVO (REJILLA ESTRICTA DE 3 COLUMNAS)
    # =========================================================================
    with tab_live:
        if not analyzed_games:
            st.warning("No se encontraron partidos para la fecha seleccionada.")
        else:
            for row_start in range(0, len(analyzed_games), 3):
                col1, col2, col3 = st.columns(3)
                row_cols = (col1, col2, col3)
                row_slice = analyzed_games[row_start : row_start + 3]

                for col_idx, game_item in enumerate(row_slice):
                    with row_cols[col_idx]:
                        render_card_in_column(
                            game_item,
                            hfa_goals=hfa_goals,
                            ev_threshold=ev_threshold,
                        )

            with st.expander("📊 Tabla Maestra de Cuotas Decimales & Líneas Alternativas (5.5 / 6.0 / 6.5)"):
                st.dataframe(export_df, use_container_width=True, hide_index=True)

    # =========================================================================
    # PESTAÑA 2: AUDITORÍA & CALIBRACIÓN POST-PARTIDO
    # =========================================================================
    with tab_audit:
        st.markdown("<h4>📈 Auditoría Post-Partido & Calibración Probabilística</h4>", unsafe_allow_html=True)
        st.caption(
            "Evalúa automáticamente los partidos finalizados (`Final` / `Final/OT` / `Final/SO`) "
            "comparando las probabilidades Bivariadas Poisson + Monte Carlo contra el marcador oficial de ESPN."
        )

        completed_games = [g for g in analyzed_games if g.get("audit", {}).get("has_result")]

        if not completed_games:
            st.info(
                "🕒 Aún no hay partidos finalizados en la fecha seleccionada. "
                "Usa el botón **◀ Ayer** para auditar resultados cerrados."
            )
        else:
            brier_scores = [g["audit"]["brier_score"] for g in completed_games]
            mae_totals = [g["audit"]["total_abs_error"] for g in completed_games]
            ml_hits = [1 if g["audit"]["ml_hit"] else 0 for g in completed_games]
            pnl_list = [g["audit"]["best_bet_pnl_u"] for g in completed_games]

            a_col1, a_col2, a_col3, a_col4, a_col5 = st.columns(5)
            a_col1.metric("Partidos Finalizados", f"{len(completed_games)}")
            a_col2.metric("Acierto Favorito ML", f"{np.mean(ml_hits) * 100:.1f}%")
            a_col3.metric("Brier Score Medio", f"{np.mean(brier_scores):.4f}")
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
                        "Proyección Puck-Engine": f"{g['away_abbr']} {g['proj_away_goals']:.1f} - {g['proj_home_goals']:.1f} {g['home_abbr']}",
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

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("<h4>🏛️ Power Ratings de las 32 Franquicias NHL (<code>nhl_stats.xlsx</code>)</h4>", unsafe_allow_html=True)
        power_df = stats_df.copy()
        power_df["Net_xG_Diff"] = (power_df["xGF_Game"] - power_df["xGA_Game"]).round(2)
        power_df["Net_Goal_Diff"] = (power_df["Goals_For_Game"] - power_df["Goals_Against_Game"]).round(2)
        power_df = power_df.sort_values(by="Net_xG_Diff", ascending=False).reset_index(drop=True)
        st.dataframe(power_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
