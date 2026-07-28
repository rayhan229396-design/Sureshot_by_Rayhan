import os
import pytz
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string, request
import pandas as pd
import numpy as np
import yfinance as yf

# Technical Indicators
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands, AverageTrueRange

app = Flask(__name__)

CURRENCY_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", 
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
    "BTCUSD", "ETHUSD", "XAUUSD"
]

YF_MAP = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X", "USDCAD": "CAD=X", "USDCHF": "CHF=X",
    "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X", "BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD", "XAUUSD": "GC=F"
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Institutional Precision Signal AI v3.0</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Orbitron:wght@600;800;900&family=Hind+Siliguri:wght@500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #070a11;
            --card-bg: #0f1623;
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-cyan: #00f2fe;
            --accent-blue: #4facfe;
            --green-glow: #00e676;
            --red-glow: #ff1744;
            --amber-glow: #ffab00;
            --text-main: #f1f5f9;
            --text-sub: #94a3b8;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Plus Jakarta Sans', 'Hind Siliguri', sans-serif; }
        
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px 12px;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(0, 242, 254, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(79, 172, 254, 0.05) 0%, transparent 40%);
        }

        .container {
            width: 100%;
            max-width: 480px;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 28px 22px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 242, 254, 0.05);
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }

        .container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00f2fe, #4facfe, #00e676);
        }

        .header {
            text-align: center;
            margin-bottom: 24px;
        }

        .badge-live {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(0, 230, 118, 0.1);
            border: 1px solid rgba(0, 230, 118, 0.3);
            color: var(--green-glow);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }

        .dot {
            width: 7px; height: 7px;
            background-color: var(--green-glow);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--green-glow);
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
        }

        .header h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 21px;
            font-weight: 900;
            background: linear-gradient(135deg, #ffffff 0%, #a1a1aa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
        }

        .header p {
            font-size: 12px;
            color: var(--text-sub);
            margin-top: 4px;
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-group label {
            display: block;
            font-size: 11px;
            font-weight: 700;
            color: var(--text-sub);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }

        .select-box {
            width: 100%;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            color: #fff;
            font-size: 15px;
            font-weight: 700;
            outline: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .select-box:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.2);
            background: rgba(255, 255, 255, 0.06);
        }

        .select-box option {
            background: #0f1623;
            color: #fff;
        }

        .btn-analyze {
            width: 100%;
            padding: 16px;
            margin-top: 10px;
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
            border: none;
            border-radius: 14px;
            color: #000;
            font-family: 'Orbitron', sans-serif;
            font-size: 15px;
            font-weight: 900;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(0, 242, 254, 0.3);
        }

        .btn-analyze:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(0, 242, 254, 0.45);
        }

        .loader {
            display: none;
            text-align: center;
            padding: 25px 0;
        }

        .spinner {
            width: 42px; height: 42px;
            border: 4px solid rgba(255, 255, 255, 0.05);
            border-top: 4px solid var(--accent-cyan);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .result-card {
            display: none;
            margin-top: 22px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 20px;
            animation: fadeIn 0.4s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .signal-box {
            text-align: center;
            padding: 18px;
            border-radius: 14px;
            margin-bottom: 18px;
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            letter-spacing: 1px;
            text-shadow: 0 0 10px currentColor;
        }

        .signal-call {
            background: rgba(0, 230, 118, 0.12);
            border: 2px solid var(--green-glow);
            color: var(--green-glow);
        }

        .signal-put {
            background: rgba(255, 23, 68, 0.12);
            border: 2px solid var(--red-glow);
            color: var(--red-glow);
        }

        .signal-wait {
            background: rgba(255, 171, 0, 0.12);
            border: 2px solid var(--amber-glow);
            color: var(--amber-glow);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 16px;
        }

        .metric-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 12px;
            border-radius: 12px;
            text-align: center;
        }

        .metric-label {
            font-size: 11px;
            color: var(--text-sub);
            font-weight: 600;
            margin-bottom: 4px;
            text-transform: uppercase;
        }

        .metric-value {
            font-size: 14px;
            font-weight: 800;
            color: #fff;
        }

        .accuracy-badge {
            display: inline-block;
            background: linear-gradient(135deg, #00f2fe, #4facfe);
            color: #000;
            padding: 2px 10px;
            border-radius: 20px;
            font-family: 'Orbitron', sans-serif;
            font-size: 13px;
            font-weight: 900;
        }

        .reason-card {
            background: rgba(0, 0, 0, 0.3);
            border-left: 3px solid var(--accent-cyan);
            border-radius: 10px;
            padding: 12px 14px;
            font-size: 12px;
            line-height: 1.6;
            color: #cbd5e1;
        }

        .footer-note {
            text-align: center;
            font-size: 11px;
            color: #475569;
            margin-top: 20px;
        }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <div class="badge-live"><span class="dot"></span> Institutional Filter v3.0</div>
        <h1>PRECISION SIGNAL AI</h1>
        <p>MTF Alignment, ATR Volatility & MACD Engine</p>
    </div>

    <div class="form-group">
        <label>ASSET PAIR (REAL MARKET)</label>
        <select id="pairSelect" class="select-box">
            {% for pair in pairs %}
                <option value="{{ pair }}">{{ pair }}</option>
            {% endfor %}
        </select>
    </div>

    <div class="form-group">
        <label>TIMEFRAME</label>
        <select id="tfSelect" class="select-box">
            <option value="1m">1 MINUTE (M1)</option>
            <option value="5m">5 MINUTES (M5)</option>
            <option value="15m">15 MINUTES (M15)</option>
        </select>
    </div>

    <button class="btn-analyze" onclick="getSignal()">ANALYZE SIGNAL</button>

    <div class="loader" id="loader">
        <div class="spinner"></div>
        <p style="font-size: 13px; color: var(--text-sub); margin-top: 12px; font-weight: 600;">
            ৫-লেয়ার টেকনিক্যাল ফিল্টার ফিল্টারিং হচ্ছে...
        </p>
    </div>

    <div class="result-card" id="resultCard">
        <div class="signal-box" id="signalBox">
            <div style="font-size: 18px;" id="signalText">CALL</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-label">এন্ট্রি টাইম (BD TIME)</div>
                <div class="metric-value" id="resTime">--:--:--</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">কনফিডেন্স স্কোর</div>
                <div class="metric-value"><span class="accuracy-badge" id="resScore">0%</span></div>
            </div>
            <div class="metric-box">
                <div class="metric-label">লাইভ প্রাইস</div>
                <div class="metric-value" id="resPrice" style="color: var(--accent-cyan);">--</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">M15 ট্রেন্ড ফিল্টার</div>
                <div class="metric-value" id="resMtf" style="font-size: 12px;">--</div>
            </div>
        </div>

        <div class="reason-card" id="resReason">
            বিশ্লেষণ বিস্তারিত...
        </div>
    </div>

    <div class="footer-note">
        Strict Execution: Min 85%+ Confluence Score Required
    </div>
</div>

<script>
    async function getSignal() {
        const pair = document.getElementById('pairSelect').value;
        const timeframe = document.getElementById('tfSelect').value;
        const loader = document.getElementById('loader');
        const resultCard = document.getElementById('resultCard');
        
        loader.style.display = 'block';
        resultCard.style.display = 'none';
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pair, timeframe })
            });
            
            const data = await response.json();
            loader.style.display = 'none';
            
            if(data.error) {
                alert('মার্কেট ডাটা এরর: ' + data.error);
                return;
            }
            
            resultCard.style.display = 'block';
            document.getElementById('resTime').innerText = data.entry_time;
            document.getElementById('resPrice').innerText = data.price;
            document.getElementById('resMtf').innerText = data.mtf_trend;
            document.getElementById('resScore').innerText = data.confidence + '%';
            document.getElementById('resReason').innerHTML = '<strong>💡 অ্যালগরিদম ফিল্টারিং রিপাবলিক:</strong><br>' + data.reason;
            
            const signalBox = document.getElementById('signalBox');
            const signalText = document.getElementById('signalText');
            
            if (data.direction === 'CALL') {
                signalBox.className = 'signal-box signal-call';
                signalText.innerText = '🟢 NEXT CANDLE: CALL (BUY)';
            } else if (data.direction === 'PUT') {
                signalBox.className = 'signal-box signal-put';
                signalText.innerText = '🔴 NEXT CANDLE: PUT (SELL)';
            } else {
                signalBox.className = 'signal-box signal-wait';
                signalText.innerText = '⚠️ NO TRADE / WAIT';
            }
        } catch (err) {
            alert('সার্ভার সাড়া দিচ্ছে না! লিঙ্কটি চেক করুন।');
            loader.style.display = 'none';
        }
    }
</script>

</body>
</html>"""

def perform_precision_analysis(symbol, timeframe):
    try:
        yf_symbol = YF_MAP.get(symbol, f"{symbol}=X")
        tf_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
        interval = tf_map.get(timeframe, "1m")
        period = "1d" if interval == "1m" else "5d"

        # 1. Primary Timeframe Data
        df = yf.download(tickers=yf_symbol, period=period, interval=interval, progress=False)
        if df.empty or len(df) < 50:
            return {"error": "যথেষ্ট ক্যান্ডেলস্টিক ডাটা পাওয়া যায়নি।"}

        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(yf_symbol, axis=1, level=1)
        df = df.dropna()

        # 2. Higher Timeframe (M15) Data for MTF Alignment
        df_htf = yf.download(tickers=yf_symbol, period="5d", interval="15m", progress=False)
        if isinstance(df_htf.columns, pd.MultiIndex):
            df_htf = df_htf.xs(yf_symbol, axis=1, level=1)
        df_htf = df_htf.dropna()

        htf_ema20 = EMAIndicator(close=df_htf['Close'], window=20).ema_indicator().iloc[-1]
        htf_ema50 = EMAIndicator(close=df_htf['Close'], window=50).ema_indicator().iloc[-1]
        htf_trend = "BULLISH (UP)" if htf_ema20 > htf_ema50 else "BEARISH (DOWN)"

        # 3. Indicator Calculations (Primary TF)
        rsi = RSIIndicator(close=df['Close'], window=14).rsi().iloc[-1]
        ema20 = EMAIndicator(close=df['Close'], window=20).ema_indicator().iloc[-1]
        ema50 = EMAIndicator(close=df['Close'], window=50).ema_indicator().iloc[-1]
        bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
        
        macd = MACD(close=df['Close'])
        macd_diff = macd.macd_diff().iloc[-1] # Histogram
        
        stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'])
        stoch_k = stoch.stoch().iloc[-1]

        atr = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=14).average_true_range().iloc[-1]

        curr_open = float(df['Open'].iloc[-1])
        curr_high = float(df['High'].iloc[-1])
        curr_low = float(df['Low'].iloc[-1])
        curr_close = float(df['Close'].iloc[-1])
        
        prev_open = float(df['Open'].iloc[-2])
        prev_close = float(df['Close'].iloc[-2])

        # Candle Volatility Check (Filter out dead/flat market)
        candle_range = curr_high - curr_low
        if candle_range < (0.35 * atr):
            return {
                "pair": symbol, "timeframe": timeframe, "price": round(curr_close, 5),
                "entry_time": "--", "direction": "WAIT", "confidence": 0,
                "mtf_trend": htf_trend,
                "reason": "মার্কেট অত্যন্ত মন্থর/সাইডওয়েজ (Low ATR Volatility)। ভুয়া সিগন্যাল এড়াতে ট্রেড বন্ধ রাখা হলো।"
            }

        # S/R Swing Levels
        recent_high = float(df['High'].iloc[-50:-1].max())
        recent_low = float(df['Low'].iloc[-50:-1].min())
        near_support = abs(curr_close - recent_low) / recent_low < 0.0018
        near_resistance = abs(curr_close - recent_high) / recent_high < 0.0018

        # Candlestick Patterns
        body_size = abs(curr_close - curr_open)
        upper_wick = curr_high - max(curr_open, curr_close)
        lower_wick = min(curr_open, curr_close) - curr_low

        is_bull_engulfing = (curr_close > curr_open) and (prev_close < prev_open) and (curr_close > prev_open)
        is_bear_engulfing = (curr_close < curr_open) and (prev_close > prev_open) and (curr_close < prev_open)
        is_hammer = (lower_wick > 2.2 * body_size) and (upper_wick < body_size)
        is_star = (upper_wick > 2.2 * body_size) and (lower_wick < body_size)

        call_score = 0
        put_score = 0
        reasons = []

        # Rule A: MTF Alignment (25 Pts)
        if htf_trend == "BULLISH (UP)":
            call_score += 25
            reasons.append("Higher Timeframe (M15) আপট্রেন্ডে রয়েছে")
        else:
            put_score += 25
            reasons.append("Higher Timeframe (M15) ডাউনট্রেন্ডে রয়েছে")

        # Rule B: Trend & MACD Momentum (25 Pts)
        if ema20 > ema50 and macd_diff > 0:
            call_score += 25
            reasons.append("EMA 20/50 & MACD মোমেন্টাম পজিটিভ")
        elif ema20 < ema50 and macd_diff < 0:
            put_score += 25
            reasons.append("EMA 20/50 & MACD মোমেন্টাম নেগেটিভ")

        # Rule C: Support/Resistance (20 Pts)
        if near_support:
            call_score += 20
            reasons.append("মেজর সাপোর্ট লেভেল রিজেকশন (Swing Low)")
        if near_resistance:
            put_score += 20
            reasons.append("মেজর রেজিস্ট্যান্স লেভেল রিজেকশন (Swing High)")

        # Rule D: Reversal Patterns (20 Pts)
        if is_bull_engulfing or is_hammer:
            call_score += 20
            reasons.append("বুলিশ রিভার্সাল ক্যান্ডেলস্টিক স্ট্রাকচার")
        if is_bear_engulfing or is_star:
            put_score += 20
            reasons.append("বেয়ারিশ রিভার্সাল ক্যান্ডেলস্টিক স্ট্রাকচার")

        # Rule E: RSI & Stochastic Confluence (10 Pts)
        if rsi < 38 and stoch_k < 25:
            call_score += 10
            reasons.append("RSI & Stochastic উভয়ই ডাবল ওভারসোল্ড জোন")
        elif rsi > 62 and stoch_k > 75:
            put_score += 10
            reasons.append("RSI & Stochastic উভয়ই ডাবল ওভারবট জোন")

        # Final Strict Decision Execution
        if call_score >= 80 and call_score > put_score:
            direction = "CALL"
            confidence = min(call_score + 10, 97)
            final_reason = " • ".join(reasons)
        elif put_score >= 80 and put_score > call_score:
            direction = "PUT"
            confidence = min(put_score + 10, 97)
            final_reason = " • ".join(reasons)
        else:
            direction = "WAIT"
            confidence = max(call_score, put_score)
            final_reason = "মার্কেটে ৮০%+ কনফ্লুয়েন্স পারফেকশন পাওয়া যায়নি। লস এড়াতে ট্রেড বন্ধ রাখা হলো।"

        bd_tz = pytz.timezone('Asia/Dhaka')
        now = datetime.now(bd_tz)
        tf_mins = 1 if timeframe == "1m" else (5 if timeframe == "5m" else 15)
        next_candle_time = (now + timedelta(minutes=tf_mins)).replace(second=0, microsecond=0)

        return {
            "pair": symbol,
            "timeframe": timeframe,
            "price": round(curr_close, 5),
            "entry_time": next_candle_time.strftime("%H:%M:%S"),
            "direction": direction,
            "confidence": confidence,
            "mtf_trend": htf_trend,
            "reason": final_reason
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, pairs=CURRENCY_PAIRS)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True) or {}
    pair = data.get('pair', 'EURUSD')
    timeframe = data.get('timeframe', '1m')
    result = perform_precision_analysis(pair, timeframe)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
