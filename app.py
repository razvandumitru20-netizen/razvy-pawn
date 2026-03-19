from flask import Flask, render_template, request, redirect, jsonify
import requests, json, os

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
    url = "https://api.metals.live/v1/spot/gold"
    data = requests.get(url).json()
    price_usd_per_ounce = data['price']
    usd_to_eur = 0.92
    return (price_usd_per_ounce * usd_to_eur) / 31.1035

def get_eur_ron():
    url = "https://api.exchangerate.host/latest?base=EUR&symbols=RON"
    data = requests.get(url).json()
    return data['rates']['RON']

@app.route("/display")
def display():
    return render_template("display.html")

@app.route("/prices")
def prices():
    cfg = load_config()
    discount = cfg["discount"]

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
