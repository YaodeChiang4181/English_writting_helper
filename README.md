# PEEL Writing Coach Bot

透過 Telegram Bot 狀態機引導使用者依序輸入 PEEL 四段內容（Point, Explanation, Example, Link），組裝後呼叫 Google Gemini API 進行架構、文法與用詞的深度審核，最後回傳結構化評估報告。

## 環境變數

請參考 `.env.example`，在專案根目錄建立 `.env` 檔案並填入以下內容：

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## 使用 Docker 啟動 (建議)

本專案提供 `docker-compose` 快速啟動：

```bash
docker-compose up -d
```

如果要查看日誌：

```bash
docker-compose logs -f bot
```

## 本地開發 (免 Docker)

1. 建立虛擬環境：
```bash
python -m venv venv
```

2. 啟動虛擬環境 (Windows)：
```bash
venv\Scripts\activate
```

3. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

4. 執行 Bot：
```bash
python src/main.py
```
