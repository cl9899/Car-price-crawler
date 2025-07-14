✅ car_price_updater.py

整合 Yahoo、8891、權威車訊、ABC 好車、SUM 資料來源 + 預留拍賣場

import json import datetime

模擬爬蟲函式（正式版應連接實際爬蟲邏輯）

def fetch_yahoo(): return [ {"brand": "Mercedes-Benz", "model": "GT43", "year": 2021, "price": 328, "color": "黑", "source": "Yahoo", "sold_at": "2025-07-10"}, ]

def fetch_8891(): return [ {"brand": "Ferrari", "model": "California", "year": 2011, "price": 468, "color": "紅", "source": "8891", "sold_at": "2025-07-12"}, ]

def fetch_authority(): return [ {"brand": "Audi", "model": "A8L", "year": 2020, "price": 150, "color": "白", "source": "權威車訊", "sold_at": None}, ]

def fetch_abc(): return [ {"brand": "Toyota", "model": "Altis", "year": 2010, "price": 23, "color": "銀", "source": "ABC", "sold_at": "2025-07-05"}, ]

def fetch_sum(): return [ {"brand": "BMW", "model": "X5", "year": 2019, "price": 178, "color": "黑", "source": "SUM", "sold_at": "2025-07-11"}, ]

預留：拍賣場（需登入後串接）

def fetch_auction(): return []

排除異常價格（簡單示意：價格超出平均兩倍或低於一半）

def filter_outliers(data): from statistics import mean, stdev try: prices = [d['price'] for d in data if d['price'] > 0] avg = mean(prices) std = stdev(prices) if len(prices) > 1 else 0 return [d for d in data if abs(d['price'] - avg) <= 2 * std] except: return data

整合所有來源資料

def combine_data(): all_data = [] for fetch in [fetch_yahoo, fetch_8891, fetch_authority, fetch_abc, fetch_sum, fetch_auction]: try: all_data.extend(fetch()) except Exception as e: print(f"❌ 無法讀取 {fetch.name}: {e}")

# 排除異常價格
clean_data = filter_outliers(all_data)
return clean_data

寫入至 data.json

if name == "main": all_data = combine_data() with open("data.json", "w", encoding="utf-8") as f: json.dump(all_data, f, ensure_ascii=False, indent=2) print(f"✅ 已更新車價資料，共 {len(all_data)} 筆（{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）")

