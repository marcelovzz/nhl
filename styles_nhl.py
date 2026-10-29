"""
styles_nhl.py
Inyección de estilos CSS y generación de HTML sin indentación para tarjetas de 'TERMINAL SHARP: NHL QUANT',
idéntico al diseño de los módulos de NFL y NBA:
- Tarjetas simétricas con 'min-height: 560px' y 'display: flex; flex-direction: column; justify-content: space-between'
  para alinear perfectamente los botones 'LEER ANÁLISIS →' en cada fila de la cuadrícula 3x3.
- Caja analítica con fondo '#0d1117' y borde acentuado '#00ffcc' mostrando el
  '📊 DESGLOSE 5,000 SIMULACIONES (MONTE CARLO)' (Moneyline, Puck Line +/-1.5 y Total O/U).
- Resaltado en verde neón (#00ffcc / #2bd99f) en líneas con +EV y badge '⚪ LÍNEA SIN EDGE' cuando no hay ventaja.
"""

from typing import Any, Dict
import streamlit as st
from sync_espn_nhl import get_team_logo_url


def _clean_html(raw_html: str) -> str:
    """
    Elimina espacios iniciales de cada línea y líneas vacías para evitar que el parser
    Markdown de Streamlit interprete líneas con >=4 espacios como bloques de código <pre><code>.
    """
    return "\n".join(line.strip() for line in raw_html.splitlines() if line.strip())


def inject_cyberpunk_styles() -> None:
    """Inyecta la hoja de estilos Dark Mode idéntica a los módulos NFL y NBA de TERMINAL SHARP."""
    css_html = _clean_html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
        :root {
            --bg-app: #080c14;
            --card-bg: #0e1621;
            --card-bg-alt: #0d1117;
            --border-neon: rgba(43, 217, 159, 0.35);
            --border-cyan: #00ffcc;
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
        .terminal-banner {
            background: linear-gradient(180deg, #0e1621 0%, #0d1117 100%);
            border: 1px solid rgba(43, 217, 159, 0.35);
            border-left: 4px solid #00ffcc;
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
        /* Simetría estricta en la cuadrícula 3x3: min-height: 560px y display: flex */
        .sharp-card {
            background: linear-gradient(180deg, #0e1621 0%, #0d1117 100%);
            border: 1px solid rgba(43, 217, 159, 0.32);
            border-bottom: none;
            border-radius: 12px 12px 0 0;
            padding: 16px 18px 14px 18px;
            box-shadow: 0 6px 22px rgba(0, 0, 0, 0.6);
            position: relative;
            min-height: 560px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-sizing: border-box;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .sharp-card:hover {
            border-color: #00ffcc;
            box-shadow: 0 6px 25px rgba(0, 255, 204, 0.14);
        }
        .sharp-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .nhl-date-badge {
            background: rgba(0, 255, 204, 0.08);
            border: 1px solid rgba(0, 255, 204, 0.35);
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
        .teams-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 12px;
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
        .puck-engine-box {
            background: rgba(13, 17, 23, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 9px 11px;
            margin-bottom: 10px;
            text-align: center;
        }
        .puck-engine-line1 {
            color: #e6edf3;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.79rem;
            font-weight: 700;
            margin-bottom: 3px;
        }
        .puck-engine-line2 {
            color: #8b949e;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.71rem;
            font-weight: 500;
        }
        /* Caja analítica Monte Carlo con fondo '#0d1117' y borde acentuado '#00ffcc' */
        .mc-breakdown-box {
            background-color: #0d1117;
            border: 1px solid rgba(0, 255, 204, 0.35);
            border-left: 3px solid #00ffcc;
            border-radius: 8px;
            padding: 11px 13px;
            margin-bottom: 12px;
            font-family: 'JetBrains Mono', monospace;
        }
        .mc-breakdown-title {
            color: #00ffcc;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 1px dashed rgba(0, 255, 204, 0.22);
        }
        .mc-breakdown-item {
            color: #d0d7de;
            font-size: 0.73rem;
            line-height: 1.45;
            margin-bottom: 6px;
            display: flex;
            flex-direction: column;
        }
        .mc-breakdown-item:last-child {
            margin-bottom: 0;
        }
        .neon-ev-text {
            color: #00ffcc;
            font-weight: 700;
            text-shadow: 0 0 8px rgba(0, 255, 204, 0.3);
        }
        .neon-green-text {
            color: #2bd99f;
            font-weight: 700;
        }
        .ev-badge-positive {
            background-color: #0f382c;
            border: 1px solid #2bd99f;
            color: #00ffcc;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.77rem;
            font-weight: 800;
            text-align: center;
            padding: 9px 10px;
            border-radius: 7px;
            letter-spacing: 0.4px;
            box-shadow: inset 0 0 12px rgba(43, 217, 159, 0.18), 0 0 10px rgba(43, 217, 159, 0.15);
            text-transform: uppercase;
            margin-top: auto;
        }
        .ev-badge-neutral {
            background-color: rgba(22, 27, 34, 0.92);
            border: 1px solid rgba(139, 148, 158, 0.28);
            color: #8b949e;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            font-weight: 700;
            text-align: center;
            padding: 9px 10px;
            border-radius: 7px;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            margin-top: auto;
        }
        /* Botón expandible inferior 'LEER ANÁLISIS →' perfectamente alineado */
        div[data-testid="stExpander"] {
            background: #0d1117 !important;
            border: 1px solid rgba(43, 217, 159, 0.32) !important;
            border-top: 1px solid rgba(0, 255, 204, 0.22) !important;
            border-radius: 0 0 12px 12px !important;
            margin-top: -1rem !important;
            margin-bottom: 18px !important;
            overflow: hidden;
        }
        div[data-testid="stExpander"] details summary {
            background: rgba(14, 22, 33, 0.96) !important;
            color: #00ffcc !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.76rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px !important;
            padding: 9px 14px !important;
        }
        div[data-testid="stExpander"] details summary:hover {
            color: #2bd99f !important;
            background: rgba(15, 56, 44, 0.45) !important;
        }
        </style>
        """
    )
    st.markdown(css_html, unsafe_allow_html=True)


def build_header_banner_html(date_label: str, total_games: int, sharp_signals_count: int) -> str:
    """Construye el HTML sin indentación para el encabezado superior de la terminal."""
    raw = f"""
<div class="terminal-banner">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
<div>
<p class="terminal-title">🏒 TERMINAL SHARP: NHL QUANT</p>
<p class="terminal-subtitle">PUCK-ENGINE BIVARIATE POISSON / DIXON-COLES • 5,000 MONTE CARLO (3v3 OT + SO) • GOALIE SV%</p>
</div>
<div style="display:flex; gap:8px; align-items:center; font-family:'JetBrains Mono', monospace;">
<span class="nhl-date-badge">📅 {date_label}</span>
<span class="nhl-date-badge">🏒 PARTIDOS: {total_games}</span>
<span class="nhl-date-badge" style="background:#0f382c; border-color:#2bd99f; color:#00ffcc;">🔥 SEÑALES +EV: {sharp_signals_count}</span>
</div>
</div>
</div>
"""
    return _clean_html(raw)


def render_header_banner(date_label: str, total_games: int, sharp_signals_count: int) -> None:
    """Renderiza el encabezado superior de la terminal con unsafe_allow_html=True."""
    st.markdown(
        build_header_banner_html(date_label, total_games, sharp_signals_count),
        unsafe_allow_html=True,
    )


def build_game_card_html(g: Dict[str, Any], hfa_goals: float = 0.28, ev_threshold: float = 2.0) -> str:
    """
    Genera el HTML simétrico (min-height: 560px, display: flex) de la tarjeta NHL con:
    - Encabezado, logos, nombres y marcadores proyectados en verde neón (#2bd99f)
    - Bloque central Puck-Engine
    - Caja analítica '#0d1117' con borde '#00ffcc':
      * 📊 DESGLOSE 5,000 SIMULACIONES (MONTE CARLO)
      * 🏒 Moneyline [Equipo]: XX.X% | Casas: XX.X% | ESPN: XX.X%
      * 🛡️ Puck Line [Equipo] ([+/-1.5]): XX.X% cubre
      * 🎯 Total ([Línea O/U]): Más de [Línea] en XX.X% (Menos: XX.X%)
    - Badge de Valor (+EV) o '⚪ LÍNEA SIN EDGE'
    """
    away = g["away_abbr"]
    home = g["home_abbr"]

    away_logo = g.get("away_logo") or get_team_logo_url(away)
    home_logo = g.get("home_logo") or get_team_logo_url(home)

    raw_date = str(g.get("date_yyyymmdd", ""))
    formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}" if len(raw_date) == 8 else raw_date

    time_or_status = g.get("status_detail", "7:00 PM ET")
    if g.get("is_completed") and g.get("home_score") is not None and g.get("away_score") is not None:
        time_or_status = f"{time_or_status} ({away} {g['away_score']} - {g['home_score']} {home})"

    proj_away = g["proj_away_goals"]
    proj_home = g["proj_home_goals"]
    proj_total = g["proj_total_goals"]

    fair_away = g["fair_away_ml"]
    fair_home = g["fair_home_ml"]

    # Datos para el bloque "📊 DESGLOSE 5,000 SIMULACIONES (MONTE CARLO)"
    ml_team_label = g.get("ml_focus_team", g["home_name"])
    ml_model_pct = g.get("ml_focus_model_pct", g["prob_home_ml_pct"])
    ml_mkt_pct = g.get("ml_focus_mkt_pct", g.get("mkt_home_ml_devig_pct", 50.0))
    ml_espn_pct = g.get("ml_focus_espn_pct", g.get("espn_home_wp_pct", 50.0))
    ml_ev = g.get("ml_focus_ev_pct", max(g["ev_home_ml"], g["ev_away_ml"]))

    pl_team_label = g.get("pl_focus_team", g["home_name"])
    pl_line_val = float(g.get("pl_focus_line", g["home_pl_line"]))
    pl_cover_pct = g.get("pl_focus_cover_pct", g["prob_home_pl_pct"])
    pl_ev = g.get("pl_focus_ev_pct", max(g["ev_home_pl"], g["ev_away_pl"]))

    total_line = float(g.get("total_line", 6.0))
    over_pct = g["prob_over_pct"]
    under_pct = g["prob_under_pct"]
    tot_ev = max(g["ev_over"], g["ev_under"])

    ml_cls = "neon-ev-text" if ml_ev >= ev_threshold else "neon-green-text"
    pl_cls = "neon-ev-text" if pl_ev >= ev_threshold else "neon-green-text"
    tot_cls = "neon-ev-text" if tot_ev >= ev_threshold else "neon-green-text"

    ml_ev_tag = f' <span class="neon-ev-text">[+{ml_ev:.1f}% EV]</span>' if ml_ev >= ev_threshold else ""
    pl_ev_tag = f' <span class="neon-ev-text">[+{pl_ev:.1f}% EV]</span>' if pl_ev >= ev_threshold else ""
    tot_ev_tag = f' <span class="neon-ev-text">[+{tot_ev:.1f}% EV]</span>' if tot_ev >= ev_threshold else ""

    bb = g["best_bet"]
    if bb["ev_pct"] >= ev_threshold:
        sel_upper = str(bb["selection"]).upper()
        ev_badge_html = (
            f'<div class="ev-badge-positive">'
            f'🔥 VALOR: {sel_upper} ({bb["mkt_odds"]:.2f}) | EV: +{bb["ev_pct"]:.1f}%'
            f"</div>"
        )
    else:
        ev_badge_html = '<div class="ev-badge-neutral">⚪ LÍNEA SIN EDGE</div>'

    raw_card = f"""
<div class="sharp-card">
<div>
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
<div class="puck-engine-line1">Proyección Puck-Engine: {away} {proj_away:.1f} - {proj_home:.1f} {home}</div>
<div class="puck-engine-line2">Cuota Justa ML: {away} {fair_away:.2f} | {home} {fair_home:.2f} &middot; Total Proy: {proj_total:.1f} &middot; HFA +{hfa_goals:.2f}</div>
</div>
<div class="mc-breakdown-box">
<div class="mc-breakdown-title">📊 DESGLOSE 5,000 SIMULACIONES (MONTE CARLO)</div>
<div class="mc-breakdown-item">
<span>🏒 <b>Moneyline {ml_team_label}:</b> <span class="{ml_cls}">{ml_model_pct:.1f}%</span> | Casas: {ml_mkt_pct:.1f}% | ESPN: {ml_espn_pct:.1f}%{ml_ev_tag}</span>
</div>
<div class="mc-breakdown-item">
<span>🛡️ <b>Puck Line {pl_team_label} ({pl_line_val:+.1f}):</b> <span class="{pl_cls}">{pl_cover_pct:.1f}% cubre</span>{pl_ev_tag}</span>
</div>
<div class="mc-breakdown-item">
<span>🎯 <b>Total ({total_line:.1f}):</b> Más de {total_line:.1f} en <span class="{tot_cls}">{over_pct:.1f}%</span> (Menos: {under_pct:.1f}%){tot_ev_tag}</span>
</div>
</div>
</div>
{ev_badge_html}
</div>
"""
    return _clean_html(raw_card)


def render_game_card(g: Dict[str, Any], hfa_goals: float = 0.28, ev_threshold: float = 2.0) -> None:
    """
    Renderiza la tarjeta individual de partido con unsafe_allow_html=True,
    seguida por el botón expandible 'LEER ANÁLISIS →' perfectamente alineado.
    """
    away = g["away_abbr"]
    home = g["home_abbr"]
    bb = g["best_bet"]

    card_html = build_game_card_html(g, hfa_goals=hfa_goals, ev_threshold=ev_threshold)
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander("LEER ANÁLISIS →", expanded=False):
        detail_lines = [
            f"<div><b>⚡ Simulación Monte Carlo ({g.get('n_sims', 5000):,} iteraciones | {g.get('prob_ot_pct', 0):.1f}% prob. 3v3 OT | {g.get('prob_so_pct', 0):.1f}% Shootout)</b></div>",
            f"<div>• <b>Goles Esperados Regulación (60m):</b> <code>{away} {g['lambda_away_reg']:.2f}</code> vs <code>{home} {g['lambda_home_reg']:.2f}</code></div>",
            f"<div>• <b>Moneyline (Modelo vs Casas Desvigilado vs ESPN):</b></div>",
            f"<div>&nbsp;&nbsp;◦ <code>{away} ML</code>: Modelo <b>{g['prob_away_ml_pct']:.1f}%</b> | Casas <b>{g['mkt_away_ml_devig_pct']:.1f}%</b> | ESPN <b>{g['espn_away_wp_pct']:.1f}%</b> | Mkt <b>{g['away_ml_dec']:.2f}</b> (<code>EV {g['ev_away_ml']:+.1f}%</code>)</div>",
            f"<div>&nbsp;&nbsp;◦ <code>{home} ML</code>: Modelo <b>{g['prob_home_ml_pct']:.1f}%</b> | Casas <b>{g['mkt_home_ml_devig_pct']:.1f}%</b> | ESPN <b>{g['espn_home_wp_pct']:.1f}%</b> | Mkt <b>{g['home_ml_dec']:.2f}</b> (<code>EV {g['ev_home_ml']:+.1f}%</code>)</div>",
            f"<div>• <b>Puck Line / Hándicap (+/-1.5):</b></div>",
            f"<div>&nbsp;&nbsp;◦ <code>{g['fav_pl_name']} cubre -1.5</code> en <b>{g['fav_pl_cover_pct']:.1f}%</b> | <code>{g['dog_pl_name']} cubre +1.5</code> en <b>{g['dog_pl_cover_pct']:.1f}%</b></div>",
            f"<div>&nbsp;&nbsp;◦ Cuotas Mkt: <code>{away} {g['away_pl_line']:+.1f}</code> @ <b>{g['away_pl_dec']:.2f}</b> (<code>EV {g['ev_away_pl']:+.1f}%</code>) | <code>{home} {g['home_pl_line']:+.1f}</code> @ <b>{g['home_pl_dec']:.2f}</b> (<code>EV {g['ev_home_pl']:+.1f}%</code>)</div>",
            f"<div>• <b>Totales Dinámicos (Línea {g['total_line']:.1f}):</b></div>",
            f"<div>&nbsp;&nbsp;◦ <code>Más de {g['total_line']:.1f}</code> en <b>{g['prob_over_pct']:.1f}%</b> (Mkt <b>{g['over_dec']:.2f}</b>, <code>EV {g['ev_over']:+.1f}%</code>) | <code>Menos de {g['total_line']:.1f}</code> en <b>{g['prob_under_pct']:.1f}%</b> (Mkt <b>{g['under_dec']:.2f}</b>, <code>EV {g['ev_under']:+.1f}%</code>)</div>",
            f"<div>• <b>Quarter-Kelly Stake Sugerido ({bb['selection']}):</b> <code>{bb['kelly_pct']:.2f}%</code> de banca</div>",
        ]
        st.markdown("\n".join(detail_lines), unsafe_allow_html=True)
