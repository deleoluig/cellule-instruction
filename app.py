from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import datetime
import os
import json
import traceback

app = Flask(__name__)

SPREADSHEET_ID = "1WJbQ8gHN-UwY09G2yFkmnn_Bdx65nAxJoCFlrwlWxRo"
SHEET_NAME = "Encodage"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

AGENTS = [
    "BOURCE", "DE LEO", "DELHEZ", "DESARCY", "ERNST C", "ERNST JG",
    "LALOYAUX S.", "LEMAIRE", "MAGER", "MALEMPRE", "M'RABET",
    "PLUMHANS", "PORTZENHEIN J", "QUALIZZA", "RENARD", "SWINEN JF",
    "TAHIR", "THEUNENS", "TSAGKAS", "VERMEEREN",
]

THEMES = [
    "Organisation exercice",
    "Stagiaire",
    "Plannification",
    "Création exercice",
    "Réunion cellule AMU",
    "Réunion cellule pompiers",
    "Test opérationnel",
    "Divers",
]

DUREES = {
    "5 min":  round(5/60, 3),
    "10 min": round(10/60, 3),
    "15 min": round(15/60, 3),
    "20 min": round(20/60, 3),
    "30 min": round(30/60, 3),
    "45 min": round(45/60, 3),
    "1h":     1.0,
    "1h30":   1.5,
    "2h":     2.0,
    "3h":     3.0,
    "4h":     4.0,
    "8h":     8.0,
}

def get_sheet():
    raw = os.environ.get("GOOGLE_CREDENTIALS", "")
    try:
        creds_dict = json.loads(raw)
        if isinstance(creds_dict, str):
            creds_dict = json.loads(creds_dict)
    except Exception:
        with open("credentials.json", "r", encoding="utf-8") as f:
            creds_dict = json.load(f)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

@app.route("/test")
def test():
    """Route de diagnostic — à supprimer après résolution"""
    result = {}
    try:
        raw = os.environ.get("GOOGLE_CREDENTIALS", "")
        result["creds_present"] = bool(raw)
        result["creds_length"] = len(raw)
        result["creds_start"] = raw[:30] if raw else "VIDE"
        creds_dict = json.loads(raw)
        if isinstance(creds_dict, str):
            creds_dict = json.loads(creds_dict)
        result["creds_type"] = creds_dict.get("type", "?")
        result["client_email"] = creds_dict.get("client_email", "?")
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        result["gspread_ok"] = True
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        result["sheet_ok"] = True
        result["sheet_title"] = sheet.title
    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
    return jsonify(result)

@app.route("/")
def index():
    today = datetime.date.today().strftime("%Y-%m-%d")
    return render_template("index.html",
                           agents=AGENTS,
                           themes=THEMES,
                           durees=list(DUREES.keys()),
                           today=today)

@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.json
        date_str  = data.get("date", "")
        agent     = data.get("agent", "").strip()
        theme     = data.get("theme", "").strip()
        tache     = data.get("tache", "").strip()
        garde     = data.get("garde", "En garde")
        duree_lbl = data.get("duree", "30 min")

        errors = []
        if not date_str:
            errors.append("Date manquante")
        if not agent:
            errors.append("Agent manquant")
        if not theme:
            errors.append("Thème manquant")
        if not tache:
            errors.append("Description de la tâche manquante")
        if errors:
            return jsonify({"ok": False, "error": ", ".join(errors)}), 400

        dt      = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        date_fr = dt.strftime("%d/%m/%Y")
        mois    = dt.month
        annee   = dt.year
        duree_h = DUREES.get(duree_lbl, 0.5)

        sheet = get_sheet()
        sheet.append_row(
            [date_fr, mois, annee, agent, theme, tache, garde, duree_h],
            value_input_option="USER_ENTERED"
        )
        return jsonify({"ok": True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
