# 出國行前天氣與穿衣助手

提供準備出國旅遊的人查詢目的地目前天氣、當地時間與未來七日預報，並依溫度和降雨機率整理行李及穿衣提醒。

## 功能

- 一鍵查詢東京、首爾、曼谷、倫敦、紐約與雪梨。
- 搜尋全球城市；同名城市會列出國家及時區供選擇。
- 顯示當地時間、氣溫、體感溫度、相對濕度與風速。
- 顯示未來七日溫度、降雨機率及打包建議。
- 外部服務錯誤或查無城市時顯示繁體中文提示。

## 本機執行

需要 Python 3.12。

```powershell
py -3.12 -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

接著在瀏覽器開啟 `http://127.0.0.1:5000`。應用程式會透過 HTTPS 呼叫 Open-Meteo，無須 API 金鑰。

## 部署至 Vercel

將此專案推送至 GitHub，於 Vercel 匯入該儲存庫即可部署。根目錄的 `vercel.json` 已設定 Python Serverless Function 與路由。部署環境需使用 Python 3.12。

## 初始化 Git 並推送至 GitHub

安裝 Git 並在 GitHub 建立空白儲存庫後，於此專案根目錄執行以下命令；請將網址替換成自己的 GitHub 儲存庫網址。

```powershell
git init
git add .
git commit -m "建立出國行前天氣與穿衣助手"
git branch -M main
git remote add origin <GitHub 儲存庫網址>
git push -u origin main
```

## 資料來源與授權

天氣資料來自 [Open-Meteo](https://open-meteo.com/)。依 CC BY 4.0 授權要求，網站頁尾標示：Weather data by Open-Meteo.com (CC BY 4.0)。
