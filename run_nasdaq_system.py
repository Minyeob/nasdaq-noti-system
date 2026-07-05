import yfinance as yf
from datetime import datetime
import os
import requests
import urllib3
import json

# --- [1. 텔레그램 설정] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8556096282:AAGjfQ-IfwmvGfN_b0p9cet89W2bZMKLS4Q")
CHAT_ID = os.environ.get("CHAT_ID", "8659694273")

GITHUB_USERNAME = "내깃허브아이디"  # ⚠️ 본인의 실제 깃허브 아이디로 수정 필수!
REPO_NAME = "nasdaq-master-system"
DASHBOARD_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/nasdaq_dashboard.html"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# --- [2. 텔레그램 발송 함수] ---
def send_telegram(text):
    print("\n📨 [텔레그램 발송 시도] 서버로 메시지를 전송합니다...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        result = response.json()
        if result.get("ok"):
            print("✅ [전송 성공] 텔레그램으로 알림 메시지가 정상 발송되었습니다!")
            return True
        else:
            print(f"❌ [전송 실패] 텔레그램 서버 거절 이유: {result}")
            return False
    except Exception as e:
        print(f"❌ [통신 에러] 텔레그램 API 호출 중 예외 발생: {e}")
        return False

TICKERS = ['QQQ', 'QLD', 'TQQQ']

def get_stock_data(ticker):
    try:
        print(f"📡 {ticker} 최신 시세 불러오는 중...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty: return None
            
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        ath = hist['High'].max()
        from_ath_percent = ((current_price - ath) / ath) * 100
        
        return {
            "ticker": ticker, "current": f"{current_price:.2f}", "prev": f"{prev_close:.2f}",
            "change": f"{change:.2f}", "percent": f"{change_percent:.2f}", "ath": f"{ath:.2f}",
            "mdd": f"{from_ath_percent:.2f}", "raw_mdd": from_ath_percent, "raw_change": change
        }
    except Exception as e:
        print(f"❌ {ticker} 오류: {e}")
        return None

# --- [3. 시그널 판별 함수 (줄바꿈 오류 완벽 해결)] ---
def get_signal_info(ticker, qqq_mdd):
    if ticker == 'TQQQ':
        if qqq_mdd <= -30:
            badge = '<div class="status-badge status-warning">🚨 [매수 5단계] TQQQ 적극 매수 타점!</div>'
            msg = "🚨 <b>[매수 5단계]</b> TQQQ / QLD 적극 매수 구간! (-30% 이하)"
            return (badge, msg, True)
        elif qqq_mdd >= 30:
            badge = '<div class="status-badge status-warning">🎉 [매도 타점] 전고점 +30% (TQQQ 전량 청산)</div>'
            msg = "🎉 <b>[매도 타점]</b> 전고점 +30% 도달 (TQQQ 전량 청산)"
            return (badge, msg, True)
        elif qqq_mdd >= 20:
            badge = '<div class="status-badge status-active">💰 [매도 타점] 전고점 +20% (TQQQ 1차 익절 50%)</div>'
            msg = "💰 <b>[매도 타점]</b> 전고점 +20% 도달 (TQQQ 1차 익절 50%)"
            return (badge, msg, True)
        else:
            badge = '<div class="status-badge">☕ 현재 TQQQ 타점 아님 (관망/홀딩)</div>'
            msg = "☕ TQQQ: 관망/홀딩"
            return (badge, msg, False)
            
    elif ticker == 'QLD':
        if -30 < qqq_mdd <= -25:
            badge = '<div class="status-badge status-active">🔵 [매수 4단계] QLD 25% 매수 타점 (-25%)</div>'
            msg = "🔵 <b>[매수 4단계]</b> QLD 25% 매수 타점 (-25% 구간)"
            return (badge, msg, True)
        elif -25 < qqq_mdd <= -20:
            badge = '<div class="status-badge status-active">🔵 [매수 3단계] QLD 25% 매수 타점 (-20%)</div>'
            msg = "🔵 <b>[매수 3단계]</b> QLD 25% 매수 타점 (-20% 구간)"
            return (badge, msg, True)
        elif qqq_mdd >= 40:
            badge = '<div class="status-badge status-warning">🔥 [매도 타점] 전고점 +40% (QLD 전량 익절)</div>'
            msg = "🔥 <b>[매도 타점]</b> 전고점 +40% 도달 (QLD 전량 익절)"
            return (badge, msg, True)
        elif qqq_mdd >= 20:
            badge = '<div class="status-badge status-active">💰 [매도 타점] 전고점 +20%~+35% (QLD 분할 익절)</div>'
            msg = "💰 <b>[매도 타점]</b> 전고점 +20%~+35% 구간 (QLD 분할 익절)"
            return (badge, msg, True)
        else:
            badge = '<div class="status-badge">☕ 현재 QLD 타점 아님 (관망/홀딩)</div>'
            msg = "☕ QLD: 관망/홀딩"
            return (badge, msg, False)
            
    elif ticker == 'QQQ':
        if -20 < qqq_mdd <= -15:
            badge = '<div class="status-badge status-active">🟢 [매수 2단계] QQQ 25% 매수 타점 (-15%)</div>'
            msg = "🟢 <b>[매수 2단계]</b> QQQ 25% 매수 타점 (-15% 구간)"
            return (badge, msg, True)
        elif -15 < qqq_mdd <= -10:
            badge = '<div class="status-badge status-active">🟢 [매수 1단계] QQQ 25% 매수 타점 (-10%)</div>'
            msg = "🟢 <b>[매수 1단계]</b> QQQ 25% 매수 타점 (-10% 구간)"
            return (badge, msg, True)
        elif 15 <= qqq_mdd < 26:
            badge = '<div class="status-badge status-active">💰 [매도 타점] 전고점 +15%~+25% (전략 A 분할 익절)</div>'
            msg = "💰 <b>[매도 타점]</b> 전고점 +15%~+25% 구간 (QQQ 분할 익절)"
            return (badge, msg, True)
        else:
            badge = '<div class="status-badge">☕ 현재 QQQ 타점 아님 (관망/홀
