from flask import Flask, jsonify, request
import json
from datetime import datetime

app = Flask(__name__)

data_path = "data.json"

def load_data():
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def home():
    return "Car Price Crawler Backend OK"

@app.route("/data")
def get_data():
    return jsonify(load_data())

@app.route("/query")
def query():
    car = request.args.get("car", "").lower()
    all_data = load_data()
    filtered = [d for d in all_data if car in d.get("model", "").lower()]
    return jsonify(filtered)

@app.route("/update/yahoo")
def update_yahoo():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dummy = {"source": "yahoo", "model": "GT43", "brand": "Benz", "year": 2020, "color": "黑", "price": 348, "posted": now}
    current = load_data()
    current.append(dummy)
    save_data(current)
    return jsonify({"status": "Yahoo updated", "total": len(current)})

@app.route("/update/8891")
def update_8891():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dummy = {"source": "8891", "model": "740Li", "brand": "BMW", "year": 2020, "color": "白", "price": 258, "posted": now}
    current = load_data()
    current.append(dummy)
    save_data(current)
    return jsonify({"status": "8891 updated", "total": len(current)})

@app.route("/update/autonet")
def update_autonet():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dummy = {"source": "autonet", "model": "A8L", "brand": "Audi", "year": 2017, "color": "黑", "price": 138, "posted": now}
    current = load_data()
    current.append(dummy)
    save_data(current)
    return jsonify({"status": "Autonet updated", "total": len(current)})

if __name__ == "__main__":
    app.run(debug=True)
