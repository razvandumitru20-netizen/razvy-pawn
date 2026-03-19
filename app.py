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
    url = "https://api.gold-api.com/price/XAU"
    response = requests.get(url)
    data = response.json()

    price_per_ounce = data["price"]  # USD per ounce
    price_per_gram = price_per_ounce / 31.1035

    return price_per_gram
def get_usd_ron():
    url = "https://www.bnr.ro/nbrfxrates.xml"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    for rate in root.findall(".//Rate"):
        if rate.attrib.get("currency") == "USD":
            return float(rate.text)

    raise Exception("Nu am găsit USD/RON")
@app.route("/display")
def display():
    return render_template("display.html")

@app.route("/prices")
def prices():
    cfg = load_config()
    discount = cfg["discount_percent"] / 100

    usd = get_gold_price()
    ron = get_usd_ron()

    base = eur * ron
    final = base * (1 - discount)

    return jsonify({
        "24K": round(final, 2),
        "18K": round(final * 0.75, 2),
        "14K": round(final * 0.585, 2),
        "8K": round(final * 0.333, 2)
    })

@app.route("/debug-kitco")
def debug_kitco():
    url = "https://www.kitco.com"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=15)

    return response.text[:5000]
