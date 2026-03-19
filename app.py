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
    discount = cfg["discount_percent"] / 100

    usd_per_gram = get_gold_price()
    usd_ron = get_usd_ron()

    base = usd_per_gram * usd_ron
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
            cfg["discount_percent"] = float(request.form["discount"])
            save_config(cfg)
        return redirect("/admin")

    return render_template("admin.html", discount=cfg["discount_percent"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
