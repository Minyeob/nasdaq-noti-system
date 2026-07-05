import yfinance as yf
from datetime import datetime
import os
import requests
import urllib3
import json

# --- [1. 텔레그램 설정] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8556096282:AAGjfQ-IfwmvGfN_b0p9cet89W2bZMKLS4Q")
CHAT_ID = os.environ.get("CHAT_ID", "8659694273")

GITHUB_USERNAME = "내깃허브아이디"  # ⚠️ 본인의 실제 깃허브 아이디로 꼭 수정하세요!
REPO_NAME = "nasdaq-master-system"
DASHBOARD_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/nasdaq_dashboard.html"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# --- [2. 텔레그램 발송 함수 (상세 로그 출력 추가 & HTML 안전 모드 적용)] ---
def send_telegram(text):
    print("\n📨 [텔레그램 발송 시도] 서버로 메시지를 전송합니다...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # 마크다운 에러를 피하기 위해 가장 안전한 'HTML' 파싱 모드 사용
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        result = response.json()
        
        # 텔레그램 서버의 응답 결과 분석 및 출력
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

# --- [3. 시그널 판별 (HTML 안전 문법 <b></b> 으로 변경)] ---
def get_signal_info(ticker, qqq_mdd):
    if ticker == 'TQQQ':
        if qqq_mdd <= -30: return ('<div class="status-badge status-warning">🚨 [매수 5단계] TQQQ 적극 매수 타점!</div>', "🚨 <b>[매수 5단계]</b> TQQQ / QLD 적극 매수 구간! (-30% 이하)", True)
        elif qqq_mdd >= 30: return ('<div class="status-badge status-warning">🎉 [매도 타점] 전고점 +30% (TQQQ 전량 청산)</div>', "🎉 <b>[매도 타점]</b> 전고점 +30% 도달 (TQQQ 전량 청산)", True)
        elif qqq_mdd >= 20: return ('<div class="status-badge status-active">💰 [매도 타점] 전고점 +20% (TQQQ 1차 익절 50%)</div>', "💰 <b>[매도 타점]</b> 전고점 +20% 도달 (TQQQ 1차 익절 50%)", True)
        else: return ('<div class="status-badge">☕ 현재 TQQQ 타점 아님 (관망/홀딩)</div>', "☕ TQQQ: 관망/홀딩", False)
    elif ticker == 'QLD':
        if -30 < qqq_mdd <= -25: return ('<div class="status-badge status-active">🔵 [매수 4단계] QLD 25% 매수 타점 (-25%)</div>', "🔵 <b>[매수 4단계]</b> QLD 25% 매수 타점 (-25% 구간)", True)
        elif -25 < qqq_mdd <= -20: return ('<div class="status-badge status-active">🔵 [매수 3단계] QLD 25% 매수 타점 (-20%)</div>', "🔵 <b>[매수 3단계]</b> QLD 25% 매수 타점 (-20% 구간)", True)
        elif qqq_mdd >= 40: return ('<div class="status-badge status-warning">🔥 [매도 타점] 전고점 +40% (QLD 전량 익절)</div>', "🔥 <b>[매도 타점]</b> 전고점 +40% 도달 (QLD 전량 익절)", True)
        elif qqq_mdd >= 20: return ('<div class="status-badge status-active">💰 [매도 타점] 전고점 +20%~+35% (QLD 분할 익절)</div>', "💰 <b>[매도 타점]</b> 전고점 +20%~+35% 구간 (QLD 분할 익절)", True)
        else: return ('<div class="status-badge">☕ 현재 QLD 타점 아님 (관망/홀딩)</div>', "☕ QLD: 관망/홀딩", False)
    elif ticker == 'QQQ':
        if -20 < qqq_mdd <= -15: return ('<div class="status-badge status-active">🟢 [매수 2단계] QQQ 25% 매수 타점 (-15%)</div>', "🟢 <b>[매수 2단계]</b> QQQ 25% 매수 타점 (-15% 구간)", True)
        elif -15 < qqq_mdd <= -10: return ('<div class="status-badge status-active">🟢 [매수 1단계] QQQ 25% 매수 타점 (-10%)</div>', "🟢 <b>[매수 1단계]</b> QQQ 25% 매수 타점 (-10% 구간)", True)
        elif 15 <= qqq_mdd < 26: return ('<div class="status-badge status-active">💰 [매도 타점] 전고점 +15%~+25% (전략 A 분할 익절)</div>', "💰 <b>[매도 타점]</b> 전고점 +15%~+25% 구간 (QQQ 분할 익절)", True)
        else: return ('<div class="status-badge">☕ 현재 QQQ 타점 아님 (관망/홀딩)</div>', "☕ QQQ: 관망/홀딩", False)
    return ('<div class="status-badge">☕
