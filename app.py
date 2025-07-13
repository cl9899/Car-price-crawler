from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import os
import json
import re

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 預設年份與里程數（部分範例）
car_defaults = {
    'gt43': {'brand': 'benz', 'year': 2020, 'mileage': 30000},
    'panamera diesel': {'brand': 'porsche', 'year': 2018, 'mileage': 60000},
    's400 coupe': {'brand': 'benz', 'year': 2015, 'mileage': 90000},
    'gla45': {'brand': 'benz', 'year': 2015, 'mileage': 80000},
}

def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def estimate_price(brand, model, year, mileage):
    data = load_data()
    matches = [d for d in data if brand in d['品牌'].lower() and model in d['車型'].lower()]
    if not matches:
        return None

    prices = [int(d['價格']) for d in matches if d['價格'].isdigit()]
    if not prices:
        return None

    avg_price = sum(prices) // len(prices)
    buy_price = int(avg_price * 0.85)
    source_info = f"市價平均：{avg_price} 萬（{len(prices)} 筆）"
    return avg_price, buy_price, source_info

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip().lower()
    response = ""
    found = False

    for keyword, default in car_defaults.items():
        if keyword in msg:
            brand = default['brand']
            model = keyword
            year = default['year']
            mileage = default['mileage']
            result = estimate_price(brand, model, year, mileage)
            if result:
                avg, buy, info = result
                response = f"""📍 {year} {brand.upper()} {model.upper()}
🛣️ 里程：約 {mileage//10000} 萬公里
📊 {info}
💰 估計收購價：{buy} 萬左右
🏦 可貸款金額：{avg} 萬（依書價）"""
            else:
                response = f"查無 {model.upper()} 市價資料，請稍後再試或補充更多關鍵字。"
            found = True
            break

    if not found:
        response = "請輸入車型（如 GT43、Gla45、S400 Coupe），我來幫你估價。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

if __name__ == "__main__":
    app.run()
