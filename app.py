"""出國行前天氣與穿衣助手。"""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

熱門城市 = [
    {"名稱": "東京", "旗幟": "🇯🇵", "搜尋名稱": "Tokyo"},
    {"名稱": "首爾", "旗幟": "🇰🇷", "搜尋名稱": "Seoul"},
    {"名稱": "曼谷", "旗幟": "🇹🇭", "搜尋名稱": "Bangkok"},
    {"名稱": "倫敦", "旗幟": "🇬🇧", "搜尋名稱": "London"},
    {"名稱": "紐約", "旗幟": "🇺🇸", "搜尋名稱": "New York"},
    {"名稱": "雪梨", "旗幟": "🇦🇺", "搜尋名稱": "Sydney"},
]


class 外部服務錯誤(Exception):
    """外部天氣服務無法提供資料時使用。"""


def _取得_json(url, params):
    try:
        回應 = requests.get(url, params=params, timeout=5)
        回應.raise_for_status()
        return 回應.json()
    except requests.exceptions.Timeout as 錯誤:
        raise 外部服務錯誤("連線等候逾時，請稍後再試。") from 錯誤
    except requests.exceptions.RequestException as 錯誤:
        raise 外部服務錯誤("目前無法連線至天氣資料服務，請稍後再試。") from 錯誤
    except ValueError as 錯誤:
        raise 外部服務錯誤("天氣資料格式暫時無法讀取，請稍後再試。") from 錯誤


def _搜尋城市(名稱):
    資料 = _取得_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": 名稱, "count": 5, "language": "zh", "format": "json"},
    )
    結果 = 資料.get("results") or []
    if not 結果:
        return []
    return [
        {
            "名稱": 項目.get("name", 名稱),
            "國家": 項目.get("country", ""),
            "時區": 項目.get("timezone", "UTC"),
            "緯度": 項目["latitude"],
            "經度": 項目["longitude"],
        }
        for 項目 in 結果
        if "latitude" in 項目 and "longitude" in 項目
    ]


def _取得天氣(城市):
    資料 = _取得_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": 城市["緯度"],
            "longitude": 城市["經度"],
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 7,
        },
    )
    目前 = 資料.get("current", {})
    每日 = 資料.get("daily", {})
    每日預報 = []
    for 索引, 日期 in enumerate(每日.get("time", [])):
        每日預報.append(
            {
                "日期": 日期,
                "最低": _取值(每日.get("temperature_2m_min"), 索引),
                "最高": _取值(每日.get("temperature_2m_max"), 索引),
                "降雨": _取值(每日.get("precipitation_probability_max"), 索引),
            }
        )

    有效低溫 = [項目["最低"] for 項目 in 每日預報 if 項目["最低"] is not None]
    有效高溫 = [項目["最高"] for 項目 in 每日預報 if 項目["最高"] is not None]
    有效降雨 = [項目["降雨"] for 項目 in 每日預報 if 項目["降雨"] is not None]
    建議 = []
    if 有效低溫 and min(有效低溫) < 10:
        建議.append("預報低溫低於 10°C，帶上羽絨衣或發熱衣，早晚保暖。")
    日溫差 = [
        項目["最高"] - 項目["最低"]
        for 項目 in 每日預報
        if 項目["最高"] is not None and 項目["最低"] is not None
    ]
    if 日溫差 and max(日溫差) > 10:
        建議.append("一週日夜溫差較大，採洋蔥式穿搭，方便依體感增減衣物。")
    if 有效降雨 and max(有效降雨) >= 40:
        建議.append("有幾天降雨機率達 40% 以上，記得帶折疊傘或防水鞋。")
    if 有效高溫 and max(有效高溫) >= 28:
        建議.append("白天偏熱，準備透氣衣物、防曬用品並適時補充水分。")
    if not 建議:
        建議.append("近期氣溫較舒適，帶件薄外套並依每日預報調整穿搭。")

    時區名稱 = 城市.get("時區") or 資料.get("timezone") or "UTC"
    try:
        當地時間 = datetime.now(ZoneInfo(時區名稱)).strftime("%Y年%m月%d日 %H:%M")
    except (ZoneInfoNotFoundError, ValueError):
        時區名稱 = 資料.get("timezone") or "UTC"
        當地時間 = datetime.now(ZoneInfo("UTC")).strftime("%Y年%m月%d日 %H:%M")

    return {
        "目前": 目前,
        "預報": 每日預報,
        "建議": 建議[:4],
        "時區": 時區名稱,
        "當地時間": 當地時間,
    }


def _取值(欄位, 索引):
    if 欄位 is None or 索引 >= len(欄位):
        return None
    return 欄位[索引]


@app.route("/", methods=["GET", "POST"])
def 首頁():
    搜尋詞 = request.form.get("city", "").strip() if request.method == "POST" else request.args.get("city", "東京").strip()
    選擇索引 = request.form.get("result", "0") if request.method == "POST" else "0"
    錯誤訊息 = None
    城市清單 = []
    城市 = None
    天氣 = None

    if not 搜尋詞:
        錯誤訊息 = "請輸入想查詢的城市名稱。"
    else:
        try:
            城市清單 = _搜尋城市(搜尋詞)
            if not 城市清單:
                錯誤訊息 = "找不到這個城市，請確認拼字或改用英文城市名再試一次。"
            else:
                try:
                    索引 = int(選擇索引)
                except ValueError:
                    索引 = 0
                索引 = max(0, min(索引, len(城市清單) - 1))
                城市 = 城市清單[索引]
                天氣 = _取得天氣(城市)
        except 外部服務錯誤 as 錯誤:
            錯誤訊息 = str(錯誤)

    return render_template(
        "index.html",
        熱門城市=熱門城市,
        搜尋詞=搜尋詞,
        城市清單=城市清單,
        選擇索引=選擇索引,
        城市=城市,
        天氣=天氣,
        錯誤訊息=錯誤訊息,
    )


if __name__ == "__main__":
    app.run(debug=False)
