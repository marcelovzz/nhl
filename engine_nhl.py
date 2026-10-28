"""
engine_nhl.py
Motor Cuantitativo para NHL ("TERMINAL SHARP: NHL QUANT").
Implementa:
1. Cálculo de goles esperados (xG) con ponderación regresiva (60% xG / 40% Goles reales),
   ajuste de ritmo (Pace_Events), ventaja de localía (HFA ~ +0.28 goles) y factor de Starting_Goalie (Save_Pct).
2. Matriz analítica Bivariada de Poisson con ajuste de baja anotación Dixon-Coles (rho) para tiempo reglamentario (60 min).
3. Simulación Monte Carlo (5,000 iteraciones) con resolución explícita de Tiempo Extra (3v3 OT) y Shootouts (SO)
   para eliminar empates en Moneyline y modelar el gol extra de OT/SO en mercados de Totales y Puck Line.
4. Cálculo de probabilidades justas, cuotas decimales justas y Valor Esperado (+EV%).
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import poisson

# Parámetros globales de calibración NHL
LEAGUE_AVG_GOALS_TEAM = 3.10
LEAGUE_AVG_PACE = 61.2
LEAGUE_AVG_SV_PCT = 0.906
DEFAULT_HFA_GOALS = 0.28  # ~+0.28 goles de ventaja para el equipo local en NHL
DEFAULT_MC_ITERATIONS = 5000
DIXON_COLES_RHO = -0.085  # Ligera sobrerrepresentación de empates en 60 min (1-1, 2-2, 3-3) en hockey


def dixon_coles_tau(x: int, y: int, lam_home: float, lam_away: float, rho: float = DIXON_COLES_RHO) -> float:
    """
    Factor de corrección tau de Dixon-Coles para marcadores bajos/empates en regulación.
    Asegura que los marcadores 0-0, 1-0, 0-1 y 1-1 capturen la correlación defensiva de hockey.
    """
    if x == 0 and y == 0:
        return max(0.01, 1.0 - (lam_home * lam_away * rho))
    if x == 0 and y == 1:
        return max(0.01, 1.0 + (lam_home * rho))
    if x == 1 and y == 0:
        return max(0.01, 1.0 + (lam_away * rho))
    if x == 1 and y == 1:
        return max(0.01, 1.0 - rho)
    return 1.0


def build_bivariate_dixon_coles_matrix(
    lam_home: float,
    lam_away: float,
    cov_lambda3: float = 0.08,
    rho: float = DIXON_COLES_RHO,
    max_goals: int = 12,
) -> np.ndarray:
    """
    Construye la matriz conjunta P(G_home = i, G_away = j) en tiempo reglamentario (60 min)
    combinando una distribución Bivariada de Poisson (componente común cov_lambda3 de ritmo de partido)
    con el kernel de ajuste Dixon-Coles.
    """
    l1 = max(0.35, lam_home - cov_lambda3)
    l2 = max(0.35, lam_away - cov_lambda3)
    l3 = max(0.0, min(cov_lambda3, min(lam_home, lam_away) * 0.25))

    p1 = poisson.pmf(np.arange(max_goals + 1), l1)
    p2 = poisson.pmf(np.arange(max_goals + 1), l2)
    p3 = poisson.pmf(np.arange(max_goals + 1), l3)

    # Convolución bivariada de Poisson: X = X1 + X3, Y = X2 + X3
    matrix = np.zeros((max_goals + 1, max_goals + 1), dtype=float)
    for k in range(max_goals + 1):
        if p3[k] < 1e-9:
            continue
        sub_h = p1[: max_goals + 1 - k]
        sub_a = p2[: max_goals + 1 - k]
        matrix[k:, k:] += p3[k] * np.outer(sub_h, sub_a)

    # Aplicar corrección Dixon-Coles en la esquina (0..1, 0..1)
    for i in (0, 1):
        for j in (0, 1):
            matrix[i, j] *= dixon_coles_tau(i, j, lam_home, lam_away, rho=rho)

    total_mass = matrix.sum()
    if total_mass > 0:
        matrix /= total_mass

    return matrix


def compute_expected_goals(
    home_row: pd.Series,
    away_row: pd.Series,
    hfa_goals: float = DEFAULT_HFA_GOALS,
    goalie_weight: float = 12.5,
) -> Dict[str, Any]:
    """
    Calcula las tasas esperadas de gol (lambda_home, lambda_away) en 60 minutos
    integrando:
    - Fuerza ofensiva/defensiva híbrida (60% xG_Game + 40% Goals_Game)
    - Factor de ritmo (Pace_Events vs promedio NHL)
    - HFA (~+0.28 goles repartidos en +0.14 al local y -0.14 al visitante)
    - Ajuste por Starting_Goalie (Save_Pct relativo a la media de la liga .906)
    """
    # Promedios de la liga dinámicos
    h_off = 0.60 * float(home_row["xGF_Game"]) + 0.40 * float(home_row["Goals_For_Game"])
    h_def = 0.60 * float(home_row["xGA_Game"]) + 0.40 * float(home_row["Goals_Against_Game"])

    a_off = 0.60 * float(away_row["xGF_Game"]) + 0.40 * float(away_row["Goals_For_Game"])
    a_def = 0.60 * float(away_row["xGA_Game"]) + 0.40 * float(away_row["Goals_Against_Game"])

    # Factor de ritmo (Pace)
    match_pace = 0.5 * (float(home_row["Pace_Events"]) + float(away_row["Pace_Events"]))
    pace_multiplier = np.clip(match_pace / LEAGUE_AVG_PACE, 0.88, 1.14)

    # Goles base cruzados (Ataque vs Defensa rival normalizado a media NHL)
    base_lam_home = ((h_off * a_def) / LEAGUE_AVG_GOALS_TEAM) * pace_multiplier
    base_lam_away = ((a_off * h_def) / LEAGUE_AVG_GOALS_TEAM) * pace_multiplier

    # Ajuste por Starting_Goalie (Save_Pct vs media de liga 0.906)
    # Un portero con .918 ahorra goles al rival; uno con .894 concede más.
    home_sv = float(home_row["Save_Pct"])
    away_sv = float(away_row["Save_Pct"])

    # Multiplicador de goles permitidos según el portero rival
    away_goalie_factor = np.clip(1.0 - (away_sv - LEAGUE_AVG_SV_PCT) * goalie_weight, 0.78, 1.24)
    home_goalie_factor = np.clip(1.0 - (home_sv - LEAGUE_AVG_SV_PCT) * goalie_weight, 0.78, 1.24)

    # Aplicar factor de portero y ventaja de localía (HFA ~ +0.28 goles diferenciales)
    lam_home = (base_lam_home * away_goalie_factor) + (hfa_goals * 0.55)
    lam_away = (base_lam_away * home_goalie_factor) - (hfa_goals * 0.45)

    lam_home = float(np.clip(lam_home, 1.45, 5.25))
    lam_away = float(np.clip(lam_away, 1.35, 5.10))

    return {
        "lambda_home_reg": round(lam_home, 3),
        "lambda_away_reg": round(lam_away, 3),
        "match_pace": round(match_pace, 1),
        "home_goalie": str(home_row.get("Starting_Goalie", "TBD")),
        "away_goalie": str(away_row.get("Starting_Goalie", "TBD")),
        "home_sv_pct": round(home_sv, 3),
        "away_sv_pct": round(away_sv, 3),
        "away_goalie_factor": round(float(away_goalie_factor), 3),
        "home_goalie_factor": round(float(home_goalie_factor), 3),
    }


def run_monte_carlo_nhl(
    prob_matrix_reg: np.ndarray,
    lam_home: float,
    lam_away: float,
    n_sims: int = DEFAULT_MC_ITERATIONS,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Ejecuta simulación Monte Carlo (5,000 iteraciones por defecto) muestreando de la distribución
    conjunta Bivariada Poisson / Dixon-Coles en tiempo reglamentario (60 min) y resolviendo:
    - Empates en regulación -> 5 minutos de 3v3 Overtime (~68% se decide en OT proporcional a fuerza ofensiva)
    - Si persiste el empate tras 3v3 OT -> Shootout (SO, ~52% local / 48% visitante ajustado por Save_Pct).
    En NHL, ganar en OT o SO otorga +1 gol oficial al marcador final del equipo ganador.
    """
    rng = np.random.default_rng(seed)
    max_goals = prob_matrix_reg.shape[0] - 1

    flat_probs = prob_matrix_reg.ravel()
    flat_probs = flat_probs / flat_probs.sum()

    sampled_indices = rng.choice(len(flat_probs), size=n_sims, p=flat_probs)
    reg_home_goals = (sampled_indices // (max_goals + 1)).astype(int)
    reg_away_goals = (sampled_indices % (max_goals + 1)).astype(int)

    final_home_goals = reg_home_goals.copy()
    final_away_goals = reg_away_goals.copy()

    ties_mask = reg_home_goals == reg_away_goals
    n_ties = int(np.sum(ties_mask))

    went_ot = np.zeros(n_sims, dtype=bool)
    went_so = np.zeros(n_sims, dtype=bool)

    if n_ties > 0:
        went_ot[ties_mask] = True
        # En 3v3 OT, ~67% de los juegos empatados se resuelven antes del Shootout
        ot_resolution_prob = 0.67
        ot_home_share = np.clip(lam_home / (lam_home + lam_away), 0.38, 0.62)
        so_home_share = np.clip(0.515 + 0.15 * (ot_home_share - 0.5), 0.44, 0.58)

        u_stage = rng.random(n_ties)
        u_winner = rng.random(n_ties)

        resolved_in_ot = u_stage < ot_resolution_prob
        resolved_in_so = ~resolved_in_ot

        tie_indices = np.where(ties_mask)[0]
        went_so[tie_indices[resolved_in_so]] = True

        home_wins_tie = np.where(
            resolved_in_ot,
            u_winner < ot_home_share,
            u_winner < so_home_share,
        )

        # El ganador en OT o Shootout suma +1 gol en el boxscore oficial de NHL (relevante para Totales)
        final_home_goals[tie_indices[home_wins_tie]] += 1
        final_away_goals[tie_indices[~home_wins_tie]] += 1

    # En Puck Line (-1.5 / +1.5), también modelamos Empty Net Goals en los últimos 2 minutos
    # cuando un equipo gana por 1 gol en regulación (~22% de las ventajas de 1 gol en reg terminan en +2 por ENG)
    reg_lead_home_1 = (reg_home_goals - reg_away_goals) == 1
    reg_lead_away_1 = (reg_away_goals - reg_home_goals) == 1

    eng_home = reg_lead_home_1 & (rng.random(n_sims) < 0.18)
    eng_away = reg_lead_away_1 & (rng.random(n_sims) < 0.17)

    final_home_goals[eng_home] += 1
    final_away_goals[eng_away] += 1

    total_goals = final_home_goals + final_away_goals
    goal_diff = final_home_goals - final_away_goals  # >0 significa gana Local

    prob_home_ml = float(np.mean(goal_diff > 0))
    prob_away_ml = float(np.mean(goal_diff < 0))

    # Asegurar que no existan empates en Moneyline
    if prob_home_ml + prob_away_ml > 0:
        norm = prob_home_ml + prob_away_ml
        prob_home_ml /= norm
        prob_away_ml /= norm

    # Probabilidades de Puck Line
    prob_home_minus_1_5 = float(np.mean(goal_diff >= 2))
    prob_away_plus_1_5 = 1.0 - prob_home_minus_1_5

    prob_away_minus_1_5 = float(np.mean(goal_diff <= -2))
    prob_home_plus_1_5 = 1.0 - prob_away_minus_1_5

    return {
        "n_sims": n_sims,
        "final_home_goals": final_home_goals,
        "final_away_goals": final_away_goals,
        "total_goals": total_goals,
        "goal_diff": goal_diff,
        "prob_reg_tie": float(n_ties / n_sims),
        "prob_ot": float(np.mean(went_ot)),
        "prob_so": float(np.mean(went_so)),
        "prob_home_ml": prob_home_ml,
        "prob_away_ml": prob_away_ml,
        "prob_home_minus_1_5": prob_home_minus_1_5,
        "prob_away_plus_1_5": prob_away_plus_1_5,
        "prob_away_minus_1_5": prob_away_minus_1_5,
        "prob_home_plus_1_5": prob_home_plus_1_5,
        "proj_home_goals_final": float(np.mean(final_home_goals)),
        "proj_away_goals_final": float(np.mean(final_away_goals)),
        "proj_total_goals_final": float(np.mean(total_goals)),
    }


def compute_total_market_probs(total_goals_sim: np.ndarray, line: float) -> Tuple[float, float, float]:
    """
    Calcula las probabilidades de Over, Under y Push (para líneas enteras como 6.0)
    y retorna las probabilidades efectivas sin Push (reembolso) para comparar con cuotas decimales.
    """
    p_over_raw = float(np.mean(total_goals_sim > line))
    p_under_raw = float(np.mean(total_goals_sim < line))
    p_push = float(np.mean(total_goals_sim == line))

    non_push = p_over_raw + p_under_raw
    if non_push <= 0:
        return 0.5, 0.5, p_push

    p_over_eff = p_over_raw / non_push
    p_under_eff = p_under_raw / non_push
    return p_over_eff, p_under_eff, p_push


def fair_decimal_odds(prob: float) -> float:
    """Convierte una probabilidad justa (0..1) en cuota decimal justa (1 / p)."""
    clamped = float(np.clip(prob, 0.01, 0.99))
    return round(1.0 / clamped, 3)


def calculate_ev_pct(fair_prob: float, market_decimal_odds: float, push_prob: float = 0.0) -> float:
    """
    Calcula el Valor Esperado porcentual (+EV%):
    Si no hay Push: EV% = (P_win * Cuota_Decimal - 1) * 100
    Si hay Push (ej. Total 6.0): EV% = (P_win_eff * (1 - P_push) * (Cuota_Decimal - 1) - P_loss_eff * (1 - P_push)) * 100
    """
    if market_decimal_odds <= 1.0:
        return -100.0
    effective_ev = ((fair_prob * market_decimal_odds) - 1.0) * (1.0 - push_prob) * 100.0
    return round(float(effective_ev), 2)


def kelly_fraction_stake(fair_prob: float, market_decimal_odds: float, fraction: float = 0.25) -> float:
    """Calcula el porcentaje sugerido de banca mediante Quarter-Kelly (tope 5%)."""
    b = market_decimal_odds - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - fair_prob
    f_star = ((b * fair_prob) - q) / b
    if f_star <= 0:
        return 0.0
    return round(float(min(0.05, f_star * fraction) * 100.0), 2)


def analyze_game(
    game: Dict[str, Any],
    stats_df: pd.DataFrame,
    hfa_goals: float = DEFAULT_HFA_GOALS,
    n_sims: int = DEFAULT_MC_ITERATIONS,
    ev_threshold: float = 2.0,
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline cuantitativo completo para un partido de NHL y devuelve todas las métricas
    de simulación, cuotas justas, +EV% en los 3 mercados (ML, Puck Line, Totales) y auditoría si finalizó.
    """
    stats_indexed = stats_df.set_index("Team_Abbr", drop=False)

    home_abbr = game["home_abbr"]
    away_abbr = game["away_abbr"]

    # Fallback en caso de que un equipo especial no esté en la tabla
    if home_abbr in stats_indexed.index:
        home_row = stats_indexed.loc[home_abbr]
    else:
        home_row = stats_df.iloc[0]

    if away_abbr in stats_indexed.index:
        away_row = stats_indexed.loc[away_abbr]
    else:
        away_row = stats_df.iloc[1]

    xg_info = compute_expected_goals(home_row, away_row, hfa_goals=hfa_goals)
    lam_h = xg_info["lambda_home_reg"]
    lam_a = xg_info["lambda_away_reg"]

    # Semilla determinista reproducible basada en el ID del partido + parámetros
    seed_val = abs(hash(f"{game.get('game_id')}_{lam_h:.3f}_{lam_a:.3f}_{n_sims}")) % (2**31 - 1)

    matrix_reg = build_bivariate_dixon_coles_matrix(lam_h, lam_a)
    mc = run_monte_carlo_nhl(matrix_reg, lam_h, lam_a, n_sims=n_sims, seed=seed_val)

    # 1. Evaluación Moneyline
    p_home_ml = mc["prob_home_ml"]
    p_away_ml = mc["prob_away_ml"]
    fair_home_ml = fair_decimal_odds(p_home_ml)
    fair_away_ml = fair_decimal_odds(p_away_ml)

    mkt_home_ml = float(game.get("home_ml_dec", fair_home_ml))
    mkt_away_ml = float(game.get("away_ml_dec", fair_away_ml))

    ev_home_ml = calculate_ev_pct(p_home_ml, mkt_home_ml)
    ev_away_ml = calculate_ev_pct(p_away_ml, mkt_away_ml)

    # 2. Evaluación Puck Line (+1.5 / -1.5)
    home_pl_line = float(game.get("home_pl_line", -1.5))
    away_pl_line = float(game.get("away_pl_line", 1.5))

    if home_pl_line < 0:
        p_home_pl = mc["prob_home_minus_1_5"]
        p_away_pl = mc["prob_away_plus_1_5"]
    else:
        p_home_pl = mc["prob_home_plus_1_5"]
        p_away_pl = mc["prob_away_minus_1_5"]

    fair_home_pl = fair_decimal_odds(p_home_pl)
    fair_away_pl = fair_decimal_odds(p_away_pl)

    mkt_home_pl = float(game.get("home_pl_dec", fair_home_pl))
    mkt_away_pl = float(game.get("away_pl_dec", fair_away_pl))

    ev_home_pl = calculate_ev_pct(p_home_pl, mkt_home_pl)
    ev_away_pl = calculate_ev_pct(p_away_pl, mkt_away_pl)

    # 3. Evaluación Totales (5.5 / 6.0 / 6.5)
    total_line = float(game.get("total_line", 6.0))
    p_over, p_under, p_push = compute_total_market_probs(mc["total_goals"], total_line)

    fair_over = fair_decimal_odds(p_over)
    fair_under = fair_decimal_odds(p_under)

    mkt_over = float(game.get("over_dec", 1.91))
    mkt_under = float(game.get("under_dec", 1.91))

    ev_over = calculate_ev_pct(p_over, mkt_over, push_prob=p_push)
    ev_under = calculate_ev_pct(p_under, mkt_under, push_prob=p_push)

    # Además calculamos las líneas alternativas 5.5, 6.0 y 6.5 para el desglose cuantitativo
    alt_totals = {}
    for alt_l in (5.5, 6.0, 6.5):
        po, pu, pp = compute_total_market_probs(mc["total_goals"], alt_l)
        alt_totals[alt_l] = {
            "p_over": round(po * 100, 1),
            "p_under": round(pu * 100, 1),
            "p_push": round(pp * 100, 1),
            "fair_over": fair_decimal_odds(po),
            "fair_under": fair_decimal_odds(pu),
        }

    # Selección de mejores oportunidades (+EV Signals)
    candidates = [
        {
            "market": "Moneyline",
            "selection": f"{away_abbr} ML",
            "prob": round(p_away_ml * 100, 1),
            "fair_odds": fair_away_ml,
            "mkt_odds": mkt_away_ml,
            "ev_pct": ev_away_ml,
            "kelly_pct": kelly_fraction_stake(p_away_ml, mkt_away_ml),
        },
        {
            "market": "Moneyline",
            "selection": f"{home_abbr} ML",
            "prob": round(p_home_ml * 100, 1),
            "fair_odds": fair_home_ml,
            "mkt_odds": mkt_home_ml,
            "ev_pct": ev_home_ml,
            "kelly_pct": kelly_fraction_stake(p_home_ml, mkt_home_ml),
        },
        {
            "market": "Puck Line",
            "selection": f"{away_abbr} {away_pl_line:+.1f}",
            "prob": round(p_away_pl * 100, 1),
            "fair_odds": fair_away_pl,
            "mkt_odds": mkt_away_pl,
            "ev_pct": ev_away_pl,
            "kelly_pct": kelly_fraction_stake(p_away_pl, mkt_away_pl),
        },
        {
            "market": "Puck Line",
            "selection": f"{home_abbr} {home_pl_line:+.1f}",
            "prob": round(p_home_pl * 100, 1),
            "fair_odds": fair_home_pl,
            "mkt_odds": mkt_home_pl,
            "ev_pct": ev_home_pl,
            "kelly_pct": kelly_fraction_stake(p_home_pl, mkt_home_pl),
        },
        {
            "market": "Total",
            "selection": f"Over {total_line}",
            "prob": round(p_over * 100, 1),
            "fair_odds": fair_over,
            "mkt_odds": mkt_over,
            "ev_pct": ev_over,
            "kelly_pct": kelly_fraction_stake(p_over, mkt_over),
        },
        {
            "market": "Total",
            "selection": f"Under {total_line}",
            "prob": round(p_under * 100, 1),
            "fair_odds": fair_under,
            "mkt_odds": mkt_under,
            "ev_pct": ev_under,
            "kelly_pct": kelly_fraction_stake(p_under, mkt_under),
        },
    ]

    best_bet = max(candidates, key=lambda c: c["ev_pct"])
    positive_ev_signals = [c for c in candidates if c["ev_pct"] >= ev_threshold]

    # Auditoría post-partido si el partido ya finalizó
    audit = evaluate_post_game_audit(game, p_home_ml, p_away_ml, mc["proj_total_goals_final"], best_bet)

    return {
        **game,
        **xg_info,
        "prob_reg_tie_pct": round(mc["prob_reg_tie"] * 100, 1),
        "prob_ot_pct": round(mc["prob_ot"] * 100, 1),
        "prob_so_pct": round(mc["prob_so"] * 100, 1),
        "proj_home_goals": round(mc["proj_home_goals_final"], 2),
        "proj_away_goals": round(mc["proj_away_goals_final"], 2),
        "proj_total_goals": round(mc["proj_total_goals_final"], 2),
        # Moneyline
        "prob_home_ml_pct": round(p_home_ml * 100, 1),
        "prob_away_ml_pct": round(p_away_ml * 100, 1),
        "fair_home_ml": fair_home_ml,
        "fair_away_ml": fair_away_ml,
        "ev_home_ml": ev_home_ml,
        "ev_away_ml": ev_away_ml,
        # Puck Line
        "prob_home_pl_pct": round(p_home_pl * 100, 1),
        "prob_away_pl_pct": round(p_away_pl * 100, 1),
        "fair_home_pl": fair_home_pl,
        "fair_away_pl": fair_away_pl,
        "ev_home_pl": ev_home_pl,
        "ev_away_pl": ev_away_pl,
        # Totales
        "prob_over_pct": round(p_over * 100, 1),
        "prob_under_pct": round(p_under * 100, 1),
        "prob_push_pct": round(p_push * 100, 1),
        "fair_over": fair_over,
        "fair_under": fair_under,
        "ev_over": ev_over,
        "ev_under": ev_under,
        "alt_totals": alt_totals,
        # Señales Sharp
        "best_bet": best_bet,
        "positive_ev_signals": positive_ev_signals,
        "audit": audit,
    }


def evaluate_post_game_audit(
    game: Dict[str, Any],
    p_home_ml: float,
    p_away_ml: float,
    proj_total: float,
    best_bet: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evalúa la precisión del modelo cuando un partido tiene resultado final ('is_completed' == True):
    - Brier Score (calibración probabilística en Moneyline)
    - Log Loss
    - Error absoluto en Goles Totales
    - Resultado de la jugada principal (+EV Pick) y PnL en unidades (1u plana)
    """
    if not game.get("is_completed") or game.get("home_score") is None or game.get("away_score") is None:
        return {"has_result": False}

    h_score = int(game["home_score"])
    a_score = int(game["away_score"])
    actual_total = h_score + a_score
    home_won = 1.0 if h_score > a_score else 0.0

    # Brier Score & Log-Loss
    brier = (p_home_ml - home_won) ** 2
    eps = 1e-6
    p_win_actual = p_home_ml if home_won == 1.0 else p_away_ml
    log_loss = -float(np.log(np.clip(p_win_actual, eps, 1.0 - eps)))

    model_fav_home = p_home_ml >= 0.5
    ml_hit = (model_fav_home and h_score > a_score) or ((not model_fav_home) and a_score > h_score)
    total_abs_error = abs(actual_total - proj_total)

    # Evaluar si el best_bet ganó
    sel = best_bet["selection"]
    mkt_odds = float(best_bet["mkt_odds"])
    home_abbr = game["home_abbr"]
    away_abbr = game["away_abbr"]

    bet_status = "PENDING"
    pnl_units = 0.0

    if sel == f"{home_abbr} ML":
        bet_status = "WIN" if h_score > a_score else "LOSS"
    elif sel == f"{away_abbr} ML":
        bet_status = "WIN" if a_score > h_score else "LOSS"
    elif sel.startswith(f"{home_abbr} "):
        line_val = float(sel.split()[1])
        bet_status = "WIN" if (h_score + line_val) > a_score else "LOSS"
    elif sel.startswith(f"{away_abbr} "):
        line_val = float(sel.split()[1])
        bet_status = "WIN" if (a_score + line_val) > h_score else "LOSS"
    elif sel.startswith("Over "):
        line_val = float(sel.split()[1])
        if actual_total > line_val:
            bet_status = "WIN"
        elif actual_total == line_val:
            bet_status = "PUSH"
        else:
            bet_status = "LOSS"
    elif sel.startswith("Under "):
        line_val = float(sel.split()[1])
        if actual_total < line_val:
            bet_status = "WIN"
        elif actual_total == line_val:
            bet_status = "PUSH"
        else:
            bet_status = "LOSS"

    if bet_status == "WIN":
        pnl_units = round(mkt_odds - 1.0, 2)
    elif bet_status == "LOSS":
        pnl_units = -1.00
    else:
        pnl_units = 0.00

    return {
        "has_result": True,
        "actual_score_str": f"{away_abbr} {a_score} - {h_score} {home_abbr}" + (" (OT/SO)" if game.get("went_to_ot") else ""),
        "actual_total": actual_total,
        "ml_hit": bool(ml_hit),
        "brier_score": round(float(brier), 4),
        "log_loss": round(float(log_loss), 4),
        "total_abs_error": round(float(total_abs_error), 2),
        "best_bet_status": bet_status,
        "best_bet_pnl_u": pnl_units,
    }


def build_predictions_export_df(analyzed_games: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Construye un DataFrame tabular limpio con todas las proyecciones, cuotas justas, cuotas de mercado y +EV%
    listo para descargarse en formato Excel (.xlsx).
    """
    rows = []
    for g in analyzed_games:
        bb = g["best_bet"]
        audit = g.get("audit", {})
        rows.append(
            {
                "Fecha": g["date_yyyymmdd"],
                "Estado": g["status_detail"],
                "Visitante": g["away_abbr"],
                "Goalie_Vis": f"{g['away_goalie']} ({g['away_sv_pct']:.3f})",
                "Local": g["home_abbr"],
                "Goalie_Loc": f"{g['home_goalie']} ({g['home_sv_pct']:.3f})",
                "xG_Reg_Vis": g["lambda_away_reg"],
                "xG_Reg_Loc": g["lambda_home_reg"],
                "Goles_Proy_Vis": g["proj_away_goals"],
                "Goles_Proy_Loc": g["proj_home_goals"],
                "Total_Proy_MC": g["proj_total_goals"],
                "Prob_OT_%": g["prob_ot_pct"],
                "Prob_Vis_ML_%": g["prob_away_ml_pct"],
                "Prob_Loc_ML_%": g["prob_home_ml_pct"],
                "Cuota_Justa_Vis_ML": g["fair_away_ml"],
                "Cuota_Justa_Loc_ML": g["fair_home_ml"],
                "Momio_Mkt_Vis_ML": g["away_ml_dec"],
                "Momio_Mkt_Loc_ML": g["home_ml_dec"],
                "EV_Vis_ML_%": g["ev_away_ml"],
                "EV_Loc_ML_%": g["ev_home_ml"],
                "Linea_PL_Loc": g["home_pl_line"],
                "Prob_Loc_PL_%": g["prob_home_pl_pct"],
                "Momio_Mkt_Loc_PL": g["home_pl_dec"],
                "EV_Loc_PL_%": g["ev_home_pl"],
                "Linea_Total": g["total_line"],
                "Prob_Over_%": g["prob_over_pct"],
                "Momio_Mkt_Over": g["over_dec"],
                "EV_Over_%": g["ev_over"],
                "Prob_Under_%": g["prob_under_pct"],
                "Momio_Mkt_Under": g["under_dec"],
                "EV_Under_%": g["ev_under"],
                "Mejor_Pick_Sharp": bb["selection"],
                "Mercado_Pick": bb["market"],
                "Cuota_Pick_Dec": bb["mkt_odds"],
                "EV_Pick_%": bb["ev_pct"],
                "Stake_Kelly_%": bb["kelly_pct"],
                "Marcador_Final": audit.get("actual_score_str", "Pendiente"),
                "Resultado_Pick": audit.get("best_bet_status", "N/A"),
                "PnL_Unidades": audit.get("best_bet_pnl_u", 0.0),
                "Brier_Score": audit.get("brier_score", np.nan),
            }
        )
    return pd.DataFrame(rows)
