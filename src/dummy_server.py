import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import logging

logger = logging.getLogger(__name__)

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 回應 200 OK 狀態碼
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive!")
        
    def log_message(self, format, *args):
        # 覆寫此方法，關閉收到 GET 請求時的終端機輸出，避免 log 被 UptimeRobot 洗版
        pass

def run_dummy_server():
    # Render 部署時會自動提供 PORT 環境變數，如果沒有則預設使用 10000
    port = int(os.environ.get('PORT', 10000))
    server_address = ('0.0.0.0', port)
    logger.info(f"Starting dummy web server on port {port}...")
    try:
        httpd = HTTPServer(server_address, DummyHandler)
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start dummy server: {e}")

def keep_alive():
    """啟動一個背景執行緒來運行 Web 伺服器"""
    t = threading.Thread(target=run_dummy_server)
    t.daemon = True # 設定為 daemon，當主程式(機器人)結束時，此伺服器也會自動結束
    t.start()
