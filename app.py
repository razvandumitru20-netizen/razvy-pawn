from flask import Flask, render_template, request, redirect, jsonify
import requests, json, os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("display.html")
def load_config():
    with open("config.json") as f:
        return json.load(f)

def save_config(cfg):
    with open("config.json", "w") as f:
        json.dump(cfg, f)

def get_gold_price():
    url = "https://www.kitco.com/charts/gold"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    if "EUR/g" not in text:
        raise Exception("Nu am găsit EUR/g pe pagina Kitco")

    import re
    match = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*EUR/g", text)

    if not match:
        raise Exception("Nu am găsit prețul aurului în EUR/g pe Kitco")

    eur_per_gram = float(match.group(1).replace(",", "."))
    return eur_per_gram
def get_eur_ron():
    url = "https://www.bnr.ro/nbrfxrates.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    for rate in root.iter():
        if rate.tag.endswith("Rate") and rate.attrib.get("currency") == "EUR":
            return float(rate.text)

    raise Exception("Nu am găsit cursul EUR în XML-ul BNR")

@app.route("/display")
def display():
    return render_template("display.html")

@app.route("/prices")
def prices():
    cfg = load_config()
    discount = cfg["discount_percent"] / 100

    eur = get_gold_price()
    ron = get_eur_ron()

    base = eur * ron
    final = base * (1 - discount)

    return jsonify({
        "24K": round(final, 2),
        "18K": round(final * 0.75, 2),
        "14K": round(final * 0.585, 2),
        "8K": round(final * 0.333, 2)
    })

@app.route("/admin", methods=["GET", "POST"])
def admin():
    cfg = load_config()

    if request.method == "POST":
        if request.form["password"] == cfg["password"]:
            cfg["discount"] = float(request.form["discount"])
            save_config(cfg)
        return redirect("/admin")

    return render_template("admin.html", discount=cfg["discount"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
