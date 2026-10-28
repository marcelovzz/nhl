"""
sync_espn_nhl.py
Módulo de ingesta en tiempo real desde la API pública de ESPN para NHL.
Extrae cartelera por fecha ('dates=YYYYMMDD'), momios en formato DECIMAL
(Moneyline, Puck Line +/-1.5, Totales 5.5/6.0/6.5) y marcadores finales para auditoría.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import requests

ESPN_NHL_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"

# Normalización de abreviaturas ESPN -> estándar 3 letras de nhl_stats.xlsx
ABBR_NORMALIZATION: Dict[str, str] = {
    "TB": "TBL",
    "LA": "LAK",
    "NJ": "NJD",
    "SJ": "SJS",
    "UTAH": "UTA",
    "VEG": "VGK",
    "MON": "MTL",
    "WAS": "WSH",
    "CLB": "CBJ",
    "CAL": "CGY",
    "NAS": "NSH",
    "WIN": "WPG",
}


def normalize_team_abbr(abbr: str) -> str:
    """Normaliza la abreviatura de ESPN al estándar de 3 letras del modelo."""
    if not abbr:
        return "UNK"
    clean = str(abbr).strip().upper()
    return ABBR_NORMALIZATION.get(clean, clean)


def american_to_decimal(american_odds: Any, default: float = 1.91) -> float:
    """
    Convierte momios americanos (ej. -150, +130, 'EVEN', -110) a cuota DECIMAL (ej. 1.67, 2.30).
    Si ya recibe un valor decimal válido entre 1.01 y 25.0, lo respeta.
    """
    if american_odds is None:
        return round(default, 3)

    if isinstance(american_odds, str):
        raw = american_odds.strip().upper()
        if raw in ("EVEN", "EV", "PK", "PICK"):
            return 2.000
        raw = raw.replace("+", "")
        try:
            val = float(raw)
        except ValueError:
            return round(default, 3)
    elif isinstance(american_odds, (int, float)):
        val = float(american_odds)
    else:
        return round(default, 3)

    if val == 0:
        return round(default, 3)

    # Si ya viene en formato decimal (ej. 1.85 o 2.15)
    if 1.01 <= val < 15.0:
        return round(val, 3)

    if val >= 100:
        return round(1.0 + (val / 100.0), 3)
    if val <= -100:
        return round(1.0 + (100.0 / abs(val)), 3)

    return round(default, 3)


def _extract_nested_american(node: Optional[Dict[str, Any]], *keys: str) -> Optional[Any]:
    """Busca recursivamente un valor en un diccionario anidado."""
    cur = node
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _parse_details_ml(details: str, home_abbr: str, away_abbr: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parsea strings tipo 'CAR -165' o 'EDM -140' desde el campo 'details' de ESPN
    y estima el momio de ambos lados aplicando un vig estándar (~4.2%).
    """
    if not details:
        return None, None
    parts = details.strip().split()
    if len(parts) < 2:
        return None, None

    fav_abbr = normalize_team_abbr(parts[0])
    try:
        fav_am = float(parts[1])
    except ValueError:
        return None, None

    if abs(fav_am) < 100:
        return None, None

    fav_dec = american_to_decimal(fav_am)
    fav_imp = 1.0 / fav_dec
    dog_imp = max(0.12, min(0.88, 1.042 - fav_imp))
    dog_dec = round(1.0 / dog_imp, 3)

    if fav_abbr == home_abbr:
        return fav_dec, dog_dec
    if fav_abbr == away_abbr:
        return dog_dec, fav_dec
    return None, None


def _parse_odds_block(
    odds_list: List[Dict[str, Any]],
    home_abbr: str,
    away_abbr: str,
) -> Dict[str, Any]:
    """
    Extrae momios en formato DECIMAL para:
    - Moneyline (Local / Visitante)
    - Puck Line (-1.5 / +1.5)
    - Totales (Over / Under en líneas 5.5, 6.0 o 6.5)
    """
    result = {
        "provider": "Consensus / Market Est.",
        "has_live_odds": False,
        "home_ml_dec": 1.87,
        "away_ml_dec": 2.02,
        "home_pl_line": -1.5,
        "away_pl_line": 1.5,
        "home_pl_dec": 2.55,
        "away_pl_dec": 1.54,
        "total_line": 6.0,
        "over_dec": 1.91,
        "under_dec": 1.91,
    }

    if not odds_list:
        return result

    primary = None
    for item in odds_list:
        if isinstance(item, dict):
            primary = item
            break

    if not primary:
        return result

    result["has_live_odds"] = True
    provider_info = primary.get("provider") or {}
    if isinstance(provider_info, dict) and provider_info.get("name"):
        result["provider"] = str(provider_info["name"])

    # 1. MONEYLINE
    home_odds_node = primary.get("homeTeamOdds") or {}
    away_odds_node = primary.get("awayTeamOdds") or {}
    ml_node = primary.get("moneyline") or {}

    home_ml_am = (
        home_odds_node.get("moneyLine")
        or _extract_nested_american(ml_node, "home", "close", "odds")
        or _extract_nested_american(ml_node, "home", "current", "odds")
    )
    away_ml_am = (
        away_odds_node.get("moneyLine")
        or _extract_nested_american(ml_node, "away", "close", "odds")
        or _extract_nested_american(ml_node, "away", "current", "odds")
    )

    if home_ml_am is not None and away_ml_am is not None:
        result["home_ml_dec"] = american_to_decimal(home_ml_am, 1.87)
        result["away_ml_dec"] = american_to_decimal(away_ml_am, 2.02)
    else:
        details_str = str(primary.get("details") or "")
        h_dec, a_dec = _parse_details_ml(details_str, home_abbr, away_abbr)
        if h_dec and a_dec:
            result["home_ml_dec"] = h_dec
            result["away_ml_dec"] = a_dec

    # Determinar quién es favorito para orientar el Puck Line (-1.5 al favorito, +1.5 al underdog)
    home_is_fav = result["home_ml_dec"] <= result["away_ml_dec"]

    # 2. PUCK LINE (+1.5 / -1.5)
    spread_val = primary.get("spread")
    ps_node = primary.get("pointSpread") or {}

    home_pl_line = None
    if spread_val is not None:
        try:
            s_float = float(spread_val)
            if abs(s_float) in (1.5, 2.5):
                home_pl_line = -1.5 if home_is_fav else 1.5
        except (ValueError, TypeError):
            pass

    raw_home_line = _extract_nested_american(ps_node, "home", "close", "line") or home_odds_node.get("spread")
    if raw_home_line is not None:
        try:
            parsed_line = float(str(raw_home_line).replace("+", ""))
            if abs(parsed_line) == 1.5:
                home_pl_line = parsed_line
        except ValueError:
            pass

    if home_pl_line is None:
        home_pl_line = -1.5 if home_is_fav else 1.5

    result["home_pl_line"] = home_pl_line
    result["away_pl_line"] = -home_pl_line

    home_pl_am = (
        home_odds_node.get("spreadOdds")
        or _extract_nested_american(ps_node, "home", "close", "odds")
        or _extract_nested_american(ps_node, "home", "current", "odds")
    )
    away_pl_am = (
        away_odds_node.get("spreadOdds")
        or _extract_nested_american(ps_node, "away", "close", "odds")
        or _extract_nested_american(ps_node, "away", "current", "odds")
    )

    default_home_pl_dec = 2.55 if home_pl_line < 0 else 1.54
    default_away_pl_dec = 1.54 if home_pl_line < 0 else 2.55

    result["home_pl_dec"] = american_to_decimal(home_pl_am, default_home_pl_dec)
    result["away_pl_dec"] = american_to_decimal(away_pl_am, default_away_pl_dec)

    # 3. TOTALES (Over/Under 5.5 / 6.0 / 6.5)
    ou_raw = primary.get("overUnder")
    total_node = primary.get("total") or {}
    if ou_raw is None:
        ou_raw = _extract_nested_american(total_node, "over", "close", "line")

    parsed_total = 6.0
    if ou_raw is not None:
        try:
            clean_ou = str(ou_raw).upper().replace("O", "").replace("U", "").strip()
            val_ou = float(clean_ou)
            # Ajustar al escalón NHL estándar más cercano (5.5, 6.0, 6.5)
            parsed_total = min([5.5, 6.0, 6.5], key=lambda x: abs(x - val_ou))
        except ValueError:
            parsed_total = 6.0

    result["total_line"] = parsed_total

    over_am = (
        primary.get("overOdds")
        or _extract_nested_american(total_node, "over", "close", "odds")
        or _extract_nested_american(total_node, "over", "current", "odds")
    )
    under_am = (
        primary.get("underOdds")
        or _extract_nested_american(total_node, "under", "close", "odds")
        or _extract_nested_american(total_node, "under", "current", "odds")
    )

    result["over_dec"] = american_to_decimal(over_am, 1.91)
    result["under_dec"] = american_to_decimal(under_am, 1.91)

    return result


def format_date_yyyymmdd(target_date: Any) -> str:
    """Convierte date, datetime o string 'YYYY-MM-DD' al formato 'YYYYMMDD' requerido por ESPN."""
    if isinstance(target_date, (date, datetime)):
        return target_date.strftime("%Y%m%d")
    raw = str(target_date).strip().replace("-", "").replace("/", "")
    if len(raw) == 8 and raw.isdigit():
        return raw
    return datetime.now().strftime("%Y%m%d")


def fetch_nhl_scoreboard(target_date: Any, timeout: int = 10) -> Dict[str, Any]:
    """
    Consulta el endpoint oficial de ESPN para NHL en la fecha indicada ('dates=YYYYMMDD').
    Retorna un diccionario con:
      - 'date_str': YYYYMMDD
      - 'games': lista de diccionarios de partidos normalizados
      - 'error': mensaje de error si falló la red (o None)
    """
    date_param = format_date_yyyymmdd(target_date)
    params = {"dates": date_param}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TerminalSharpNHLQuant/2.0",
        "Accept": "application/json",
    }

    try:
        response = requests.get(ESPN_NHL_SCOREBOARD_URL, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return {
            "date_str": date_param,
            "games": [],
            "error": f"Error de conexión con ESPN API: {exc}",
        }

    events = payload.get("events") or []
    games: List[Dict[str, Any]] = []

    for event in events:
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        comp = competitions[0]
        competitors = comp.get("competitors") or []

        home_comp = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away_comp = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home_comp or not away_comp:
            continue

        home_team = home_comp.get("team") or {}
        away_team = away_comp.get("team") or {}

        home_abbr = normalize_team_abbr(home_team.get("abbreviation", ""))
        away_abbr = normalize_team_abbr(away_team.get("abbreviation", ""))

        home_name = home_team.get("displayName") or home_team.get("name") or home_abbr
        away_name = away_team.get("displayName") or away_team.get("name") or away_abbr

        # Estado del partido y auditoría post-partido
        status_obj = comp.get("status") or event.get("status") or {}
        status_type = status_obj.get("type") or {}
        state = str(status_type.get("state") or "pre").lower()  # 'pre', 'in', 'post'
        is_completed = bool(status_type.get("completed", False)) or state == "post"
        status_detail = str(status_type.get("shortDetail") or status_type.get("detail") or "Programado")
        period = int(status_obj.get("period") or 0)
        went_to_ot = period > 3 or ("OT" in status_detail.upper()) or ("SO" in status_detail.upper())

        home_score: Optional[int] = None
        away_score: Optional[int] = None
        if state in ("in", "post") or is_completed:
            try:
                home_score = int(float(home_comp.get("score", 0)))
                away_score = int(float(away_comp.get("score", 0)))
            except (ValueError, TypeError):
                home_score, away_score = None, None

        # Momios en formato decimal
        odds_list = comp.get("odds") or []
        parsed_odds = _parse_odds_block(odds_list, home_abbr, away_abbr)

        venue_name = (comp.get("venue") or {}).get("fullName", "NHL Arena")
        start_date_iso = comp.get("date") or event.get("date") or ""

        games.append(
            {
                "game_id": str(event.get("id", f"{away_abbr}_{home_abbr}_{date_param}")),
                "date_yyyymmdd": date_param,
                "start_time_iso": start_date_iso,
                "venue": venue_name,
                "status_state": state,
                "status_detail": status_detail,
                "is_completed": is_completed,
                "went_to_ot": went_to_ot,
                "period": period,
                "home_abbr": home_abbr,
                "home_name": home_name,
                "away_abbr": away_abbr,
                "away_name": away_name,
                "home_score": home_score,
                "away_score": away_score,
                **parsed_odds,
            }
        )

    return {
        "date_str": date_param,
        "games": games,
        "error": None,
    }


def get_demo_slate(target_date: Any) -> List[Dict[str, Any]]:
    """
    Genera una cartelera de respaldo realista (con partidos en vivo/pre-partido y finalizados)
    cuando la fecha consultada es fuera de calendario o sin conexión, permitiendo probar toda la terminal.
    """
    date_param = format_date_yyyymmdd(target_date)
    return [
        {
            "game_id": f"DEMO_1_{date_param}",
            "date_yyyymmdd": date_param,
            "start_time_iso": f"{date_param[:4]}-{date_param[4:6]}-{date_param[6:8]}T23:00Z",
            "venue": "Madison Square Garden",
            "status_state": "pre",
            "status_detail": "7:00 PM ET",
            "is_completed": False,
            "went_to_ot": False,
            "period": 0,
            "home_abbr": "NYR",
            "home_name": "New York Rangers",
            "away_abbr": "BOS",
            "away_name": "Boston Bruins",
            "home_score": None,
            "away_score": None,
            "provider": "DraftKings (Demo Slate)",
            "has_live_odds": True,
            "home_ml_dec": 1.80,
            "away_ml_dec": 2.10,
            "home_pl_line": -1.5,
            "away_pl_line": 1.5,
            "home_pl_dec": 2.65,
            "away_pl_dec": 1.52,
            "total_line": 5.5,
            "over_dec": 1.95,
            "under_dec": 1.87,
        },
        {
            "game_id": f"DEMO_2_{date_param}",
            "date_yyyymmdd": date_param,
            "start_time_iso": f"{date_param[:4]}-{date_param[4:6]}-{date_param[6:8]}T23:30Z",
            "venue": "Amerant Bank Arena",
            "status_state": "pre",
            "status_detail": "7:30 PM ET",
            "is_completed": False,
            "went_to_ot": False,
            "period": 0,
            "home_abbr": "FLA",
            "home_name": "Florida Panthers",
            "away_abbr": "TBL",
            "away_name": "Tampa Bay Lightning",
            "home_score": None,
            "away_score": None,
            "provider": "ESPN BET (Demo Slate)",
            "has_live_odds": True,
            "home_ml_dec": 1.76,
            "away_ml_dec": 2.15,
            "home_pl_line": -1.5,
            "away_pl_line": 1.5,
            "home_pl_dec": 2.50,
            "away_pl_dec": 1.57,
            "total_line": 6.0,
            "over_dec": 1.91,
            "under_dec": 1.91,
        },
        {
            "game_id": f"DEMO_3_{date_param}",
            "date_yyyymmdd": date_param,
            "start_time_iso": f"{date_param[:4]}-{date_param[4:6]}-{date_param[6:8]}T01:00Z",
            "venue": "Rogers Place",
            "status_state": "post",
            "status_detail": "Final",
            "is_completed": True,
            "went_to_ot": False,
            "period": 3,
            "home_abbr": "EDM",
            "home_name": "Edmonton Oilers",
            "away_abbr": "COL",
            "away_name": "Colorado Avalanche",
            "home_score": 4,
            "away_score": 2,
            "provider": "FanDuel (Demo Slate)",
            "has_live_odds": True,
            "home_ml_dec": 1.83,
            "away_ml_dec": 2.05,
            "home_pl_line": -1.5,
            "away_pl_line": 1.5,
            "home_pl_dec": 2.58,
            "away_pl_dec": 1.54,
            "total_line": 6.5,
            "over_dec": 1.87,
            "under_dec": 1.95,
        },
        {
            "game_id": f"DEMO_4_{date_param}",
            "date_yyyymmdd": date_param,
            "start_time_iso": f"{date_param[:4]}-{date_param[4:6]}-{date_param[6:8]}T02:00Z",
            "venue": "American Airlines Center",
            "status_state": "post",
            "status_detail": "Final/OT",
            "is_completed": True,
            "went_to_ot": True,
            "period": 4,
            "home_abbr": "DAL",
            "home_name": "Dallas Stars",
            "away_abbr": "WPG",
            "away_name": "Winnipeg Jets",
            "home_score": 3,
            "away_score": 2,
            "provider": "DraftKings (Demo Slate)",
            "has_live_odds": True,
            "home_ml_dec": 1.85,
            "away_ml_dec": 2.00,
            "home_pl_line": -1.5,
            "away_pl_line": 1.5,
            "home_pl_dec": 2.70,
            "away_pl_dec": 1.50,
            "total_line": 5.5,
            "over_dec": 1.98,
            "under_dec": 1.85,
        },
    ]
