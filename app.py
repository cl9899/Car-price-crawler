from flask import Flask, request from linebot import LineBotApi, WebhookHandler from linebot.models import MessageEvent, TextMessage, TextSendMessage from linebot.exceptions import InvalidSignatureError import os import json import re

app = Flask(name)

讀取環境變數中的 LINE Token 和 Secret

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN") LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN) handler = WebhookHandler(LINE_CHANNEL_SECRET)

預設年份與里程數（部分範例）

car_defaults = { 'gt43': {'brand': 'benz', 'model': 'gt43', 'year': 2020, 'mileage': 30000}, 'california': {'brand': 'ferrari', 'model': 'california', 'year': 2011, 'mileage': 40000}, # 可依需求擴充 }

@app.route("/webhook", methods=['POST']) def webhook(): signature = request.headers['X-Line-Signature'] body = request.get_data(as_text=True) try: handler.handle(body, signature) except InvalidSignatureError: return 'Invalid signature', 400 return 'OK'

@handler.add(MessageEvent, message=TextMessage) def handle_message(event): user_msg = event.message.text.lower()

# 範例：模糊查詢回傳預設估價
for key in car_defaults:
    if key in user_msg:
        info = car_defaults[key]
        reply = f"📍 預估車款：{info['year']} {info['brand'].upper()} {info['model'].upper()}\n"
        reply += f"🛣️ 預設里程：{info['mileage']} 公里\n"
        reply += "📊 系統將自動查詢市價並估算收購價..."
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )
        return

# 預設回覆
line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text="請輸入車款或年份，例如：2020 GT43 或 California")
)

if name == "main": app.run()

