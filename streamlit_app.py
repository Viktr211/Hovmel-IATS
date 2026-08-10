# ============================================================
# HOVMEL — ЖИВОЙ ГРАФИК OKX (МИНИМАЛИЗМ)
# (c) 2024 HOVMEL Trading Systems
# ============================================================

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio
import websockets
import json
import threading
import time

st.set_page_config(
    page_title="HOVMEL - Live OKX Chart",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# ИНИЦИАЛИЗАЦИЯ
# ============================================================
if 'ohlcv' not in st.session_state:
    st.session_state.ohlcv = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
if 'current_price' not in st.session_state:
    st.session_state.current_price = 0
if 'bid' not in st.session_state:
    st.session_state.bid = 0
if 'ask' not in st.session_state:
    st.session_state.ask = 0
if 'running' not in st.session_state:
    st.session_state.running = False
if 'symbol' not in st.session_state:
    st.session_state.symbol = 'BTC/USDT'
if 'ws_running' not in st.session_state:
    st.session_state.ws_running = False

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']

# ============================================================
# ФУНКЦИЯ ОБНОВЛЕНИЯ СВЕЧЕЙ
# ============================================================
def update_candles(price, volume=0):
    now = datetime.now()
    minute = now.replace(second=0, microsecond=0)
    df = st.session_state.ohlcv
    if df.empty or df['timestamp'].iloc[-1] != minute:
        new = pd.DataFrame({
            'timestamp': [minute],
            'open': [price],
            'high': [price],
            'low': [price],
            'close': [price],
            'volume': [volume]
        })
        st.session_state.ohlcv = pd.concat([df, new], ignore_index=True)
        if len(st.session_state.ohlcv) > 300:
            st.session_state.ohlcv = st.session_state.ohlcv.iloc[-300:]
    else:
        idx = df.index[-1]
        st.session_state.ohlcv.at[idx, 'high'] = max(df.at[idx, 'high'], price)
        st.session_state.ohlcv.at[idx, 'low'] = min(df.at[idx, 'low'], price)
        st.session_state.ohlcv.at[idx, 'close'] = price
        st.session_state.ohlcv.at[idx, 'volume'] += volume

# ============================================================
# WEBSOCKET (trades + ticker)
# ============================================================
async def ws_handler():
    symbol = st.session_state.symbol.replace('/', '-')
    uri = "wss://ws.okx.com:8443/ws/v5/public"
    try:
        async with websockets.connect(uri) as ws:
            sub = {
                "op": "subscribe",
                "args": [
                    {"channel": "trades", "instId": symbol},
                    {"channel": "ticker", "instId": symbol}
                ]
            }
            await ws.send(json.dumps(sub))
            st.session_state.logs = "✅ Подключено к OKX"
            while st.session_state.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    if 'data' in data and len(data['data']) > 0:
                        for item in data['data']:
                            if 'ticker' in data.get('arg', {}).get('channel', ''):
                                st.session_state.bid = float(item.get('bidPx', 0))
                                st.session_state.ask = float(item.get('askPx', 0))
                            else:
                                p = float(item.get('px', 0))
                                v = float(item.get('sz', 0))
                                if p > 0:
                                    update_candles(p, v)
                                    st.session_state.current_price = p
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        st.session_state.logs = f"❌ Ошибка: {e}"
        st.session_state.ws_running = False

def start_ws():
    if not st.session_state.ws_running and st.session_state.running:
        st.session_state.ws_running = True
        def run():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.run_until_complete(ws_handler())
        threading.Thread(target=run, daemon=True).start()

# ============================================================
# CSS — МИНИМАЛЬНЫЙ
# ============================================================
st.markdown("""
<style>
    .main { background: #0d0d1a; padding: 0; }
    .header { 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        background: #1a1a2e;
        padding: 10px 20px;
        border-bottom: 1px solid #333;
        color: #eee;
        font-family: 'Segoe UI', sans-serif;
    }
    .symbol { font-size: 24px; font-weight: bold; color: #ffd700; }
    .price { font-size: 28px; color: #00ff88; }
    .bid { color: #00ff88; }
    .ask { color: #ff4444; }
    .btn { 
        background: #2a2a4e; 
        border: none; 
        color: #fff; 
        padding: 8px 24px; 
        border-radius: 6px; 
        cursor: pointer;
        font-weight: bold;
        font-size: 16px;
    }
    .btn-start { background: #00cc66; }
    .btn-stop { background: #ff4444; }
    .status { font-size: 14px; color: #aaa; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ШАПКА
# ============================================================
st.markdown(f"""
<div class="header">
    <div>
        <span class="symbol">{st.session_state.symbol}</span>
        <span style="margin-left: 20px; font-size: 18px; color: #888;">
            BID <span class="bid">{st.session_state.bid:.1f}</span> 
            ASK <span class="ask">{st.session_state.ask:.1f}</span>
        </span>
        <span style="margin-left: 20px; font-size: 18px; color: #ffd700;">
            Last: {st.session_state.current_price:.1f}
        </span>
    </div>
    <div>
        <select id="symbolSelect" onchange="window.location.href='?symbol='+this.value">
            {''.join([f'<option value="{s}" {"selected" if s==st.session_state.symbol else ""}>{s}</option>' for s in SYMBOLS])}
        </select>
        <button class="btn btn-start" onclick="startBot()">▶ Start</button>
        <button class="btn btn-stop" onclick="stopBot()">⏹ Stop</button>
        <span class="status">{'🟢 ONLINE' if st.session_state.running else '⏹ OFFLINE'}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ГРАФИК (на всю ширину)
# ============================================================
df = st.session_state.ohlcv.copy()
if df.empty:
    # Если данных нет — показываем заглушку
    df = pd.DataFrame({
        'timestamp': [datetime.now()],
        'open': [60000],
        'high': [60000],
        'low': [60000],
        'close': [60000],
        'volume': [0]
    })

fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                     row_heights=[0.8, 0.2], vertical_spacing=0.02)

fig.add_trace(go.Candlestick(
    x=df['timestamp'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='OKX',
    increasing_line_color='#00ff88',
    decreasing_line_color='#ff4444'
), row=1, col=1)

# SMA
if len(df) > 20:
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma20'], line=dict(color='#ffaa00', width=1), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma50'], line=dict(color='#4488ff', width=1), name='SMA 50'), row=1, col=1)

# Линии BID/ASK
if st.session_state.bid > 0:
    fig.add_hline(y=st.session_state.bid, line=dict(color='#00ff88', width=1, dash='dash'), annotation_text=f'BID {st.session_state.bid:.1f}', annotation_position='bottom right', row=1, col=1)
if st.session_state.ask > 0:
    fig.add_hline(y=st.session_state.ask, line=dict(color='#ff4444', width=1, dash='dash'), annotation_text=f'ASK {st.session_state.ask:.1f}', annotation_position='top left', row=1, col=1)

# Last
fig.add_hline(y=st.session_state.current_price, line=dict(color='#ffff00', width=1, dash='dot'), annotation_text=f'Last {st.session_state.current_price:.1f}', annotation_position='top right', row=1, col=1)

# Объём
fig.add_trace(go.Bar(x=df['timestamp'], y=df['volume'], name='Volume', marker_color='#4466aa', opacity=0.5), row=2, col=1)

fig.update_layout(
    template='plotly_dark',
    height=700,
    showlegend=False,
    paper_bgcolor='#0d0d1a',
    plot_bgcolor='#0d0d1a',
    margin=dict(l=0, r=0, t=0, b=0),
    xaxis_rangeslider_visible=False,
    hovermode='x unified'
)
fig.update_xaxes(gridcolor='#1a1a2e', showgrid=True)
fig.update_yaxes(gridcolor='#1a1a2e', showgrid=True)

st.plotly_chart(fig, use_container_width=True, key="chart")

# ============================================================
# ОБНОВЛЕНИЕ ГРАФИКА (автоматический рефреш)
# ============================================================
if st.session_state.running:
    time.sleep(0.2)
    st.rerun()

# ============================================================
# УПРАВЛЕНИЕ (через JavaScript)
# ============================================================
st.components.v1.html("""
<script>
function startBot() {
    fetch('/api/command', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({command: 'start'}) });
    location.reload();
}
function stopBot() {
    fetch('/api/command', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({command: 'stop'}) });
    location.reload();
}
</script>
""", height=0)

# ============================================================
# API ДЛЯ КОМАНД (через скрытый запрос)
# ============================================================
if st.query_params.get('command') == 'start':
    st.session_state.running = True
    start_ws()
    st.query_params.clear()
    st.rerun()
elif st.query_params.get('command') == 'stop':
    st.session_state.running = False
    st.session_state.ws_running = False
    st.query_params.clear()
    st.rerun()
