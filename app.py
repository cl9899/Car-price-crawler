from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import re

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") or "你的 channel access token"
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET") or "你的 channel secret"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "LINE Auto Estimator Backend OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    signature = request.headers['X-Line-Signature']

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)

    return "OK", 200

def parse_message(text):
    text = text.strip()
    result = {
        "action": None,
        "year": None,
        "model": None,
        "mileage": None,
        "price": None,
        "features": []
    }

    if "更新" in text:
        result["action"] = "update"
    elif "查詢" in text or "估價" in text:
        result["action"] = "estimate"
    elif "買" in text:
        result["action"] = "record"
    else:
        result["action"] = "parse"

    year_match = re.search(r"(20\d{2}|19\d{2})", text)
    if year_match:
        result["year"] = year_match.group()

    mileage_match = re.search(r"跑?(\d+(\.\d+)?)(萬)?", text)
    if mileage_match:
        num = float(mileage_match.group(1))
        if mileage_match.group(3):  # 有 "萬"
            num *= 10000
        result["mileage"] = int(num)

    price_match = re.search(r"買(\d+)(萬)?", text)
    if price_match:
        price = int(price_match.group(1))
        if price_match.group(2):  # 有 "萬"
            price *= 10000
        result["price"] = price

    tokens = text.split()
    for token in tokens:
        if result["model"] is None and token.upper() in text.upper():
            result["model"] = token
        elif token not in [result["year"], str(result["mileage"]), str(result["price"]), result["model"]]:
            result["features"].append(token)

    return result

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    parsed = parse_message(user_message)

    reply = ""
    if parsed["action"] == "update":
        reply = "🔄 已觸發車價資料更新作業"
    elif parsed["action"] == "estimate":
        reply = f"📌 查詢車輛：{parsed['year']} {parsed['model']}（{parsed['mileage']}公里）\n📊 系統正在評估中，請稍後..."
    elif parsed["action"] == "record":
        reply = f"✅ 已記錄 {parsed['year']} {parsed['model']} 的實際收購價 {parsed['price']} 元"
    else:
        reply = f"📥 已解析：{parsed['year']} {parsed['model']}，里程 {parsed['mileage']}，配備：{'、'.join(parsed['features'])}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
