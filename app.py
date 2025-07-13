from flask import Flask, request, jsonify
import json
import re

app = Flask(__name__)

# 讀取資料
with open("data.json", "r", encoding="utf-8") as f:
    car_data = json.load(f)

with open("car_model_map.json", "r", encoding="utf-8") as f:
    model_map = json.load(f)

# 簡易文字清洗與關鍵資訊擷取
def parse_message(msg):
    msg = msg.lower().replace("估價", "").strip()

    year_match = re.search(r"(20\d{2}|19\d{2})", msg)
    mileage_match = re.search(r"(\d{1,3})(萬|w)", msg)
    color_match = re.search(r"(白|黑|灰|銀|藍|紅|綠|金|紫|黃)", msg)

    year = year_match.group() if year_match else None
    mileage = mileage_match.group(1) + "萬" if mileage_match else None
    color = color_match.group(0) if color_match else None

    car_model = None
    for keyword in model_map:
        if keyword in msg:
            car_model = model_map[keyword]
            break

    return {
        "year": year,
        "mileage": mileage,
        "color": color,
        "model": car_model
    }

# 估價邏輯
def estimate_price(parsed):
    model = parsed["model"]
    if not model:
        return {"error": "無法辨識車型，請重新輸入"}

    matches = [c for c in car_data if model.lower() in c["車型"].lower()]
    if parsed["year"]:
        matches = [c for c in matches if parsed["year"] in c["年份"]]

    if not matches:
        return {"error": f"查無 {model} 市場資料"}

    prices = [int(c["價格"]) for c in matches if c["價格"].isdigit()]
    if not prices:
        return {"error": "無有效價格資料"}

    avg_price = int(sum(prices) / len(prices))
    low_price = int(avg_price * 0.83)
    high_price = int(avg_price * 0.87)

    return {
        "model": model,
        "year": parsed.get("year"),
        "mileage": parsed.get("mileage"),
        "color": parsed.get("color"),
        "source_count": len(prices),
        "avg_price": avg_price,
        "suggested_range": f"{low_price}–{high_price} 萬"
    }

# LINE Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    events = body.get("events", [])
    responses = []

    for event in events:
        msg_type = event["message"]["type"]
        if msg_type == "text":
            text = event["message"]["text"]
            parsed = parse_message(text)
            result = estimate_price(parsed)

            if "error" in result:
                reply = result["error"]
            else:
                reply = f"""📍 {result['year'] or ''} {result['model']}
🛣️ 里程：{result['mileage'] or '預設12萬'}
🎨 顏色：{result['color'] or '未提供'}
📊 市場均價：{result['avg_price']} 萬（{result['source_count']} 筆）
💰 收購預估：{result['suggested_range']}"""

            responses.append(reply)

        elif msg_type == "image":
            reply = "📷 已收到車輛照片，可補上年份與里程數進行估價。"
            responses.append(reply)

    return jsonify({"replies": responses})

# 測試首頁
@app.route("/", methods=["GET"])
def index():
    return "🚗 Car Price Estimation API is running."

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
