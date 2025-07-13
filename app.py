from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json
import os
import re

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

# 檢查變數是否設定
if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("請先設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 載入資料
with open("data.json", "r", encoding="utf-8") as f:
    car_data = json.load(f)

with open("car_model_map.json", "r", encoding="utf-8") as f:
    model_map = json.load(f)

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
            brand, model = model_map[keyword]["brand"], model_map[keyword]["model"]
            break
    return year, mileage, color, brand, model

def estimate_price(brand, model, year, mileage, color):
    results = [c for c in car_data if c["brand"] == brand and model.lower() in c["model"].lower()]
    if year:
        results = [c for c in results if abs(c["year"] - year) <= 1]

    avg_price = sum([c["price"] for c in results]) / len(results) if results else 0
    source_count = len(results)
    estimated_price = round(avg_price * 0.85) if avg_price else 0
    loan_price = round(avg_price) if avg_price else 0

    return {
        "avg_price": round(avg_price),
        "estimated_price": estimated_price,
        "loan_price": loan_price,
        "count": source_count
    }

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
        reply = "請輸入車型（如 GT43、Gla45、S400 Coupe），我來幫你估價。"
    else:
        price_info = estimate_price(brand, model, year, mileage, color)
        reply = f"""📍 {year or '年份未知'} {brand} {model}
🛣️ 里程：{int(mileage) if mileage else '不詳'} 公里
🎨 顏色：{color or '不詳'}
📊 市價參考：{price_info['avg_price']} 萬（共 {price_info['count']} 筆）
💰 估計收購價：{price_info['estimated_price']} 萬左右
🏦 可貸款金額：{price_info['loan_price']} 萬（依書價）
"""

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/", methods=["GET"])
def index():
    return "LINE Bot 估價系統啟動中"

if __name__ == "__main__":
    app.run()
