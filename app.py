from flask import Flask, request from linebot import LineBotApi, WebhookHandler from linebot.models import MessageEvent, TextMessage, TextSendMessage from linebot.exceptions import InvalidSignatureError import os, json, re

app = Flask(name)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET") line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) handler = WebhookHandler(LINE_CHANNEL_SECRET)

預設年份與里程數

car_defaults = { 'gt43': {'brand': 'Benz', 'model': 'GT43', 'year': '2020', 'mileage': '30000'}, 'gla45': {'brand': 'Benz', 'model': 'GLA45', 'year': '2015', 'mileage': '80000'}, 's400 coupe': {'brand': 'Benz', 'model': 'S400 Coupe', 'year': '2016', 'mileage': '90000'}, 'panamera diesel': {'brand': 'Porsche', 'model': 'Panamera Diesel', 'year': '2018', 'mileage': '60000'}, 'california': {'brand': 'Ferrari', 'model': 'California', 'year': '2011', 'mileage': '50000'}, 'a8l': {'brand': 'Audi', 'model': 'A8L 4.2', 'year': '2020', 'mileage': '78000'}, 'x5': {'brand': 'BMW', 'model': 'X5', 'year': '2021', 'mileage': '30000'} }

@app.route("/webhook", methods=['POST']) def webhook(): signature = request.headers['X-Line-Signature'] body = request.get_data(as_text=True) try: handler.handle(body, signature) except InvalidSignatureError: return 'Invalid signature', 400 return 'OK'

@handler.add(MessageEvent, message=TextMessage) def handle_message(event): msg = event.message.text.lower() reply = ""

# 嘗試抓關鍵車型
matched = None
for key in car_defaults:
    if key in msg:
        matched = car_defaults[key]
        break

if not matched:
    reply = "❗ 無法解析車型，請輸入例如：2020 GT43 或 Benz GLA45"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    return

brand = matched['brand']
model = matched['model']
year = matched['year']
mileage = matched['mileage']

# 回覆格式（暫以假資料模擬）
reply = f"""

📍 {year} {brand} {model} 🛣️ 里程：{int(mileage) // 10000}萬公里 🎨 顏色：灰色（預設） 📊 市價參考：\n- Yahoo：170萬（3筆）\n- 8891：165萬（2筆）\n- 權威車訊：150萬 💰 估計收購價：135 萬左右 🏦 可貸款金額：150 萬（依書價）"""

line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if name == "main": app.run()

