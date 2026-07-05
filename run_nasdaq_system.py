import yfinance as yf
from datetime import datetime
import os
import requests
import urllib3
import json

# --- [1. 텔레그램 설정 (깃허브 보안 환경변수 우선 적용)] ---
# 깃허브 시크릿에 설정된 토큰이 없으면 내장된 기본 토큰을 사용합니다.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8556096282:AAGjfQ-IfwmvGfN_b0p9cet89W2bZMKLS4Q")
CHAT_ID = os.environ.get("CHAT_ID", "8659694273")

# 내 깃허브 아이디와 저장소 이름으로 대시보드 링크 생성 (본인 아이디로 수정 필요!)
GITHUB_USERNAME = "내깃허브아이디"  # 예: "quant-trader"
REPO_NAME = "nasdaq-master-system"   # 예: "nasdaq-master-system"
DASHBOARD_URL = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/nasdaq_dashboard.html"

# SSL 무시 설정
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, verify=False, timeout=10)
        return response.json()
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
        return None

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

def get_signal_info(ticker, qqq_mdd):
    if ticker == 'TQQQ':
        if qqq_mdd <= -30: return ('<div class="status-badge status-warning">🚨 [매수 5단계] TQQQ 적극 매수 타점!</div>', "🚨 **[매수 5단계]** TQQQ / QLD 적극 매수 구간! (-30% 이하)", True)
        elif qqq_mdd >= 30: return ('<div class="status-badge status-warning">🎉 [매도 타점] 전고점 +30% (TQQQ 전량 청산)</div>', "🎉 **[매도 타점]** 전고점 +30% 도달 (TQQQ 전량 청산)", True)
        elif qqq_mdd >= 20: return ('<div class="status-badge status-active">💰 [매도 타점] 전고점 +20% (TQQQ 1차 익절 50%)</div>', "💰 **[매도 타점]** 전고점 +20% 도달 (TQQQ 1차 익절 50%)", True)
        else: return ('<div class="status-badge">☕ 현재 TQQQ 타점 아님 (관망/홀딩)</div>', "☕ TQQQ: 관망/홀딩", False)
    elif ticker == 'QLD':
        if -30 < qqq_mdd <= -25: return ('<div class="status-badge status-active">🔵 [매수 4단계] QLD 25% 매수 타점 (-25%)</div>', "🔵 **[매수 4단계]** QLD 25% 매수 타점 (-25% 구간)", True)
        elif -25 < qqq_mdd <= -20: return ('<div class="status-badge status-active">🔵 [매수 3단계] QLD 25% 매수 타점 (-20%)</div>', "🔵 **[매수 3단계]** QLD 25% 매수 타점 (-20% 구간)", True)
        elif qqq_mdd >= 40: return ('<div class="status-badge status-warning">🔥 [매도 타점] 전고점 +40% (QLD 전량 익절)</div>', "🔥 **[매도 타점]** 전고점 +40% 도달 (QLD 전량 익절)", True)
        elif qqq_mdd >= 20: return ('<div class="status-badge status-active">💰 [매도 타점] 전고점 +20%~+35% (QLD 분할 익절)</div>', "💰 **[매도 타점]** 전고점 +20%~+35% 구간 (QLD 분할 익절)", True)
        else: return ('<div class="status-badge">☕ 현재 QLD 타점 아님 (관망/홀딩)</div>', "☕ QLD: 관망/홀딩", False)
    elif ticker == 'QQQ':
        if -20 < qqq_mdd <= -15: return ('<div class="status-badge status-active">🟢 [매수 2단계] QQQ 25% 매수 타점 (-15%)</div>', "🟢 **[매수 2단계]** QQQ 25% 매수 타점 (-15% 구간)", True)
        elif -15 < qqq_mdd <= -10: return ('<div class="status-badge status-active">🟢 [매수 1단계] QQQ 25% 매수 타점 (-10%)</div>', "🟢 **[매수 1단계]** QQQ 25% 매수 타점 (-10% 구간)", True)
        elif 15 <= qqq_mdd < 26: return ('<div class="status-badge status-active">💰 [매도 타점] 전고점 +15%~+25% (전략 A 분할 익절)</div>', "💰 **[매도 타점]** 전고점 +15%~+25% 구간 (QQQ 분할 익절)", True)
        else: return ('<div class="status-badge">☕ 현재 QQQ 타점 아님 (관망/홀딩)</div>', "☕ QQQ: 관망/홀딩", False)
    return ('<div class="status-badge">☕ 관망</div>', "☕ 관망", False)

if __name__ == '__main__':
    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    qqq_data = get_stock_data('QQQ')
    if not qqq_data: exit()
        
    base_mdd = qqq_data['raw_mdd']
    cards_html = ""
    telegram_lines = [f"📊 **[나스닥 마스터 시스템 알림]**", f"⏰ 기준: {now_str}\n"]
    telegram_lines.append(f"🛰️ **기준 지수 (QQQ)**\n• 현재가: **${qqq_data['current']}** ({qqq_data['percent']}%)\n• 52주 고점 대비 (MDD): **{qqq_data['mdd']}%**\n")
    telegram_lines.append("=" * 25)
    
    active_signals_count = 0
    for t in TICKERS:
        d = qqq_data if t == 'QQQ' else get_stock_data(t)
        if d:
            is_up = d['raw_change'] >= 0
            color_class = "up" if is_up else "down"
            sign = "+" if is_up else ""
            html_badge, tg_text, is_active = get_signal_info(d['ticker'], base_mdd)
            
            if is_active:
                active_signals_count += 1
                telegram_lines.append(f"\n💡 **[{d['ticker']} 액션 시그널 발생!]**\n└ {tg_text}")
            
            cards_html += f"""
            <div class="ticker-card">
                <div class="ticker-title"><span>{d['ticker']}</span> <small style="font-size: 13px; color: #6c757d;">52주 최고: ${d['ath']}</small></div>
                <div><span class="price-current">${d['current']}</span><span class="price-change {color_class}">{sign}{d['change']} ({sign}{d['percent']}%)</span></div>
                <ul class="stats-list"><li><span>전일 종가</span> <strong>${d['prev']}</strong></li><li><span>52주 최고가 대비 (MDD)</span> <strong class="mdd-highlight">{d['mdd']}%</strong></li></ul>
                {html_badge}
            </div>"""
        else: cards_html += f"""<div class="ticker-card"><div class="ticker-title"><span>{t}</span></div><p style="color:red;">데이터 실패</p></div>"""

    if active_signals_count == 0:
        telegram_lines.append("\n☕ **현재는 매수/매도 액션 타점이 아닙니다.**\n└ 평온하게 관망(Holding) 유지하세요.")
        
    telegram_lines.append("\n" + "=" * 25)
    # 텔레그램 하단에 내 웹사이트 대시보드 링크 추가!
    telegram_lines.append(f"\n🌐 **[실시간 웹 대시보드 열기]**\n└ {DASHBOARD_URL}")
    
    send_telegram("\n".join(telegram_lines))

    # HTML 생성
    html_content = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>나스닥 마스터 분할 매매 시스템</title>
    <style>:root {{--bg: #f8f9fa; --card: #fff; --text: #212529; --muted: #6c757d; --border: #dee2e6; --blue: #0d6efd; --green: #198754; --red: #dc3545; --purple: #6f42c1;}} body {{font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text); padding: 30px 20px; margin: 0;}} .container {{max-width: 1100px; margin: 0 auto; background: var(--card); padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);}} h1 {{font-size: 26px; margin-bottom: 10px;}} .summary {{background: #e8f4f8; border-left: 4px solid var(--blue); padding: 15px; border-radius: 4px; margin-bottom: 25px; font-size: 14px;}} .header {{display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;}} .grid {{display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 35px;}} .ticker-card {{border: 1px solid var(--border); border-radius: 8px; padding: 20px; background: #fdfdfd;}} .ticker-title {{font-size: 18px; font-weight: 700; margin: 0 0 10px 0; display: flex; justify-content: space-between;}} .price-current {{font-size: 24px; font-weight: 800;}} .price-change {{font-size: 14px; font-weight: 600; margin-left: 8px;}} .up {{color: var(--red);}} .down {{color: var(--blue);}} .stats-list {{margin: 15px 0 0 0; padding: 0; list-style: none; font-size: 13.5px; color: var(--muted);}} .stats-list li {{display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #eee;}} .mdd-highlight {{font-weight: 700; color: var(--blue);}} .status-badge {{margin-top: 15px; padding: 10px; border-radius: 6px; text-align: center; font-weight: 700; font-size: 13.5px; background: #e9ecef; color: #495057;}} .status-active {{background: #d1e7dd; color: #0f5132; border: 1px solid #badbcc;}} .status-warning {{background: #f8d7da; color: #842029; border: 1px solid #f5c2c7;}} table {{width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 30px; font-size: 14px;}} th, td {{padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top;}} th {{background: #f8f9fa; font-weight: 700; border-bottom: 2px solid #adb5bd;}} .badge {{display: inline-block; padding: 3px 7px; border-radius: 4px; font-size: 11.5px; font-weight: 700; color: #fff; margin-bottom: 3px;}} .bg-buy {{background: var(--blue);}} .bg-sell-a {{background: var(--green);}} .bg-sell-b {{background: var(--purple);}} .bg-sell-c {{background: #fd7e14;}} .bg-emergency {{background: var(--red);}} .point {{font-weight: 700; color: var(--blue);}} .trigger {{font-weight: 600; color: #343a40;}} .rules {{background: #fdfdfd; border: 1px solid var(--border); border-radius: 8px; padding: 15px 20px; font-size: 13.5px;}}</style></head>
    <body><div class="container"><h1>📈 나스닥 마스터 분할 매매 시스템</h1><div class="summary"><strong>핵심 원칙:</strong> 지수 하락 폭에 따라 자산 배분(1배수 ➔ 2배수 ➔ 3배수)을 자동 조절하며, 상승 모멘텀과 침체 여부에 따라 출구를 분리한 시스템 모델.</div>
    <div class="header"><h2 style="font-size: 18px; margin: 0;">🛰️ 실시간 매매 시그널 모니터링</h2><span style="font-size: 13px; color: #6c757d;">⏰ 시세 기준: {now_str}</span></div>
    <div class="grid">{cards_html}</div>
    <h2 style="font-size: 18px; margin: 0 0 10px 0;">📋 매수 및 매도 액션 매트릭스</h2>
    <table><thead><tr><th style="width: 15%;">구분</th><th style="width: 25%;">지수 기준점</th><th style="width: 32%;">대상 주식 및 매수·매도 액션</th><th style="width: 28%;">핵심 전략 목표</th></tr></thead>
    <tbody><tr><td><span class="badge bg-buy">매수 전략</span><br><small style="color:#6c757d">하락 분할 매수</small></td><td class="trigger">-10% 하락 시<br>-15% 하락 시<br>-20% 하락 시<br>-25% 하락 시<br>-30% 이상 하락 시</td><td>가용 현금의 <span class="point">25% QQQ</span> 매수<br>가용 현금의 <span class="point">25% QQQ</span> 매수<br>가용 현금의 <span class="point">25% QLD</span> 매수<br>가용 현금의 <span class="point">25% QLD</span> 매수<br>신규 자금 발생 시 <span class="point">TQQQ / QLD</span> 추가 매수</td><td>잔파도 횡보장 레버리지 녹아내림 방어<br>1배수 단가 낮추기 및 장기 코어 자산 확보<br>약세장 진입 확인. 2배수 레버리지 시작<br>바닥권 단가 극대화 (수익비 최적화 타점)<br>파산 위험 없이 3배수로 평단가 바닥 고정</td></tr>
    <tr><td><span class="badge bg-sell-a">매도 전략 A</span><br><small style="color:#6c757d">QQQ만 매수 시</small></td><td class="trigger">전고점 +15% 도달 시<br>전고점 +20% 도달 시<br>전고점 +25% 도달 시</td><td>QQQ 물량 <span class="point">30%</span> 매도<br>QQQ 물량 <span class="point">30%</span> 매도<br>QQQ 물량 <span class="point">30%</span> 매도 <small>(나머지 10% 홀딩)</small></td><td>가벼운 조정(-10%~-15%) 후의 평균 상승치에서 확실하게 익절</td></tr>
    <tr><td><span class="badge bg-sell-b">매도 전략 B</span><br><small style="color:#6c757d">QLD 매수 시</small></td><td class="trigger">전고점 +20% 도달 시<br>전고점 +25% 도달 시<br>전고점 +30% 도달 시<br>전고점 +35% 도달 시<br>전고점 +40% 도달 시</td><td>QLD <span class="point">20%</span> 매도<br>QLD <span class="point">20%</span> 매도<br>QLD <span class="point">20%</span> 매도 / QQQ <span class="point">50%</span> 매도<br>QLD <span class="point">20%</span> 매도 / QQQ <span class="point">25%</span> 매도<br>QLD <span class="point">20%</span> 매도 / QQQ <span class="point">25%</span> 매도</td><td>약세장 극복 후 대세 상승장(+40%) 꼭지점까지 2배수 복리 수확</td></tr>
    <tr><td><span class="badge bg-sell-c">매도 전략 C</span><br><small style="color:#6c757d">TQQQ 매수 시</small></td><td class="trigger">전고점 +20% 도달 시<br>전고점 +30% 도달 시</td><td>TQQQ 물량 <span class="point">50%</span> 매도<br>TQQQ 물량 <span class="point">50%</span> 매도 <small>(전량 청산)</small></td><td>미완성 랠리 방어(+20%에서 원금 수십 배 확보) 후 +30% 홈런 졸업</td></tr>
    <tr><td><span class="badge bg-emergency">비상 탈출 룰</span><br><small style="color:#6c757d">장기 침체 대비</small></td><td class="trigger">매수 후 3년 이상 지나도<br>전고점 돌파 실패 시</td><td>바닥에서 산 QLD / TQQQ가<br><span style="color: var(--red); font-weight: bold;">+70% 수익 도달 시 전량 매도</span></td><td>닷컴버블급 암흑기에서도 3~4년 만에 복리 효과로 원금과 수익 챙겨 생존</td></tr></tbody></table>
    <div class="rules"><h3 style="margin:0 0 8px 0; color:var(--blue); font-size:15px;">📌 실전 매매 원칙 요약</h3><ul style="margin:0; padding-left:20px;"><li><strong>룰 스위칭 원칙:</strong> QLD가 1주라도 매수되는 순간(-20% 이탈), 매도 전략 A는 즉시 무효화되고 <strong>매도 전략 B</strong>로 상향 전환됩니다.</li><li><strong>3배수 독립 익절:</strong> TQQQ는 고점에서의 하강 속도가 매우 빠르므로 QLD보다 빠른 시점(+20%, +30%)에 <strong>매도 전략 C</strong>를 통해 독립적으로 졸업합니다.</li><li><strong>시간 방어 원칙:</strong> 3년 이상 전고점을 뚫지 못하는 장기 침체기에는 <strong>+70% 비상 탈출 룰</strong>을 최우선으로 가동하여 계좌를 지켜냅니다.</li></ul></div></div></body></html>"""

    # 서버 환경(헤드리스)에서는 브라우저 띄우기 명령어 제외, 파일만 저장
    with open("nasdaq_dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 자동화 스크립트 실행 및 파일 빌드 완료!")
