
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import os
import re
from datetime import datetime

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

# 驗證環境變數
if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("請設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 載入資料
with open("data.json", "r", encoding="utf-8") as f:
    car_data = json.load(f)

with open("car_model_map.json", "r", encoding="utf-8") as f:
    model_map = json.load(f)

# 載入歷史實價紀錄
if os.path.exists("history.json"):
    with open("history.json", "r", encoding="utf-8") as f:
        history = json.load(f)
else:
    history = []

# 資料清洗：排除異常值
def clean_data(records):
    prices = [r["price"] for r in records]
    if len(prices) < 3:
        return records
    avg = sum(prices) / len(prices)
    std = (sum((p - avg) ** 2 for p in prices) / len(prices)) ** 0.5
    return [r for r in records if abs(r["price"] - avg) <= std * 1.5]

# 拆解輸入訊息
def parse_input(text):
    year_match = re.search(r"(20\d{2}|19\d{2})", text)
    mileage_match = re.search(r"(\d+(?:\.\d+)?)(萬|公里|km)?", text)
    color_match = re.search(r"(白|黑|銀|灰|紅|藍|綠|紫|金|橘)", text)

    year = int(year_match.group(1)) if year_match else None
    mileage = float(mileage_match.group(1)) * 10000 if mileage_match and '萬' in text else None
    color = color_match.group(1) if color_match else None

    brand, model = None, None
    for keyword in model_map:
        if keyword.lower() in text.lower():
            brand = model_map[keyword]["brand"]
            model = model_map[keyword]["model"]
            break
    return year, mileage, color, brand, model

# 主估價邏輯
def estimate_price(brand, model, year, mileage, color):
    matches = [r for r in car_data if r["brand"] == brand and model.lower() in r["model"].lower()]
    if year:
        matches = [r for r in matches if abs(r["year"] - year) <= 1]
    matches = clean_data(matches)

    if not matches:
        return None

    # 各來源平均
    def group_by_source(data):
        from collections import defaultdict
        sources = defaultdict(list)
        for r in data:
            sources[r["source"]].append(r["price"])
        return {k: {"avg": round(sum(v)/len(v)), "count": len(v)} for k, v in sources.items()}

    source_stats = group_by_source(matches)
    all_prices = [r["price"] for r in matches]
    avg_price = round(sum(all_prices) / len(all_prices))
    estimated = round(avg_price * 0.85)
    fallback = any(v["count"] < 2 for v in source_stats.values())

    return {
        "brand": brand,
        "model": model,
        "year": year,
        "mileage": mileage,
        "color": color,
        "avg_price": avg_price,
        "estimated_price": estimated,
        "loan_price": avg_price,
        "count": len(matches),
        "sources": source_stats,
        "fallback": fallback
    }

def find_history(brand, model):
    same = [h for h in history if h["brand"] == brand and h["model"] == model]
    return sorted(same, key=lambda x: x["date"], reverse=True)

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400, "Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    year, mileage, color, brand, model = parse_input(msg)

    if not model:
        reply = "請輸入車型（如 GT43、Altis、S400 Coupe），我來幫你估價。"
    else:
        result = estimate_price(brand, model, year, mileage, color)
        if not result:
            reply = f"找不到 {brand} {model} 的估價資料，請確認輸入是否正確。"
        else:
            reply = f"""📍 {result["year"] or "年份不詳"} {brand} {model}
🛣️ 里程：{int(result["mileage"]) if result["mileage"] else "不詳"} 公里
🎨 顏色：{result["color"] or "不詳"}
📊 市價參考：
""" + "".join([f"- {src}：{info['avg']} 萬（{info['count']} 筆）\n" for src, info in result["sources"].items()]) + f"""💰 估計收購價：{result["estimated_price"]} 萬
🏦 可貸款金額：{result["loan_price"]} 萬（依書價）"""

            hist = find_history(brand, model)
            if hist:
                reply += "\n📁 歷史實價：\n" + "\n".join([f"- {h['date']} 買 {h['price']} 萬，跑 {h['mileage']}" for h in hist])

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/", methods=["GET"])
def index():
    return "✅ LINE Bot 車價估價系統運作中"

if __name__ == "__main__":
    app.run()
