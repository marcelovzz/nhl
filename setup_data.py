"""
setup_data.py
Generador automático del dataset base 'nhl_stats.xlsx' con las 32 franquicias de la NHL.
Incluye métricas ofensivas/defensivas (GF/G, GA/G, xGF/G, xGA/G), Pace y Goalies titulares.
Soporta escritura y lectura con 'openpyxl' y cuenta con respaldo nativo OpenXML (.xlsx)
para garantizar funcionamiento incluso antes de instalar dependencias externas.
"""

import io
import os
import xml.etree.ElementTree as ET
import zipfile
from xml.sax.saxutils import escape
import pandas as pd

NHL_DEFAULT_FILENAME = "nhl_stats.xlsx"

# Datos base calibrados de las 32 franquicias de la NHL
NHL_TEAMS_DATA = [
    ("ANA", "Anaheim Ducks", 2.62, 3.45, 2.70, 3.38, 59.5, 0.896, "Lukas Dostal"),
    ("BOS", "Boston Bruins", 3.18, 3.74 - 1.00, 3.05, 2.88, 60.2, 0.912, "Jeremy Swayman"),
    ("BUF", "Buffalo Sabres", 3.02, 3.08, 3.01, 3.04, 62.1, 0.905, "Ukko-Pekka Luukkonen"),
    ("CGY", "Calgary Flames", 2.94, 3.15, 2.98, 3.10, 61.0, 0.901, "Dustin Wolf"),
    ("CAR", "Carolina Hurricanes", 3.42, 2.60, 3.62, 2.48, 64.5, 0.911, "Pyotr Kochetkov"),
    ("CHI", "Chicago Blackhawks", 2.45, 3.52, 2.52, 3.44, 58.4, 0.895, "Petr Mrazek"),
    ("COL", "Colorado Avalanche", 3.65, 2.98, 3.54, 2.92, 64.8, 0.906, "Alexandar Georgiev"),
    ("CBJ", "Columbus Blue Jackets", 2.88, 3.55, 2.86, 3.42, 61.8, 0.894, "Elvis Merzlikins"),
    ("DAL", "Dallas Stars", 3.56, 2.68, 3.48, 2.65, 62.0, 0.914, "Jake Oettinger"),
    ("DET", "Detroit Red Wings", 3.12, 3.22, 2.95, 3.20, 60.5, 0.902, "Cam Talbot"),
    ("EDM", "Edmonton Oilers", 3.62, 2.84, 3.70, 2.75, 64.2, 0.908, "Stuart Skinner"),
    ("FLA", "Florida Panthers", 3.40, 2.58, 3.55, 2.54, 63.6, 0.915, "Sergei Bobrovsky"),
    ("LAK", "Los Angeles Kings", 3.08, 2.66, 3.16, 2.62, 59.8, 0.910, "Darcy Kuemper"),
    ("MIN", "Minnesota Wild", 3.15, 2.88, 3.12, 2.85, 60.4, 0.912, "Filip Gustavsson"),
    ("MTL", "Montreal Canadiens", 2.78, 3.38, 2.76, 3.35, 60.9, 0.898, "Sam Montembeault"),
    ("NSH", "Nashville Predators", 3.14, 3.06, 3.24, 2.98, 62.3, 0.913, "Juuse Saros"),
    ("NJD", "New Jersey Devils", 3.38, 2.96, 3.45, 2.88, 63.4, 0.909, "Jacob Markstrom"),
    ("NYI", "New York Islanders", 2.92, 2.95, 2.96, 3.02, 59.6, 0.914, "Ilya Sorokin"),
    ("NYR", "New York Rangers", 3.36, 2.72, 3.28, 2.82, 61.2, 0.918, "Igor Shesterkin"),
    ("OTT", "Ottawa Senators", 3.16, 3.18, 3.20, 3.08, 62.5, 0.904, "Linus Ullmark"),
    ("PHI", "Philadelphia Flyers", 2.86, 3.14, 2.94, 3.06, 60.7, 0.897, "Samuel Ersson"),
    ("PIT", "Pittsburgh Penguins", 3.05, 3.20, 3.18, 3.15, 62.6, 0.900, "Tristan Jarry"),
    ("SJS", "San Jose Sharks", 2.42, 3.68, 2.48, 3.60, 58.2, 0.892, "Mackenzie Blackwood"),
    ("SEA", "Seattle Kraken", 2.90, 2.92, 2.94, 2.88, 59.9, 0.907, "Joey Daccord"),
    ("STL", "St. Louis Blues", 2.95, 3.08, 2.86, 3.14, 60.1, 0.908, "Jordan Binnington"),
    ("TBL", "Tampa Bay Lightning", 3.46, 2.94, 3.36, 2.90, 62.4, 0.913, "Andrei Vasilevskiy"),
    ("TOR", "Toronto Maple Leafs", 3.48, 2.86, 3.44, 2.84, 62.9, 0.911, "Anthony Stolarz"),
    ("UTA", "Utah Hockey Club", 3.06, 3.12, 3.02, 3.08, 61.4, 0.905, "Connor Ingram"),
    ("VAN", "Vancouver Canucks", 3.34, 2.78, 3.22, 2.80, 61.1, 0.914, "Thatcher Demko"),
    ("VGK", "Vegas Golden Knights", 3.38, 2.82, 3.32, 2.84, 62.2, 0.910, "Adin Hill"),
    ("WSH", "Washington Capitals", 3.10, 2.96, 3.04, 2.98, 60.0, 0.908, "Logan Thompson"),
    ("WPG", "Winnipeg Jets", 3.36, 2.48, 3.28, 2.60, 60.8, 0.921, "Connor Hellebuyck"),
]

COLUMNS = [
    "Team_Abbr",
    "Team_Name",
    "Goals_For_Game",
    "Goals_Against_Game",
    "xGF_Game",
    "xGA_Game",
    "Pace_Events",
    "Save_Pct",
    "Starting_Goalie",
]


def _col_letter(idx: int) -> str:
    """Convierte índice base-0 de columna a letra Excel (A, B, ..., Z, AA...)."""
    result = ""
    n = idx + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def _dataframe_to_sheet_xml(df: pd.DataFrame) -> str:
    """Genera el XML de una hoja OpenXML (.xlsx) a partir de un DataFrame."""
    rows_xml = []
    # Encabezados (fila 1)
    header_cells = []
    for c_idx, col_name in enumerate(df.columns):
        ref = f"{_col_letter(c_idx)}1"
        header_cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(col_name))}</t></is></c>')
    rows_xml.append(f'<row r="1">{"".join(header_cells)}</row>')

    # Filas de datos
    for r_idx, row in enumerate(df.itertuples(index=False), start=2):
        cells = []
        for c_idx, val in enumerate(row):
            ref = f"{_col_letter(c_idx)}{r_idx}"
            if isinstance(val, (int, float)) and not pd.isna(val):
                cells.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                text_val = "" if pd.isna(val) else str(val)
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(text_val)}</t></is></c>')
        rows_xml.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(rows_xml)}</sheetData>'
        "</worksheet>"
    )


def write_xlsx_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """
    Escribe uno o varios DataFrames a un archivo Excel (.xlsx) en memoria.
    Usa 'openpyxl' si está disponible o el generador OpenXML nativo como respaldo.
    """
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        buffer.seek(0)
        return buffer.getvalue()
    except ImportError:
        buffer = io.BytesIO()
        sheet_names = list(sheets.keys())
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            overrides = "".join(
                f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for i in range(len(sheet_names))
            )
            content_types = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                f"{overrides}</Types>"
            )
            zf.writestr("[Content_Types].xml", content_types)

            root_rels = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="xl/workbook.xml"/>'
                "</Relationships>"
            )
            zf.writestr("_rels/.rels", root_rels)

            sheets_tag = "".join(
                f'<sheet name="{escape(name[:31])}" sheetId="{i+1}" r:id="rId{i+1}"/>'
                for i, name in enumerate(sheet_names)
            )
            workbook_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f"<sheets>{sheets_tag}</sheets></workbook>"
            )
            zf.writestr("xl/workbook.xml", workbook_xml)

            wb_rels_tag = "".join(
                f'<Relationship Id="rId{i+1}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{i+1}.xml"/>'
                for i in range(len(sheet_names))
            )
            wb_rels = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f"{wb_rels_tag}</Relationships>"
            )
            zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)

            for i, name in enumerate(sheet_names):
                zf.writestr(f"xl/worksheets/sheet{i+1}.xml", _dataframe_to_sheet_xml(sheets[name]))

        buffer.seek(0)
        return buffer.getvalue()


def read_excel_safe(source: str | io.BytesIO) -> pd.DataFrame:
    """Lee un archivo .xlsx usando pandas/openpyxl o el lector OpenXML integrado."""
    try:
        return pd.read_excel(source, engine="openpyxl")
    except ImportError:
        with zipfile.ZipFile(source, "r") as zf:
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in zf.namelist():
                ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for si in ss_root.findall("m:si", ns):
                    texts = [t.text or "" for t in si.findall(".//m:t", ns)]
                    shared_strings.append("".join(texts))

            sheet_root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            parsed_rows: list[list[str | float]] = []
            for row_el in sheet_root.findall(".//m:sheetData/m:row", ns):
                row_vals: list[str | float] = []
                for c_el in row_el.findall("m:c", ns):
                    c_type = c_el.attrib.get("t", "")
                    if c_type == "inlineStr":
                        t_el = c_el.find(".//m:t", ns)
                        row_vals.append(t_el.text if t_el is not None and t_el.text is not None else "")
                    elif c_type == "s":
                        v_el = c_el.find("m:v", ns)
                        idx = int(v_el.text) if v_el is not None and v_el.text else 0
                        row_vals.append(shared_strings[idx] if idx < len(shared_strings) else "")
                    else:
                        v_el = c_el.find("m:v", ns)
                        if v_el is not None and v_el.text is not None:
                            try:
                                row_vals.append(float(v_el.text))
                            except ValueError:
                                row_vals.append(v_el.text)
                        else:
                            row_vals.append("")
                parsed_rows.append(row_vals)

            if not parsed_rows:
                return build_default_dataframe()
            headers = [str(h) for h in parsed_rows[0]]
            return pd.DataFrame(parsed_rows[1:], columns=headers)


def build_default_dataframe() -> pd.DataFrame:
    """Retorna el DataFrame base con las 32 franquicias NHL."""
    return pd.DataFrame(NHL_TEAMS_DATA, columns=COLUMNS)


def ensure_nhl_stats_excel(filepath: str = NHL_DEFAULT_FILENAME, overwrite: bool = False) -> str:
    """
    Genera el archivo 'nhl_stats.xlsx' si no existe (o si overwrite=True).
    Retorna la ruta del archivo generado.
    """
    if os.path.exists(filepath) and not overwrite:
        return filepath

    df = build_default_dataframe()
    xlsx_bytes = write_xlsx_bytes({"NHL_Stats": df})
    with open(filepath, "wb") as f:
        f.write(xlsx_bytes)
    return filepath


if __name__ == "__main__":
    output_path = ensure_nhl_stats_excel(overwrite=True)
    print(f"[OK] Archivo base generado exitosamente en: {os.path.abspath(output_path)} (32 franquicias NHL)")
