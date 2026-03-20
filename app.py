from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)


def load_config():
    with open("config.json") as f:
        return json.load(f)


def save_config(cfg):
    with open("config.json", "w") as f:
        json.dump(cfg, f)


def get_gold_price():
    url = "https://api.gold-api.com/price/XAU"
    response = requests.get(url, timeout=15)
    data = response.json()

    price_per_ounce_usd = data["price"]
    price_per_gram_usd = price_per_ounce_usd / 31.1035
    return price_per_gram_usd


def get_usd_ron():
    url = "https://www.bnr.ro/nbrfxrates.xml"
    response = requests.get(url, timeout=15)
    root = ET.fromstring(response.content)

    for rate in root.iter():
        if rate.tag.endswith("Rate") and rate.attrib.get("currency") == "USD":
            return float(rate.text)

    raise Exception("Nu am găsit USD/RON în XML-ul BNR")


@app.route("/")
def home():
    return render_template("display.html")


@app.route("/display")
def display():
    return render_template("display.html")


@app.route("/prices")
def prices():
    cfg = load_config()

    usd_per_gram = get_gold_price()
    usd_ron = get_usd_ron()

    base = usd_per_gram * usd_ron

    d24 = cfg["discount_24k"] / 100
    d18 = cfg["discount_18k"] / 100
    d14 = cfg["discount_14k"] / 100
    d8 = cfg["discount_8k"] / 100

    return jsonify({
        "24K": round(base * (1 - d24), 2),
        "18K": round(base * 0.75 * (1 - d18), 2),
        "14K": round(base * 0.585 * (1 - d14), 2),
        "8K": round(base * 0.333 * (1 - d8), 2)
    })

@app.route("/admin", methods=["GET", "POST"])
def admin():
    cfg = load_config()

    if request.method == "POST":
        if request.form["password"] == cfg["password"]:
            cfg["discount_24k"] = float(request.form["d24"])
            cfg["discount_18k"] = float(request.form["d18"])
            cfg["discount_14k"] = float(request.form["d14"])
            cfg["discount_8k"] = float(request.form["d8"])
            save_config(cfg)
            return redirect("/admin")

    return render_template("admin.html", cfg=cfg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
