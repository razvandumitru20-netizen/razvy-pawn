from flask import Flask, render_template, request, redirect, jsonify
import requests, json, os
import xml.etree.ElementTree as ET
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
    # 1. preț aur USD
    gold_url = "https://api.gold-api.com/price/XAU"
    gold_data = requests.get(gold_url).json()
    price_usd_per_ounce = gold_data["price"]

    # 2. curs USD → EUR real
    fx_url = "https://api.exchangerate.host/latest?base=USD&symbols=EUR"
    fx_data = requests.get(fx_url).json()
    usd_to_eur = fx_data["rates"]["EUR"]

    # 3. transformare în EUR / gram
    price_eur_per_gram = (price_usd_per_ounce * usd_to_eur) / 31.1035

    return price_eur_per_gram

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
