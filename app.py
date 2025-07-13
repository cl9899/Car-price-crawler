
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os, json, re

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Load car price data
def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def format_response(car, matches):
    response = f"📍 {car['year']} {car['brand']} {car['model']}\n"
    response += f"🛣️ 里程：{car.get('mileage', '未知')}\n"
    response += f"🎨 顏色：{car.get('color', '未知')}\n"
    response += "📊 市價參考：\n"
    if 'yahoo' in matches:
        response += f"- Yahoo：{matches['yahoo']['avg']}萬（{matches['yahoo']['count']}筆）\n"
    if '8891' in matches:
        response += f"- 8891：{matches['8891']['avg']}萬（{matches['8891']['count']}筆）\n"
    if 'authority' in matches:
        response += f"- 權威車訊：{matches['authority']}萬\n"
    response += f"💰 估計收購價：{car.get('estimate_price', '估價中')} 萬\n"
    response += f"🏦 可貸款金額：{matches.get('authority', '書價未知')} 萬（依書價）"
    return response

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.lower()
    data = load_data()

    matched = None
    for car in data:
        key = f"{car['year']} {car['brand']} {car['model']}".lower()
        if all(x in key for x in msg.split()):
            matched = car
            break

    if matched:
        response = format_response(matched, matched.get("sources", {}))
    else:
        response = "查無相關資料，請再確認車款或輸入格式。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))

@app.route("/update", methods=["GET"])
def update_data():
    # Dummy endpoint to trigger manual update (to be implemented)
    return jsonify({"status": "update triggered"})

if __name__ == "__main__":
    app.run(debug=True)
