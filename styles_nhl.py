"""
styles_nhl.py
Inyección de estilos CSS Dark Mode / Cyberpunk ("TERMINAL SHARP: NHL QUANT")
y componentes HTML responsivos con badges verdes neón para señales +EV.
"""

from typing import Any, Dict
import streamlit as st


def inject_cyberpunk_styles() -> None:
    """Inyecta la hoja de estilos Dark Mode / Cyberpunk en la aplicación Streamlit."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;600;700;800&display=swap');

        :root {
            --bg-primary: #070b14;
            --bg-card: #0d1424;
            --bg-card-alt: #121c32;
            --border-cyan: #00f0ff;
            --neon-green: #00ff88;
            --neon-amber: #ffb800;
            --neon-red: #ff3366;
            --text-main: #e6f1ff;
            --text-muted: #8b9bb4;
        }

        .stApp {
            background: radial-gradient(circle at 15% 10%, #0f1b33 0%, #070b14 60%, #05070d 100%);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
        }

        /* Header Cyber Terminal */
        .terminal-banner {
            background: linear-gradient(135deg, rgba(13, 20, 36, 0.95) 0%, rgba(9, 29, 52, 0.9) 100%);
            border: 1px solid rgba(0, 240, 255, 0.35);
            border-left: 5px solid #00f0ff;
            border-radius: 12px;
            padding: 18px 24px;
            margin-bottom: 18px;
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.12);
        }
        .terminal-title {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.65rem;
            font-weight: 800;
            letter-spacing: 1.2px;
            color: #ffffff;
            margin: 0;
            text-shadow: 0 0 12px rgba(0, 240, 255, 0.45);
        }
        .terminal-subtitle {
            color: #8b9bb4;
            font-size: 0.88rem;
            margin-top: 4px;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Tarjetas responsivas de partido */
        .nhl-game-card {
            background: linear-gradient(180deg, rgba(16, 25, 46, 0.96) 0%, rgba(10, 16, 30, 0.98) 100%);
            border: 1px solid rgba(0, 240, 255, 0.22);
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 16px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.55);
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        .nhl-game-card:hover {
            border-color: rgba(0, 255, 136, 0.55);
            box-shadow: 0 8px 26px rgba(0, 255, 136, 0.12);
        }

        .card-top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 10px;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }

        .matchup-heading {
            font-size: 1.18rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 0.4px;
        }

        .goalie-strip {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            background: rgba(6, 11, 22, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 8px;
            padding: 8px 12px;
            margin-bottom: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.80rem;
            color: #b8c7e0;
            flex-wrap: wrap;
        }

        /* Grid de mercados dentro de la tarjeta */
        .markets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 12px;
            margin-top: 10px;
        }

        .market-box {
            background: rgba(8, 13, 25, 0.85);
            border: 1px solid rgba(0, 240, 255, 0.16);
            border-radius: 9px;
            padding: 11px 13px;
        }
        .market-box-title {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #00f0ff;
            margin-bottom: 7px;
            font-weight: 700;
        }
        .market-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 4px 0;
            font-size: 0.84rem;
            border-bottom: 1px dashed rgba(255, 255, 255, 0.06);
        }
        .market-row:last-child {
            border-bottom: none;
        }

        /* Badges verdes neón para señales +EV */
        .badge-ev-plus {
            display: inline-block;
            background: rgba(0, 255, 136, 0.16);
            color: #00ff88;
            border: 1px solid #00ff88;
            border-radius: 6px;
            padding: 2px 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            font-weight: 700;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.25);
        }

        .badge-ev-neutral {
            display: inline-block;
            background: rgba(139, 155, 180, 0.12);
            color: #9aa8c0;
            border: 1px solid rgba(139, 155, 180, 0.3);
            border-radius: 6px;
            padding: 2px 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
        }

        .badge-status {
            display: inline-block;
            background: rgba(0, 240, 255, 0.12);
            color: #00f0ff;
            border: 1px solid rgba(0, 240, 255, 0.4);
            border-radius: 6px;
            padding: 2px 9px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .sharp-signal-footer {
            margin-top: 12px;
            padding: 9px 14px;
            border-radius: 8px;
            background: linear-gradient(90deg, rgba(0, 255, 136, 0.14) 0%, rgba(0, 240, 255, 0.05) 100%);
            border-left: 4px solid #00ff88;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.83rem;
        }

        .no-signal-footer {
            margin-top: 12px;
            padding: 8px 14px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.03);
            border-left: 4px solid #4a5568;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.80rem;
            color: #8b9bb4;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_ev_badge(ev_pct: float, threshold: float = 2.0) -> str:
    """Devuelve un badge HTML verde neón si el EV supera el umbral, o neutro en caso contrario."""
    sign = "+" if ev_pct > 0 else ""
    if ev_pct >= threshold:
        return f'<span class="badge-ev-plus">⚡ {sign}{ev_pct:.1f}% EV</span>'
    return f'<span class="badge-ev-neutral">{sign}{ev_pct:.1f}% EV</span>'


def render_header_banner(date_label: str, total_games: int, sharp_signals_count: int) -> None:
    """Renderiza el encabezado principal estilo terminal cuantitativa."""
    st.markdown(
        f"""
        <div class="terminal-banner">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <p class="terminal-title">🏒 TERMINAL SHARP: NHL QUANT</p>
                    <p class="terminal-subtitle">
                        BIVARIATE POISSON / DIXON-COLES • 5,000 MONTE CARLO (3v3 OT + SO) • GOALIE SV% ADJUSTED
                    </p>
                </div>
                <div style="text-align:right; font-family:'JetBrains Mono', monospace;">
                    <span class="badge-status">📅 FECHA: {date_label}</span>
                    <span class="badge-status" style="margin-left:6px;">🎯 PARTIDOS: {total_games}</span>
                    <span class="badge-ev-plus" style="margin-left:6px;">🔥 SEÑALES +EV: {sharp_signals_count}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_game_card(g: Dict[str, Any], ev_threshold: float = 2.0) -> None:
    """Renderiza una tarjeta responsiva Cyberpunk para un partido analizado de la NHL."""
    away = g["away_abbr"]
    home = g["home_abbr"]
    score_badge = ""
    if g.get("home_score") is not None and g.get("away_score") is not None:
        score_badge = f" • MARCADOR: {away} {g['away_score']} - {g['home_score']} {home}"

    ev_away_ml_html = format_ev_badge(g["ev_away_ml"], ev_threshold)
    ev_home_ml_html = format_ev_badge(g["ev_home_ml"], ev_threshold)

    ev_away_pl_html = format_ev_badge(g["ev_away_pl"], ev_threshold)
    ev_home_pl_html = format_ev_badge(g["ev_home_pl"], ev_threshold)

    ev_over_html = format_ev_badge(g["ev_over"], ev_threshold)
    ev_under_html = format_ev_badge(g["ev_under"], ev_threshold)

    bb = g["best_bet"]
    if bb["ev_pct"] >= ev_threshold:
        footer_html = f"""
        <div class="sharp-signal-footer">
            <div>
                <strong style="color:#00ff88;">🟢 SEÑAL SHARP DETECTADA:</strong>
                <span style="color:#ffffff; font-weight:700; margin-left:6px;">{bb['selection']} ({bb['market']})</span>
                <span style="color:#8b9bb4; margin-left:8px;">| Cuota Mkt: <b>{bb['mkt_odds']:.2f}</b> vs Justa: <b>{bb['fair_odds']:.2f}</b></span>
            </div>
            <div>
                <span class="badge-ev-plus">+{bb['ev_pct']:.2f}% EV</span>
                <span class="badge-status" style="margin-left:6px;">Kelly 1/4: {bb['kelly_pct']:.2f}%</span>
            </div>
        </div>
        """
    else:
        footer_html = f"""
        <div class="no-signal-footer">
            ⚪ SIN SEÑAL +EV (&ge;{ev_threshold:.1f}%): Mejor línea relativa <b>{bb['selection']}</b>
            (Cuota {bb['mkt_odds']:.2f} | Justa {bb['fair_odds']:.2f} | EV {bb['ev_pct']:+.2f}%)
        </div>
        """

    card_html = f"""
    <div class="nhl-game-card">
        <div class="card-top-bar">
            <div>
                <span class="matchup-heading">{g['away_name']} ({away}) @ {g['home_name']} ({home})</span>
                <div style="font-size:0.78rem; color:#8b9bb4; margin-top:2px;">
                    🏟️ {g['venue']} • Proveedor: {g['provider']}
                </div>
            </div>
            <div>
                <span class="badge-status">{g['status_detail']}{score_badge}</span>
                <span class="badge-status" style="margin-left:6px;">OT Prob: {g['prob_ot_pct']:.1f}%</span>
            </div>
        </div>

        <div class="goalie-strip">
            <div>🥅 <b>{away} Goalie:</b> {g['away_goalie']} (SV% {g['away_sv_pct']:.3f}) | <b>xG Reg:</b> {g['lambda_away_reg']:.2f} | <b>Proy MC:</b> {g['proj_away_goals']:.2f}</div>
            <div>🥅 <b>{home} Goalie:</b> {g['home_goalie']} (SV% {g['home_sv_pct']:.3f}) | <b>xG Reg:</b> {g['lambda_home_reg']:.2f} | <b>Proy MC:</b> {g['proj_home_goals']:.2f}</div>
            <div>⚡ <b>Total Proy (incl. OT/ENG):</b> <span style="color:#00f0ff; font-weight:700;">{g['proj_total_goals']:.2f} goles</span></div>
        </div>

        <div class="markets-grid">
            <!-- MONEYLINE -->
            <div class="market-box">
                <div class="market-box-title">🏒 MONEYLINE (INC. 3v3 OT/SO)</div>
                <div class="market-row">
                    <span><b>{away} ML</b> ({g['prob_away_ml_pct']:.1f}%)</span>
                    <span>Mkt: <b>{g['away_ml_dec']:.2f}</b> <small style="color:#8b9bb4;">(Justa {g['fair_away_ml']:.2f})</small> {ev_away_ml_html}</span>
                </div>
                <div class="market-row">
                    <span><b>{home} ML</b> ({g['prob_home_ml_pct']:.1f}%)</span>
                    <span>Mkt: <b>{g['home_ml_dec']:.2f}</b> <small style="color:#8b9bb4;">(Justa {g['fair_home_ml']:.2f})</small> {ev_home_ml_html}</span>
                </div>
            </div>

            <!-- PUCK LINE -->
            <div class="market-box">
                <div class="market-box-title">🛡️ PUCK LINE (+1.5 / -1.5)</div>
                <div class="market-row">
                    <span><b>{away} {g['away_pl_line']:+.1f}</b> ({g['prob_away_pl_pct']:.1f}%)</span>
                    <span>Mkt: <b>{g['away_pl_dec']:.2f}</b> <small style="color:#8b9bb4;">(Justa {g['fair_away_pl']:.2f})</small> {ev_away_pl_html}</span>
                </div>
                <div class="market-row">
                    <span><b>{home} {g['home_pl_line']:+.1f}</b> ({g['prob_home_pl_pct']:.1f}%)</span>
                    <span>Mkt: <b>{g['home_pl_dec']:.2f}</b> <small style="color:#8b9bb4;">(Justa {g['fair_home_pl']:.2f})</small> {ev_home_pl_html}</span>
                </div>
            </div>

            <!-- TOTALES -->
            <div class="market-box">
                <div class="market-box-title">🚨 TOTAL GOLES (LÍNEA {g['total_line']:.1f})</div>
                <div class="market-row">
                    <span><b>Over {g['total_line']:.1f}</b> ({g['prob_over_pct']:.1f}%)</span>
                    <span>Mkt: <b>{g['over_dec']:.2f}</b> <small style="color:#8b9bb4;">(Justa {g['fair_over']:.2f})</small> {ev_over_html}</span>
                </div>
                <div class="market-row">
                    <span><b>Under {g['total_line']:.1f}</b> ({g['prob_under_pct']:.1f}%)</span>
                    <span>Mkt: <b>{g['under_dec']:.2f}</b> <small style="color:#8b9bb4;">(Justa {g['fair_under']:.2f})</small> {ev_under_html}</span>
                </div>
            </div>
        </div>

        {footer_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
