"""
styles_nhl.py
Inyección de estilos CSS y renderizado de tarjetas idéntico a 'TERMINAL SHARP: NFL QUANT'.
Diseñado para rejilla estricta de 3 columnas (3x3) con fondo '#0e1621', bordes cian/verde,
marcadores proyectados en verde neón (#2bd99f / #00ffcc), bloque central Puck-Engine,
badges de valor (#0f382c) y botón expandible inferior 'ANÁLISIS DETALLADO →'.
"""

from typing import Any, Dict
import streamlit as st
from sync_espn_nhl import get_team_logo_url


def inject_cyberpunk_styles() -> None:
    """Inyecta la hoja de estilos Dark Mode idéntica a 'TERMINAL SHARP: NFL QUANT'."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg-app: #080c14;
            --card-bg: #0e1621;
            --card-bg-alt: #0d1117;
            --border-neon: rgba(43, 217, 159, 0.35);
            --border-cyan: rgba(0, 240, 255, 0.28);
            --neon-score: #2bd99f;
            --neon-bright: #00ffcc;
            --ev-badge-bg: #0f382c;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
        }

        .stApp {
            background-color: var(--bg-app);
            background-image: radial-gradient(circle at 50% 0%, #111c2d 0%, #080c14 70%);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 98% !important;
        }

        /* Banner Superior Terminal Sharp */
        .terminal-banner {
            background: linear-gradient(180deg, #0e1621 0%, #0d1117 100%);
            border: 1px solid rgba(43, 217, 159, 0.35);
            border-left: 4px solid #2bd99f;
            border-radius: 10px;
            padding: 16px 22px;
            margin-bottom: 18px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.55);
        }
        .terminal-title {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: 1px;
            color: #ffffff;
            margin: 0;
        }
        .terminal-subtitle {
            color: #8b949e;
            font-size: 0.82rem;
            margin-top: 4px;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Tarjeta de Partido idéntica a NFL QUANT */
        .sharp-card {
            background: linear-gradient(180deg, #0e1621 0%, #0d1117 100%);
            border: 1px solid rgba(43, 217, 159, 0.32);
            border-bottom: none;
            border-radius: 12px 12px 0 0;
            padding: 16px 18px 14px 18px;
            box-shadow: 0 6px 22px rgba(0, 0, 0, 0.6);
            position: relative;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .sharp-card:hover {
            border-color: #00ffcc;
            box-shadow: 0 6px 25px rgba(0, 255, 204, 0.14);
        }

        /* Encabezado de tarjeta: Badge '🏒 NHL • FECHA' y hora */
        .sharp-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .nhl-date-badge {
            background: rgba(0, 240, 255, 0.08);
            border: 1px solid rgba(0, 240, 255, 0.3);
            color: #00ffcc;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 9px;
            border-radius: 5px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .nhl-time-label {
            color: #8b949e;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            font-weight: 600;
        }

        /* Filas de Equipos (Logo + Nombre a la izquierda, Marcador Proyectado grande a la derecha) */
        .teams-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 14px;
        }
        .team-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .team-info-left {
            display: flex;
            align-items: center;
            gap: 11px;
            min-width: 0;
        }
        .team-logo-img {
            width: 34px;
            height: 34px;
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
            flex-shrink: 0;
        }
        .team-name-block {
            display: flex;
            flex-direction: column;
            line-height: 1.15;
        }
        .team-full-name {
            color: #f0f6fc;
            font-size: 0.98rem;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .team-sub-meta {
            color: #8b949e;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.70rem;
            margin-top: 2px;
        }
        .proj-score-right {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.75rem;
            font-weight: 800;
            color: #2bd99f;
            text-shadow: 0 0 12px rgba(43, 217, 159, 0.35);
            letter-spacing: -0.5px;
            line-height: 1;
            margin-left: 10px;
        }

        /* Bloque central de cuotas y proyección Puck-Engine */
        .puck-engine-box {
            background: rgba(13, 17, 23, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 12px;
            text-align: center;
        }
        .puck-engine-line1 {
            color: #e6edf3;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.80rem;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .puck-engine-line2 {
            color: #8b949e;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 500;
        }

        /* Badges de Valor (+EV) */
        .ev-badge-positive {
            background-color: #0f382c;
            border: 1px solid #2bd99f;
            color: #00ffcc;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            font-weight: 800;
            text-align: center;
            padding: 9px 10px;
            border-radius: 7px;
            letter-spacing: 0.4px;
            box-shadow: inset 0 0 12px rgba(43, 217, 159, 0.18), 0 0 10px rgba(43, 217, 159, 0.15);
            text-transform: uppercase;
        }
        .ev-badge-neutral {
            background-color: rgba(22, 27, 34, 0.9);
            border: 1px solid rgba(139, 148, 158, 0.25);
            color: #8b949e;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            font-weight: 700;
            text-align: center;
            padding: 9px 10px;
            border-radius: 7px;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }

        /* Estilizar el st.expander inferior 'ANÁLISIS DETALLADO →' acoplado a la tarjeta */
        div[data-testid="stExpander"] {
            background: #0d1117 !important;
            border: 1px solid rgba(43, 217, 159, 0.32) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 0 0 12px 12px !important;
            margin-top: -1rem !important;
            margin-bottom: 18px !important;
            overflow: hidden;
        }
        div[data-testid="stExpander"] details summary {
            background: rgba(14, 22, 33, 0.95) !important;
            color: #2bd99f !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.76rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px !important;
            padding: 8px 14px !important;
        }
        div[data-testid="stExpander"] details summary:hover {
            color: #00ffcc !important;
            background: rgba(15, 56, 44, 0.45) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header_banner(date_label: str, total_games: int, sharp_signals_count: int) -> None:
    """Renderiza el encabezado superior de la terminal."""
    st.markdown(
        f"""
        <div class="terminal-banner">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <p class="terminal-title">🏒 TERMINAL SHARP: NHL QUANT</p>
                    <p class="terminal-subtitle">
                        PUCK-ENGINE BIVARIATE POISSON / DIXON-COLES • 5,000 MONTE CARLO (3v3 OT + SO) • GOALIE SV%
                    </p>
                </div>
                <div style="display:flex; gap:8px; align-items:center; font-family:'JetBrains Mono', monospace;">
                    <span class="nhl-date-badge">📅 {date_label}</span>
                    <span class="nhl-date-badge">🏒 PARTIDOS: {total_games}</span>
                    <span class="nhl-date-badge" style="background:#0f382c; border-color:#2bd99f; color:#00ffcc;">
                        🔥 +EV: {sharp_signals_count}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_game_card(g: Dict[str, Any], hfa_goals: float = 0.28, ev_threshold: float = 2.0) -> None:
    """
    Renderiza la tarjeta individual de partido idéntica a 'TERMINAL SHARP: NFL QUANT',
    seguida por el botón expandible 'ANÁLISIS DETALLADO →' ocupando todo el ancho de la tarjeta.
    """
    away = g["away_abbr"]
    home = g["home_abbr"]

    away_logo = g.get("away_logo") or get_team_logo_url(away)
    home_logo = g.get("home_logo") or get_team_logo_url(home)

    raw_date = str(g.get("date_yyyymmdd", ""))
    if len(raw_date) == 8:
        formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    else:
        formatted_date = raw_date

    time_or_status = g.get("status_detail", "7:00 PM ET")
    if g.get("is_completed") and g.get("home_score") is not None and g.get("away_score") is not None:
        time_or_status = f"{time_or_status} ({away} {g['away_score']} - {g['home_score']} {home})"

    proj_away = g["proj_away_goals"]
    proj_home = g["proj_home_goals"]
    proj_total = g["proj_total_goals"]

    fair_away = g["fair_away_ml"]
    fair_home = g["fair_home_ml"]

    bb = g["best_bet"]
    if bb["ev_pct"] >= ev_threshold:
        sel_upper = str(bb["selection"]).upper()
        ev_badge_html = (
            f'<div class="ev-badge-positive">'
            f'🔥 VALOR: {sel_upper} ({bb["mkt_odds"]:.2f}) | EV: +{bb["ev_pct"]:.1f}%'
            f"</div>"
        )
    else:
        ev_badge_html = '<div class="ev-badge-neutral">LÍNEA SIN VALOR</div>'

    card_html = f"""
    <div class="sharp-card">
        <div class="sharp-card-header">
            <span class="nhl-date-badge">🏒 NHL • {formatted_date}</span>
            <span class="nhl-time-label">🕒 {time_or_status}</span>
        </div>

        <div class="teams-container">
            <div class="team-row">
                <div class="team-info-left">
                    <img src="{away_logo}" class="team-logo-img" alt="{away}" onerror="this.style.display='none'"/>
                    <div class="team-name-block">
                        <span class="team-full-name">{g['away_name']}</span>
                        <span class="team-sub-meta">{away} • 🥅 {g['away_goalie']} ({g['away_sv_pct']:.3f})</span>
                    </div>
                </div>
                <div class="proj-score-right">{proj_away:.1f}</div>
            </div>

            <div class="team-row">
                <div class="team-info-left">
                    <img src="{home_logo}" class="team-logo-img" alt="{home}" onerror="this.style.display='none'"/>
                    <div class="team-name-block">
                        <span class="team-full-name">{g['home_name']}</span>
                        <span class="team-sub-meta">{home} • 🥅 {g['home_goalie']} ({g['home_sv_pct']:.3f})</span>
                    </div>
                </div>
                <div class="proj-score-right">{proj_home:.1f}</div>
            </div>
        </div>

        <div class="puck-engine-box">
            <div class="puck-engine-line1">
                Proyección Puck-Engine: {away} {proj_away:.1f} - {proj_home:.1f} {home}
            </div>
            <div class="puck-engine-line2">
                Cuota Justa ML: {away} {fair_away:.2f} | {home} {fair_home:.2f} &middot; Total Proy: {proj_total:.1f} &middot; HFA +{hfa_goals:.2f}
            </div>
        </div>

        {ev_badge_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander("ANÁLISIS DETALLADO →", expanded=False):
        st.markdown(
            f"""
            **⚡ Simulación Monte Carlo ({g.get('prob_ot_pct', 0):.1f}% prob. 3v3 OT | {g.get('prob_so_pct', 0):.1f}% Shootout)**
            - **Goles Esperados Regulación (60m):** `{away} {g['lambda_away_reg']:.2f}` vs `{home} {g['lambda_home_reg']:.2f}`
            - **Moneyline (Sin Empate):**
              - `{away} ML`: Prob **{g['prob_away_ml_pct']:.1f}%** | Justa **{g['fair_away_ml']:.2f}** | Mkt **{g['away_ml_dec']:.2f}** (`EV {g['ev_away_ml']:+.1f}%`)
              - `{home} ML`: Prob **{g['prob_home_ml_pct']:.1f}%** | Justa **{g['fair_home_ml']:.2f}** | Mkt **{g['home_ml_dec']:.2f}** (`EV {g['ev_home_ml']:+.1f}%`)
            - **Puck Line (+1.5 / -1.5):**
              - `{away} {g['away_pl_line']:+.1f}`: Prob **{g['prob_away_pl_pct']:.1f}%** | Justa **{g['fair_away_pl']:.2f}** | Mkt **{g['away_pl_dec']:.2f}** (`EV {g['ev_away_pl']:+.1f}%`)
              - `{home} {g['home_pl_line']:+.1f}`: Prob **{g['prob_home_pl_pct']:.1f}%** | Justa **{g['fair_home_pl']:.2f}** | Mkt **{g['home_pl_dec']:.2f}** (`EV {g['ev_home_pl']:+.1f}%`)
            - **Totales (Línea {g['total_line']:.1f}):**
              - `OVER {g['total_line']:.1f}`: Prob **{g['prob_over_pct']:.1f}%** | Justa **{g['fair_over']:.2f}** | Mkt **{g['over_dec']:.2f}** (`EV {g['ev_over']:+.1f}%`)
              - `UNDER {g['total_line']:.1f}`: Prob **{g['prob_under_pct']:.1f}%** | Justa **{g['fair_under']:.2f}** | Mkt **{g['under_dec']:.2f}** (`EV {g['ev_under']:+.1f}%`)
            - **Quarter-Kelly Stake Sugerido ({bb['selection']}):** `{bb['kelly_pct']:.2f}%` de banca
            """
        )
