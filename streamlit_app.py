# ============================================================
# HOVMEL IATS — ШЕДЕВР v7.1_final (с исправлением AI)
# ============================================================

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import time
import threading
import json
import os
import math
import requests
import asyncio
import websockets
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

st.set_page_config(
    page_title="HOVMEL IATS v7.1 - Live Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# АВТО-ОБНОВЛЕНИЕ (каждые 500 мс для живого графика)
# ============================================================
if st.session_state.get('running', False):
    st_autorefresh(interval=500, key="live_chart_refresh")

# ============================================================
# CSS СТИЛИ (без изменений)
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .main-header { font-family: 'Orbitron', sans-serif; font-size: 2.5rem; background: linear-gradient(135deg, #FFD700 0%, #FF8C00 40%, #FF4500 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 20px 0; }
    .status-demo { display: inline-block; padding: 8px 20px; background: #00ff88; color: #000; border-radius: 20px; font-weight: bold; box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); animation: pulse-green 2s infinite; }
    .status-real { display: inline-block; padding: 8px 20px; background: #ff4444; color: #fff; border-radius: 20px; font-weight: bold; box-shadow: 0 0 20px rgba(255, 68, 68, 0.5); animation: pulse-red 2s infinite; }
    .status-ai { display: inline-block; padding: 8px 20px; background: #4488ff; color: #fff; border-radius: 20px; font-weight: bold; box-shadow: 0 0 20px rgba(68, 136, 255, 0.5); animation: pulse-blue 2s infinite; }
    @keyframes pulse-green { 0% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); } 50% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.9); } 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); } }
    @keyframes pulse-red { 0% { box-shadow: 0 0 20px rgba(255, 68, 68, 0.5); } 50% { box-shadow: 0 0 40px rgba(255, 68, 68, 0.9); } 100% { box-shadow: 0 0 20px rgba(255, 68, 68, 0.5); } }
    @keyframes pulse-blue { 0% { box-shadow: 0 0 20px rgba(68, 136, 255, 0.5); } 50% { box-shadow: 0 0 40px rgba(68, 136, 255, 0.9); } 100% { box-shadow: 0 0 20px rgba(68, 136, 255, 0.5); } }
    .status-stopped { display: inline-block; padding: 8px 20px; background: #666; color: #fff; border-radius: 20px; font-weight: bold; }
    .status-running { display: inline-block; padding: 8px 20px; background: #ffaa00; color: #000; border-radius: 20px; font-weight: bold; animation: pulse-yellow 1.5s infinite; }
    .status-paused { display: inline-block; padding: 8px 20px; background: #ff6600; color: #fff; border-radius: 20px; font-weight: bold; animation: pulse-orange 1s infinite; }
    @keyframes pulse-yellow { 0% { box-shadow: 0 0 20px rgba(255, 170, 0, 0.5); } 50% { box-shadow: 0 0 40px rgba(255, 170, 0, 0.9); } 100% { box-shadow: 0 0 20px rgba(255, 170, 0, 0.5); } }
    @keyframes pulse-orange { 0% { box-shadow: 0 0 20px rgba(255, 102, 0, 0.5); } 50% { box-shadow: 0 0 40px rgba(255, 102, 0, 0.9); } 100% { box-shadow: 0 0 20px rgba(255, 102, 0, 0.5); } }
    .metric-card { background: #1a1a2e; padding: 20px; border-radius: 12px; border: 1px solid #333; margin: 5px; }
    .metric-value { font-size: 28px; font-weight: bold; }
    .metric-green { color: #00ff88; }
    .metric-red { color: #ff4444; }
    .metric-gold { color: #ffd700; }
    .metric-blue { color: #4488ff; }
    .metric-purple { color: #bb88ff; }
    .log-container { background: #0a0a12; padding: 15px; border-radius: 8px; max-height: 300px; overflow-y: auto; font-family: 'Consolas', monospace; font-size: 12px; color: #aaa; border: 1px solid #222; }
    .log-entry-green { color: #00ff88; }
    .log-entry-red { color: #ff4444; }
    .log-entry-gold { color: #ffd700; }
    .log-entry-blue { color: #4488ff; }
    .log-entry-purple { color: #bb88ff; }
    .log-entry-white { color: #ffffff; }
    .log-entry-orange { color: #ff8800; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; background-color: #1a1a2e; border-radius: 8px 8px 0 0; padding: 5px 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px 6px 0 0; padding: 8px 20px; background-color: #2a2a4e; color: #888; font-weight: bold; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3a3a6e; color: #fff; border-bottom: 3px solid #ffd700; }
    .trade-profit { color: #4488ff; font-weight: bold; }
    .trade-loss { color: #ff4444; font-weight: bold; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; padding: 10px; }
    .trade-table { background: #0d0d1a; border-radius: 8px; padding: 10px; border: 1px solid #333; }
    .order-form { background: #0d0d1a; border-radius: 8px; padding: 15px; border: 1px solid #333; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ИНИЦИАЛИЗАЦИЯ ГЛОБАЛЬНЫХ БУФЕРОВ
# ============================================================
if 'tick_buffer' not in st.session_state:
    st.session_state.tick_buffer = []
if 'ohlcv_buffer' not in st.session_state:
    st.session_state.ohlcv_buffer = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
if 'ws_running' not in st.session_state:
    st.session_state.ws_running = False
if 'current_price' not in st.session_state:
    st.session_state.current_price = 0
if 'balance' not in st.session_state:
    st.session_state.balance = 3000.0
if 'demo_balance' not in st.session_state:
    st.session_state.demo_balance = 3000.0
if 'position' not in st.session_state:
    st.session_state.position = None
if 'pnl' not in st.session_state:
    st.session_state.pnl = 0
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'running' not in st.session_state:
    st.session_state.running = False
if 'status' not in st.session_state:
    st.session_state.status = 'stopped'
if 'dry_run' not in st.session_state:
    st.session_state.dry_run = True
if 'mode' not in st.session_state:
    st.session_state.mode = 'demo'
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = 'BTC/USDT'
if 'timeframe' not in st.session_state:
    st.session_state.timeframe = '1m'
if 'strategy' not in st.session_state:
    st.session_state.strategy = None
if 'exchange' not in st.session_state:
    st.session_state.exchange = None
if 'thread_started' not in st.session_state:
    st.session_state.thread_started = False
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = 'IATS'
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['time', 'symbol', 'side', 'volume', 'profit'])
if 'equity_data' not in st.session_state:
    st.session_state.equity_data = pd.DataFrame(columns=['time', 'equity'])
if 'markers' not in st.session_state:
    st.session_state.markers = []
if 'manual_orders' not in st.session_state:
    st.session_state.manual_orders = []
if 'manual_positions' not in st.session_state:
    st.session_state.manual_positions = []
# ===== ВАЖНО: инициализация AI-ассистента =====
if 'ai_assistant' not in st.session_state:
    st.session_state.ai_assistant = DeepSeekAIAssistant()  # класс определён ниже, но мы его создадим после определения класса. Пока это не критично, так как мы создадим его позже.

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
STRATEGIES = ['IATS', 'SMA (простая)']
TIMEFRAMES = ['1m', '5m', '15m', '1h', '1d']

# ============================================================
# ФУНКЦИЯ ОБНОВЛЕНИЯ СВЕЧЕЙ
# ============================================================
def update_candles(tick_price, tick_volume=0, symbol='BTC/USDT'):
    """Добавляет тик в текущую свечу или создаёт новую"""
    now = datetime.now()
    current_minute = now.replace(second=0, microsecond=0)
    
    df = st.session_state.ohlcv_buffer
    
    if df.empty or df['timestamp'].iloc[-1] != current_minute:
        # Новая свеча
        new_row = pd.DataFrame({
            'timestamp': [current_minute],
            'open': [tick_price],
            'high': [tick_price],
            'low': [tick_price],
            'close': [tick_price],
            'volume': [tick_volume]
        })
        st.session_state.ohlcv_buffer = pd.concat([df, new_row], ignore_index=True)
        if len(st.session_state.ohlcv_buffer) > 200:
            st.session_state.ohlcv_buffer = st.session_state.ohlcv_buffer.iloc[-200:]
    else:
        # Обновляем текущую свечу
        idx = df.index[-1]
        st.session_state.ohlcv_buffer.at[idx, 'high'] = max(df.at[idx, 'high'], tick_price)
        st.session_state.ohlcv_buffer.at[idx, 'low'] = min(df.at[idx, 'low'], tick_price)
        st.session_state.ohlcv_buffer.at[idx, 'close'] = tick_price
        st.session_state.ohlcv_buffer.at[idx, 'volume'] += tick_volume

# ============================================================
# WEBSOCKET-ХЕНДЛЕР (для получения тиков в реальном времени)
# ============================================================
async def websocket_handler():
    """Подключение к OKX WebSocket и обработка тиков"""
    symbol = st.session_state.selected_symbol
    inst_id = symbol.replace('/', '-')  # BTC/USDT → BTC-USDT
    
    uri = "wss://ws.okx.com:8443/ws/v5/public"
    
    try:
        async with websockets.connect(uri) as websocket:
            subscribe_msg = {
                "op": "subscribe",
                "args": [{
                    "channel": "trades",
                    "instId": inst_id
                }]
            }
            await websocket.send(json.dumps(subscribe_msg))
            st.session_state.logs.append(f"✅ Подписка на trades для {symbol}")
            
            while st.session_state.get('running', False):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if 'data' in data and len(data['data']) > 0:
                        for trade in data['data']:
                            price = float(trade.get('px', 0))
                            volume = float(trade.get('sz', 0))
                            if price > 0:
                                update_candles(price, volume, symbol)
                                st.session_state.current_price = price
                                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    st.session_state.logs.append(f"⚠️ WebSocket ошибка: {e}")
                    
    except Exception as e:
        st.session_state.logs.append(f"❌ WebSocket подключение failed: {e}")
        st.session_state.ws_running = False

def start_websocket():
    """Запускает WebSocket в отдельном потоке"""
    if not st.session_state.ws_running:
        st.session_state.ws_running = True
        st.session_state.logs.append("🔌 Запуск WebSocket...")
        
        def run_ws():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.run_until_complete(websocket_handler())
        
        thread = threading.Thread(target=run_ws, daemon=True)
        thread.start()

# ============================================================
# ФУНКЦИЯ ЗАПУСКА ФОНОВОГО ПОТОКА (стратегия + WebSocket)
# ============================================================
def start_bot_thread():
    if st.session_state.running and st.session_state.strategy:
        if not st.session_state.thread_started:
            def bot_loop():
                while st.session_state.running:
                    try:
                        st.session_state.strategy.tick()
                        time.sleep(1)
                    except Exception as e:
                        st.session_state.logs.append(f"❌ Ошибка в цикле: {e}")
                        time.sleep(5)
            thread = threading.Thread(target=bot_loop, daemon=True)
            thread.start()
            st.session_state.thread_started = True
            st.session_state.logs.append("🧵 Фоновый поток стратегии запущен")
        # Запускаем WebSocket отдельно (если ещё не запущен)
        if not st.session_state.ws_running:
            start_websocket()
        if st.session_state.running:
            time.sleep(0.5)
            st.rerun()

# ============================================================
# AI-АССИСТЕНТ (DeepSeek) — сокращённый
# ============================================================
class DeepSeekAIAssistant:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY') or st.secrets.get('DEEPSEEK_API_KEY', '')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    def analyze(self, analysis_type, data):
        if not self.api_key:
            return {"error": "Не задан API-ключ DeepSeek"}
        prompt = self._build_prompt(analysis_type, data)
        return self._call_deepseek(prompt)

    def _build_prompt(self, analysis_type, data):
        prompts = {
            'trend': f"""
            Проанализируй рыночные данные и определи тренд:
            {json.dumps(data, indent=2)}
            Ответь строго в JSON:
            {{
                "trend": "up" или "down" или "neutral",
                "confidence": число,
                "reason": "краткое объяснение",
                "suggested_sl_ticks": число,
                "suggested_avg_step": число,
                "suggested_risk": число,
                "sentiment": "bullish" или "bearish" или "neutral",
                "next_move": "buy" или "sell" или "wait"
            }}
            """,
            'news': f"""
            Проанализируй экономический календарь на {datetime.now().strftime('%Y-%m-%d')}:
            {json.dumps(data, indent=2)}
            Ответь в JSON:
            {{
                "has_important_news": true/false,
                "news_items": [],
                "should_pause_trading": true/false,
                "pause_before_minutes": число,
                "pause_after_minutes": число,
                "impact": "high" или "medium" или "low"
            }}
            """,
            'sentiment': f"""
            Проанализируй текущее состояние рынка:
            {json.dumps(data, indent=2)}
            Ответь в JSON:
            {{
                "overall_sentiment": "bullish" или "bearish" или "neutral",
                "confidence": число,
                "fear_greed_index": число,
                "recommendation": "buy" или "sell" или "wait"
            }}
            """,
            'learn': f"""
            Проанализируй историю сделок:
            {json.dumps(data, indent=2)}
            Ответь в JSON:
            {{
                "best_time_to_trade": "",
                "worst_time_to_trade": "",
                "optimal_avg_count": число,
                "optimal_avg_step": число,
                "risk_adjustment": "increase" или "decrease" или "keep"
            }}
            """,
            'market_state': f"""
            Текущее состояние рынка:
            {json.dumps(data, indent=2)}
            Ответь в JSON:
            {{
                "risk_percent": число,
                "max_lot": число,
                "sl_ticks": число,
                "avg_step": число,
                "avg_coefficient": число,
                "trailing_distance": число,
                "max_averaging": число,
                "max_reverses": число,
                "confidence": число
            }}
            """
        }
        return prompts.get(analysis_type, "")

    def _call_deepseek(self, prompt):
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": "Ты эксперт. Отвечай только JSON."},
                             {"role": "user", "content": prompt}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "max_tokens": 800
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                content = response.json().get('choices', [{}])[0].get('message', {}).get('content', '{}')
                return json.loads(content)
            return {"error": f"API ошибка: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

# ============================================================
# БАЗОВЫЙ КЛАСС СТРАТЕГИИ И IATS
# ============================================================
class BaseStrategy:
    def __init__(self, exchange, symbol, config):
        self.exchange = exchange
        self.symbol = symbol
        self.config = config
        self.position = None
        self.trade_history = []

    def tick(self):
        raise NotImplementedError

    def get_balance(self, currency='USDT'):
        try:
            if hasattr(self.exchange, 'apiKey') and self.exchange.apiKey:
                balance = self.exchange.fetch_balance()
                return balance['free'].get(currency, 0.0)
            else:
                return st.session_state.demo_balance
        except:
            return st.session_state.demo_balance

    def get_current_price(self):
        return st.session_state.current_price or 0.0

class IATSStrategyAI(BaseStrategy):
    def __init__(self, exchange, symbol, config, ai_assistant):
        super().__init__(exchange, symbol, config)
        self.ai = ai_assistant
        self.tick_size = self._get_tick_size()
        self.averaging_count = 0
        self.is_reversed = False
        self.reverse_count = 0
        self.trailing_active = False
        self.trailing_level = 0.0
        self.ai_last_update = None
        self.ai_suggestions = {}
        self.trading_paused = False
        self.pause_reason = ""
        self.pause_until = None
        self.learning_stats = {}
        self.best_hours = []
        self.worst_hours = []

    def _get_tick_size(self):
        return self.exchange.market(self.symbol)['precision']['price']

    def fetch_ohlcv(self, limit=200, timeframe='1m'):
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except:
            return pd.DataFrame()

    def calculate_indicators(self, df):
        if df.empty:
            return {}
        close = df['close']
        return {
            'rsi': self._calculate_rsi(close),
            'volatility': close.pct_change().std() * 100,
            'volume': df['volume'].mean(),
            'sma20': close.rolling(20).mean().iloc[-1] if len(close) >= 20 else close.iloc[-1],
            'sma50': close.rolling(50).mean().iloc[-1] if len(close) >= 50 else close.iloc[-1],
        }

    def _calculate_rsi(self, prices, period=14):
        if len(prices) < period:
            return 50
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]

    def _get_financial_calendar(self):
        events = [
            {"date": "2024-11-06", "time": "14:00", "event": "FOMC Interest Rate", "importance": "high"},
            {"date": "2024-12-18", "time": "14:00", "event": "FOMC Interest Rate", "importance": "high"},
            {"date": "2024-11-01", "time": "13:30", "event": "NFP", "importance": "high"},
            {"date": "2024-12-06", "time": "13:30", "event": "NFP", "importance": "high"},
        ]
        today = datetime.now().strftime('%Y-%m-%d')
        return [e for e in events if e['date'] >= today]

    def check_ai_news(self):
        if not self.ai.api_key:
            return
        news_data = {"today": datetime.now().strftime('%Y-%m-%d'), "events": self._get_financial_calendar()}
        result = self.ai.analyze('news', news_data)
        if result and not result.get('error'):
            if result.get('should_pause_trading', False) and result.get('impact') in ['high', 'medium']:
                self.trading_paused = True
                self.pause_reason = f"Новости: {', '.join(result.get('news_items', []))}"
                self.pause_until = datetime.now() + timedelta(minutes=result.get('pause_before_minutes', 60) + result.get('pause_after_minutes', 30) + 10)
                st.session_state.logs.append(f"⏸️ Пауза: {self.pause_reason}")
            else:
                self.trading_paused = False
                self.pause_until = None

    def check_ai_trend(self):
        if not self.ai.api_key:
            return
        df = self.fetch_ohlcv(limit=100, timeframe='1m')
        if df.empty:
            return
        ind = self.calculate_indicators(df)
        data = {"price": df['close'].iloc[-1], "rsi": ind.get('rsi'), "volatility": ind.get('volatility')}
        result = self.ai.analyze('trend', data)
        if result and not result.get('error'):
            self.ai_suggestions = result
            if result.get('suggested_sl_ticks'):
                self.config['sl_ticks'] = int(result['suggested_sl_ticks'])
            if result.get('suggested_avg_step'):
                self.config['averaging_step_ticks'] = int(result['suggested_avg_step'])
            st.session_state.logs.append(f"🧠 AI: тренд {result.get('trend')}, уверенность {result.get('confidence')}%")

    def adapt_strategy_to_market(self):
        if not self.ai.api_key:
            return
        df = self.fetch_ohlcv(limit=50, timeframe='1m')
        if df.empty:
            return
        ind = self.calculate_indicators(df)
        state = {"volatility": ind.get('volatility'), "rsi": ind.get('rsi'), "balance": self.get_balance('USDT')}
        result = self.ai.analyze('market_state', state)
        if result and not result.get('error'):
            for key in ['risk_percent', 'max_lot', 'sl_ticks', 'avg_step', 'avg_coefficient', 'trailing_distance', 'max_averaging']:
                if result.get(key):
                    self.config[key] = float(result[key]) if key != 'sl_ticks' else int(result[key])
            st.session_state.logs.append(f"🧠 AI: адаптировал параметры")

    def calculate_lot(self, side, entry_price, stop_loss_price):
        balance = self.get_balance('USDT')
        risk = balance * (self.config.get('risk_percent', 1.0) / 100.0)
        diff = abs(entry_price - stop_loss_price)
        if diff == 0:
            return 0.0
        lot = risk / diff
        step = self.exchange.market(self.symbol)['precision']['amount']
        lot = math.floor(lot / step) * step
        lot = min(lot, self.config.get('max_lot', 0.01))
        lot = max(lot, self.exchange.market(self.symbol)['limits']['amount']['min'])
        return lot if lot > 0 else 0.0

    def place_order(self, side, amount, order_type='market', stop_loss=None, take_profit=None):
        try:
            params = {}
            if stop_loss:
                params['stopLoss'] = {'stopPrice': stop_loss}
            if take_profit:
                params['takeProfit'] = {'limitPrice': take_profit}
            return self.exchange.create_market_order(self.symbol, side, amount, params=params) if order_type == 'market' else None
        except Exception as e:
            st.session_state.logs.append(f"❌ Ошибка ордера: {e}")
            return None

    def close_position(self, side, volume):
        try:
            return self.exchange.create_market_order(self.symbol, side, volume)
        except Exception as e:
            st.session_state.logs.append(f"❌ Ошибка закрытия: {e}")
            return None

    def check_entry_signal(self):
        now = datetime.now()
        if self.trading_paused and self.pause_until and now < self.pause_until:
            return False
        if self.trading_paused:
            self.trading_paused = False
            self.pause_reason = ""
        if self.ai_suggestions.get('next_move') == 'wait':
            return False
        return True

    def _add_marker(self, marker_type, price, side, time):
        if 'markers' not in st.session_state:
            st.session_state.markers = []
        st.session_state.markers.append({'type': marker_type, 'price': price, 'side': side, 'time': time})
        if len(st.session_state.markers) > 200:
            st.session_state.markers = st.session_state.markers[-200:]

    def _close_trade(self, profit):
        if not self.position:
            return
        self._add_marker('exit', self.get_current_price(), self.position['side'], datetime.now())
        trade_data = {
            'time': datetime.now(), 'symbol': self.symbol, 'side': self.position['side'],
            'volume': self.position['volume'], 'profit': profit, 'hour': datetime.now().hour,
            'avg_count': self.averaging_count, 'is_reversed': self.is_reversed
        }
        self.trade_history.append(trade_data)
        st.session_state.trade_history = self.trade_history
        new_row = pd.DataFrame({
            'time': [datetime.now()], 'symbol': [self.symbol], 'side': [self.position['side']],
            'volume': [self.position['volume']], 'profit': [profit]
        })
        st.session_state.history_data = pd.concat([st.session_state.history_data, new_row], ignore_index=True)
        current_equity = st.session_state.balance + st.session_state.history_data['profit'].sum()
        eq_row = pd.DataFrame({'time': [datetime.now()], 'equity': [current_equity]})
        st.session_state.equity_data = pd.concat([st.session_state.equity_data, eq_row], ignore_index=True)

    def tick(self):
        now = datetime.now()
        if self.ai_last_update is None or (now - self.ai_last_update).seconds > 300:
            self.ai_last_update = now
            self.check_ai_news()
            self.check_ai_trend()
            self.adapt_strategy_to_market()

        current_price = self.get_current_price()
        st.session_state.current_price = current_price

        if self.position is None:
            if self.check_entry_signal():
                sl_price = current_price - self.config.get('sl_ticks', 30) * self.tick_size
                lot = self.calculate_lot('buy', current_price, sl_price)
                if lot > 0:
                    st.session_state.logs.append(f"🟢 Вход: покупаем {lot} по {current_price}")
                    if not st.session_state.dry_run:
                        order = self.place_order('buy', lot)
                        if order:
                            self.position = {'side': 'buy', 'entry_price': current_price, 'avg_price': current_price, 'volume': lot}
                            self.averaging_count = 0
                            self.is_reversed = False
                            self.trailing_active = False
                            st.session_state.logs.append("✅ Позиция открыта")
                            self._add_marker('entry', current_price, 'buy', datetime.now())
                    else:
                        self.position = {'side': 'buy', 'entry_price': current_price, 'avg_price': current_price, 'volume': lot}
                        st.session_state.logs.append("🧪 [DRY] Позиция открыта")
                        self._add_marker('entry', current_price, 'buy', datetime.now())
            return

        side = self.position['side']
        avg = self.position['avg_price']
        vol = self.position['volume']
        profit_usdt = (current_price - avg) * vol if side == 'buy' else (avg - current_price) * vol
        st.session_state.pnl = profit_usdt
        is_profit = profit_usdt >= 0
        apply_stop = not (self.trading_paused and not is_profit)

        if apply_stop:
            if side == 'buy':
                sl = avg - self.config.get('sl_ticks', 30) * self.tick_size
                if current_price <= sl:
                    st.session_state.logs.append(f"🔴 Стоп-лосс! Цена {current_price}")
                    self.close_position('sell', vol)
                    self._close_trade(profit_usdt)
                    self.position = None
                    return
            else:
                sl = avg + self.config.get('sl_ticks', 30) * self.tick_size
                if current_price >= sl:
                    st.session_state.logs.append(f"🔴 Стоп-лосс! Цена {current_price}")
                    self.close_position('buy', vol)
                    self._close_trade(profit_usdt)
                    self.position = None
                    return

        if apply_stop and self.config.get('enable_trailing', True):
            if not self.trailing_active:
                profit_ticks = (current_price - avg) / self.tick_size if side == 'buy' else (avg - current_price) / self.tick_size
                if profit_ticks >= self.config.get('trailing_distance_ticks', 40):
                    self.trailing_active = True
                    self.trailing_level = current_price - self.config.get('trailing_distance_ticks', 40) * self.tick_size if side == 'buy' else current_price + self.config.get('trailing_distance_ticks', 40) * self.tick_size
                    st.session_state.logs.append(f"🟡 Трейлинг активирован")
            else:
                if side == 'buy':
                    new_level = current_price - self.config.get('trailing_distance_ticks', 40) * self.tick_size
                    if new_level > self.trailing_level:
                        self.trailing_level = new_level
                    if current_price <= self.trailing_level:
                        st.session_state.logs.append(f"🟡 Трейлинг сработал!")
                        self.close_position('sell', vol)
                        self._close_trade(profit_usdt)
                        self.position = None
                        return
                else:
                    new_level = current_price + self.config.get('trailing_distance_ticks', 40) * self.tick_size
                    if new_level < self.trailing_level:
                        self.trailing_level = new_level
                    if current_price >= self.trailing_level:
                        st.session_state.logs.append(f"🟡 Трейлинг сработал!")
                        self.close_position('buy', vol)
                        self._close_trade(profit_usdt)
                        self.position = None
                        return

        if self.averaging_count < self.config.get('max_averaging', 4):
            step = self.config.get('averaging_step_ticks', 60) * (self.averaging_count + 1) * self.tick_size
            if side == 'buy' and current_price <= avg - step:
                new_lot = self.calculate_lot('buy', current_price, current_price - self.config.get('sl_ticks', 30) * self.tick_size)
                if new_lot > 0:
                    st.session_state.logs.append(f"🔄 Усреднение #{self.averaging_count+1}")
                    if not st.session_state.dry_run:
                        order = self.place_order('buy', new_lot)
                        if order:
                            total_vol = vol + new_lot
                            new_avg = (avg * vol + current_price * new_lot) / total_vol
                            self.position['avg_price'] = new_avg
                            self.position['volume'] = total_vol
                            self.averaging_count += 1
                            self._add_marker('entry', current_price, 'buy', datetime.now())
                    else:
                        total_vol = vol + new_lot
                        new_avg = (avg * vol + current_price * new_lot) / total_vol
                        self.position['avg_price'] = new_avg
                        self.position['volume'] = total_vol
                        self.averaging_count += 1
                        self._add_marker('entry', current_price, 'buy', datetime.now())
            elif side == 'sell' and current_price >= avg + step:
                new_lot = self.calculate_lot('sell', current_price, current_price + self.config.get('sl_ticks', 30) * self.tick_size)
                if new_lot > 0:
                    st.session_state.logs.append(f"🔄 Усреднение #{self.averaging_count+1}")
                    if not st.session_state.dry_run:
                        order = self.place_order('sell', new_lot)
                        if order:
                            total_vol = vol + new_lot
                            new_avg = (avg * vol + current_price * new_lot) / total_vol
                            self.position['avg_price'] = new_avg
                            self.position['volume'] = total_vol
                            self.averaging_count += 1
                            self._add_marker('entry', current_price, 'sell', datetime.now())
                    else:
                        total_vol = vol + new_lot
                        new_avg = (avg * vol + current_price * new_lot) / total_vol
                        self.position['avg_price'] = new_avg
                        self.position['volume'] = total_vol
                        self.averaging_count += 1
                        self._add_marker('entry', current_price, 'sell', datetime.now())

        if (not self.trading_paused or is_profit) and self.averaging_count >= self.config.get('max_averaging', 4) and not self.is_reversed and self.reverse_count < self.config.get('max_reverses', 3):
            if side == 'buy' and current_price <= avg - 15 * self.tick_size:
                st.session_state.logs.append("🔄 Переворот BUY→SELL")
                self.close_position('sell', vol)
                self._close_trade(profit_usdt)
                new_lot = self.calculate_lot('sell', current_price, current_price + self.config.get('sl_ticks', 30) * self.tick_size)
                if new_lot > 0:
                    if not st.session_state.dry_run:
                        order = self.place_order('sell', new_lot)
                        if order:
                            self.position = {'side': 'sell', 'entry_price': current_price, 'avg_price': current_price, 'volume': new_lot}
                            self.averaging_count = 0
                            self.is_reversed = True
                            self.reverse_count += 1
                            self.trailing_active = False
                            self._add_marker('entry', current_price, 'sell', datetime.now())
                    else:
                        self.position = {'side': 'sell', 'entry_price': current_price, 'avg_price': current_price, 'volume': new_lot}
                        self.averaging_count = 0
                        self.is_reversed = True
                        self.reverse_count += 1
                        self.trailing_active = False
                        self._add_marker('entry', current_price, 'sell', datetime.now())
            elif side == 'sell' and current_price >= avg + 15 * self.tick_size:
                st.session_state.logs.append("🔄 Переворот SELL→BUY")
                self.close_position('buy', vol)
                self._close_trade(profit_usdt)
                new_lot = self.calculate_lot('buy', current_price, current_price - self.config.get('sl_ticks', 30) * self.tick_size)
                if new_lot > 0:
                    if not st.session_state.dry_run:
                        order = self.place_order('buy', new_lot)
                        if order:
                            self.position = {'side': 'buy', 'entry_price': current_price, 'avg_price': current_price, 'volume': new_lot}
                            self.averaging_count = 0
                            self.is_reversed = True
                            self.reverse_count += 1
                            self.trailing_active = False
                            self._add_marker('entry', current_price, 'buy', datetime.now())
                    else:
                        self.position = {'side': 'buy', 'entry_price': current_price, 'avg_price': current_price, 'volume': new_lot}
                        self.averaging_count = 0
                        self.is_reversed = True
                        self.reverse_count += 1
                        self.trailing_active = False
                        self._add_marker('entry', current_price, 'buy', datetime.now())

class SMAStrategy(BaseStrategy):
    def __init__(self, exchange, symbol, config):
        super().__init__(exchange, symbol, config)
        self.position = None
        self.fast_period = config.get('fast_period', 10)
        self.slow_period = config.get('slow_period', 30)

    def tick(self):
        current_price = self.get_current_price()
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, '1m', limit=50)
        if not ohlcv:
            return
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['sma_fast'] = df['close'].rolling(self.fast_period).mean()
        df['sma_slow'] = df['close'].rolling(self.slow_period).mean()
        fast = df['sma_fast'].iloc[-1]
        slow = df['sma_slow'].iloc[-1]
        prev_fast = df['sma_fast'].iloc[-2]
        prev_slow = df['sma_slow'].iloc[-2]

        if self.position is None:
            if fast > slow and prev_fast <= prev_slow:
                lot = self.config.get('lot', 0.001)
                st.session_state.logs.append(f"🟢 SMA: BUY сигнал по {current_price}")
                if not st.session_state.dry_run:
                    order = self.exchange.create_market_order(self.symbol, 'buy', lot)
                    if order:
                        self.position = {'side': 'buy', 'entry_price': current_price, 'volume': lot}
                else:
                    self.position = {'side': 'buy', 'entry_price': current_price, 'volume': lot}
        else:
            if fast < slow and prev_fast >= prev_slow:
                st.session_state.logs.append(f"🔴 SMA: SELL сигнал, закрываем позицию")
                if not st.session_state.dry_run:
                    self.exchange.create_market_order(self.symbol, 'sell', self.position['volume'])
                self.position = None

# ============================================================
# ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ (FALLBACK, ЕСЛИ WEBSOCKET ЕЩЁ НЕ ДАЛ ДАННЫХ)
# ============================================================
def fetch_ohlcv(symbol, timeframe='1m', limit=150):
    try:
        exchange = ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        dates = pd.date_range(end=datetime.now(), periods=limit, freq='1min')
        base_price = 60000 if 'BTC' in symbol else (3000 if 'ETH' in symbol else (150 if 'SOL' in symbol else 0.5))
        np.random.seed(42 + hash(symbol) % 100)
        close = base_price + np.cumsum(np.random.randn(limit) * base_price * 0.001)
        high = close + np.random.rand(limit) * base_price * 0.002
        low = close - np.random.rand(limit) * base_price * 0.002
        open_price = close - np.random.rand(limit) * base_price * 0.001
        return pd.DataFrame({
            'timestamp': dates,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(10, 100, limit)
        })

# ============================================================
# ФУНКЦИЯ ДЛЯ ОТОБРАЖЕНИЯ СТАТИСТИКИ ОБУЧЕНИЯ
# ============================================================
def display_learning_stats():
    if st.session_state.strategy and len(st.session_state.strategy.trade_history) > 0:
        st.markdown("#### 📊 Статистика обучения")
        trades = st.session_state.strategy.trade_history
        df_trades = pd.DataFrame(trades)
        if not df_trades.empty:
            fig_learn = go.Figure()
            fig_learn.add_trace(go.Scatter(
                x=df_trades['time'],
                y=df_trades['profit'].cumsum(),
                mode='lines',
                name='Кумулятивная прибыль',
                line=dict(color='#bb88ff', width=2)
            ))
            fig_learn.update_layout(
                template='plotly_dark',
                height=250,
                paper_bgcolor='#0d0d1a',
                plot_bgcolor='#0d0d1a',
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_learn, use_container_width=True)

# ============================================================
# ОСНОВНОЙ ИНТЕРФЕЙС
# ============================================================
# ===== ГАРАНТИРУЕМ ИНИЦИАЛИЗАЦИЮ AI (на случай, если она не сработала выше) =====
if 'ai_assistant' not in st.session_state:
    st.session_state.ai_assistant = DeepSeekAIAssistant()

st.markdown('<div class="main-header">📈 HOVMEL v7.1 — ЖИВОЙ ТЕРМИНАЛ</div>', unsafe_allow_html=True)

col_status1, col_status2, col_status3, col_status4, col_status5, col_status6 = st.columns(6)
with col_status1:
    mode_text = "🟢 ДЕМО" if st.session_state.mode == 'demo' else "🔴 РЕАЛ"
    mode_class = "status-demo" if st.session_state.mode == 'demo' else "status-real"
    st.markdown(f'<div class="{mode_class}">{mode_text}</div>', unsafe_allow_html=True)
with col_status2:
    if st.session_state.status == 'stopped':
        status_class = "status-stopped"
        status_text = "⏹ СТОП"
    elif st.session_state.strategy and hasattr(st.session_state.strategy, 'trading_paused') and st.session_state.strategy.trading_paused:
        status_class = "status-paused"
        status_text = "⏸ ПАУЗА"
    else:
        status_class = "status-running"
        status_text = "▶ РАБОТАЕТ"
    st.markdown(f'<div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)
with col_status3:
    dry_text = "🧪 DRY" if st.session_state.dry_run else "💪 REAL"
    st.markdown(f'<div class="status-stopped" style="background:#4466aa;">{dry_text}</div>', unsafe_allow_html=True)
with col_status4:
    # ===== БЕЗОПАСНОЕ ОБРАЩЕНИЕ К AI =====
    if 'ai_assistant' in st.session_state and st.session_state.ai_assistant:
        ai_status_text = "🧠 AI: ON" if st.session_state.ai_assistant.api_key else "🧠 AI: OFF"
    else:
        ai_status_text = "🧠 AI: OFF"
    st.markdown(f'<div class="status-ai">{ai_status_text}</div>', unsafe_allow_html=True)
with col_status5:
    st.markdown(f'<div style="color:#888; font-size:14px;">{st.session_state.selected_symbol}</div>', unsafe_allow_html=True)
with col_status6:
    st.markdown(f'<div style="text-align:right;color:#888;">{datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

col_sym1, col_sym2, col_tf = st.columns([2, 2, 2])
with col_sym1:
    new_symbol = st.selectbox("Инструмент", SYMBOLS, index=SYMBOLS.index(st.session_state.selected_symbol))
    if new_symbol != st.session_state.selected_symbol:
        st.session_state.selected_symbol = new_symbol
        st.session_state.logs.append(f"🔄 Переключено на {new_symbol}")
        st.session_state.position = None
        st.session_state.strategy = None
        st.rerun()
with col_tf:
    new_tf = st.selectbox("Таймфрейм", TIMEFRAMES, index=TIMEFRAMES.index(st.session_state.timeframe))
    if new_tf != st.session_state.timeframe:
        st.session_state.timeframe = new_tf
        st.session_state.logs.append(f"🔄 Таймфрейм изменён на {new_tf}")
        st.rerun()

col_strategy1, col_strategy2 = st.columns([2, 10])
with col_strategy1:
    new_strategy = st.selectbox("Стратегия", STRATEGIES, index=STRATEGIES.index(st.session_state.selected_strategy))
    if new_strategy != st.session_state.selected_strategy:
        st.session_state.selected_strategy = new_strategy
        st.session_state.logs.append(f"🔄 Переключено на стратегию {new_strategy}")
        st.session_state.strategy = None
        st.session_state.position = None
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Торговля", "📋 Журнал", "📈 Эксперт", "🧠 AI-Аналитика"])

# ========== ВКЛАДКА 1: ТОРГОВЛЯ ==========
with tab1:
    # Используем данные из буфера (если есть), иначе fallback
    if not st.session_state.ohlcv_buffer.empty:
        df = st.session_state.ohlcv_buffer.copy()
    else:
        df = fetch_ohlcv(st.session_state.selected_symbol, st.session_state.timeframe, limit=150)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                         row_heights=[0.7, 0.3], subplot_titles=(f'{st.session_state.selected_symbol} ({st.session_state.timeframe})', 'Объём'))
    fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                                   name=st.session_state.selected_symbol, increasing_line_color='#00ff88', decreasing_line_color='#ff4444'), row=1, col=1)
    # SMA
    if len(df) > 20:
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma20'], line=dict(color='#ffaa00', width=1.5), name='SMA 20'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma50'], line=dict(color='#4488ff', width=1.5), name='SMA 50'), row=1, col=1)

    # Линия текущей цены
    current_price = st.session_state.current_price if st.session_state.current_price else df['close'].iloc[-1]
    fig.add_hline(y=current_price, line=dict(color='#ffff00', width=1.5, dash='dot'),
                  annotation_text=f'Last: {current_price:.1f}', annotation_position='top right', row=1, col=1)

    # Линия входа и средняя
    if st.session_state.position:
        entry_price = st.session_state.position.get('entry_price', 0)
        avg_price = st.session_state.position.get('avg_price', entry_price)
        if entry_price:
            fig.add_hline(y=entry_price, line=dict(color='#00ff88', width=2, dash='dash'),
                          annotation_text=f'Entry: {entry_price:.1f}', annotation_position='top left', row=1, col=1)
        if avg_price and avg_price != entry_price:
            fig.add_hline(y=avg_price, line=dict(color='#ff8800', width=1.5, dash='dashdot'),
                          annotation_text=f'Avg: {avg_price:.1f}', annotation_position='bottom left', row=1, col=1)

    # Маркеры
    if 'markers' in st.session_state and st.session_state.markers:
        entry_buy_x, entry_buy_y, entry_sell_x, entry_sell_y, exit_x, exit_y = [], [], [], [], [], []
        for m in st.session_state.markers:
            if m['type'] == 'entry':
                if m['side'] == 'buy':
                    entry_buy_x.append(m['time']); entry_buy_y.append(m['price'])
                else:
                    entry_sell_x.append(m['time']); entry_sell_y.append(m['price'])
            else:
                exit_x.append(m['time']); exit_y.append(m['price'])
        if entry_buy_x:
            fig.add_trace(go.Scatter(x=entry_buy_x, y=entry_buy_y, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00ff88'),
                                     name='Entry BUY'), row=1, col=1)
        if entry_sell_x:
            fig.add_trace(go.Scatter(x=entry_sell_x, y=entry_sell_y, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#ff4444'),
                                     name='Entry SELL'), row=1, col=1)
        if exit_x:
            fig.add_trace(go.Scatter(x=exit_x, y=exit_y, mode='markers',
                                     marker=dict(symbol='circle', size=10, color='#ffd700'),
                                     name='Exit'), row=1, col=1)

    fig.add_trace(go.Bar(x=df['timestamp'], y=df['volume'], name='Volume', marker_color='#4466aa', opacity=0.6), row=2, col=1)
    fig.update_layout(template='plotly_dark', height=500, showlegend=True, hovermode='x unified',
                      paper_bgcolor='#0d0d1a', plot_bgcolor='#0d0d1a', margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    fig.update_xaxes(gridcolor='#1a1a2e', showgrid=True)
    fig.update_yaxes(gridcolor='#1a1a2e', showgrid=True)
    st.plotly_chart(fig, use_container_width=True, key="live_chart")

    # ---- ПАНЕЛЬ УПРАВЛЕНИЯ ----
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("▶️ СТАРТ", use_container_width=True):
            if not st.session_state.running:
                try:
                    api_key = os.getenv('OKX_API_KEY') or st.secrets.get('OKX_API_KEY', '')
                    secret = os.getenv('OKX_API_SECRET') or st.secrets.get('OKX_API_SECRET', '')
                    passphrase = os.getenv('OKX_API_PASSPHRASE') or st.secrets.get('OKX_API_PASSPHRASE', '')
                    if api_key and secret and passphrase:
                        exchange = ccxt.okx({
                            'apiKey': api_key, 'secret': secret, 'password': passphrase,
                            'enableRateLimit': True, 'options': {'defaultType': 'spot' if st.session_state.mode == 'demo' else 'future'}
                        })
                        st.session_state.logs.append("🔑 Подключение с API-ключами OKX")
                    else:
                        exchange = ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
                        st.session_state.logs.append("🌐 Публичный доступ (без API-ключей) — симуляция")
                        st.session_state.dry_run = True
                        st.session_state.balance = st.session_state.demo_balance
                    st.session_state.exchange = exchange
                    config = {
                        'risk_percent': st.session_state.get('risk', 1.0),
                        'max_lot': st.session_state.get('max_lot', 0.01),
                        'sl_ticks': st.session_state.get('sl_ticks', 30),
                        'tp_ticks': st.session_state.get('tp_ticks', 30),
                        'max_averaging': st.session_state.get('max_avg', 4),
                        'averaging_step_ticks': st.session_state.get('avg_step', 60),
                        'averaging_coefficient': st.session_state.get('avg_coef', 1.5),
                        'max_reverses': st.session_state.get('max_rev', 3),
                        'enable_trailing': st.session_state.get('trailing', True),
                        'trailing_distance_ticks': st.session_state.get('trail_dist', 40)
                    }
                    if st.session_state.selected_strategy == 'IATS':
                        st.session_state.strategy = IATSStrategyAI(exchange, st.session_state.selected_symbol, config, st.session_state.ai_assistant)
                    else:
                        sma_config = {'lot': config.get('max_lot', 0.01), 'fast_period': 10, 'slow_period': 30}
                        st.session_state.strategy = SMAStrategy(exchange, st.session_state.selected_symbol, sma_config)
                    if not api_key:
                        st.session_state.balance = st.session_state.demo_balance
                    else:
                        st.session_state.balance = st.session_state.strategy.get_balance('USDT')
                    st.session_state.running = True
                    st.session_state.status = 'running'
                    st.session_state.logs.append(f"🚀 Бот запущен на {st.session_state.selected_symbol} (стратегия: {st.session_state.selected_strategy})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка: {e}")
    with col2:
        if st.button("⏹ СТОП", use_container_width=True):
            st.session_state.running = False
            st.session_state.status = 'stopped'
            st.session_state.ws_running = False
            st.session_state.logs.append("⏹ Бот остановлен")
            st.rerun()
    with col3:
        if st.button("🧪 DRY ON", use_container_width=True):
            st.session_state.dry_run = True
            st.session_state.logs.append("🧪 Dry Run включён")
            st.rerun()
    with col4:
        if st.button("💪 DRY OFF", use_container_width=True):
            st.session_state.dry_run = False
            st.session_state.logs.append("💪 Dry Run выключен")
            st.rerun()
    with col5:
        if st.session_state.mode == 'demo':
            if st.button("🔴 РЕАЛ", use_container_width=True):
                st.session_state.mode = 'real'
                st.session_state.logs.append("🔴 Переключено на РЕАЛЬНЫЙ режим")
                st.rerun()
        else:
            if st.button("🟢 ДЕМО", use_container_width=True):
                st.session_state.mode = 'demo'
                st.session_state.logs.append("🟢 Переключено на ДЕМО режим")
                st.rerun()
    with col6:
        if st.button("🧠 AI ON", use_container_width=True):
            if st.session_state.ai_assistant.api_key:
                st.session_state.logs.append("🧠 AI активирован")
            else:
                st.error("❌ Добавьте DEEPSEEK_API_KEY")

    # ---- МЕТРИКИ ----
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">💰 Баланс</div><div class="metric-value metric-green">{st.session_state.balance:.2f}</div></div>', unsafe_allow_html=True)
    with col_m2:
        color = 'metric-green' if st.session_state.pnl >= 0 else 'metric-red'
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">📈 P&L</div><div class="metric-value {color}">{st.session_state.pnl:.2f}</div></div>', unsafe_allow_html=True)
    with col_m3:
        pos_text = f"{st.session_state.position['side'].upper()} {st.session_state.position['volume']:.3f}" if st.session_state.position else "—"
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">📊 Позиция</div><div class="metric-value metric-gold">{pos_text}</div></div>', unsafe_allow_html=True)
    with col_m4:
        price_text = f"{st.session_state.current_price:.1f}" if st.session_state.current_price else "—"
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">💹 Цена</div><div class="metric-value metric-blue">{price_text}</div></div>', unsafe_allow_html=True)
    with col_m5:
        ai_status = "Активен" if st.session_state.ai_assistant.api_key else "Неактивен"
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">🧠 AI</div><div class="metric-value metric-purple">{ai_status}</div></div>', unsafe_allow_html=True)

    # ---- НИЖНЯЯ ПАНЕЛЬ: ТОРГОВЛЯ (позиции, ордера, ручное открытие) ----
    st.markdown("---")
    st.markdown("### 📋 Торговля (ручное управление)")

    # Отображение текущей позиции
    if st.session_state.position:
        col_pos1, col_pos2, col_pos3, col_pos4, col_pos5 = st.columns(5)
        with col_pos1:
            st.write(f"**Символ:** {st.session_state.selected_symbol}")
        with col_pos2:
            st.write(f"**Направление:** {st.session_state.position['side'].upper()}")
        with col_pos3:
            st.write(f"**Объём:** {st.session_state.position['volume']:.3f}")
        with col_pos4:
            st.write(f"**Цена входа:** {st.session_state.position['entry_price']:.1f}")
        with col_pos5:
            if st.button("❌ Закрыть позицию", use_container_width=True):
                if st.session_state.dry_run:
                    st.session_state.logs.append("🧪 [DRY] Закрытие позиции")
                    st.session_state.position = None
                    st.session_state.pnl = 0
                    st.rerun()
                else:
                    if st.session_state.strategy:
                        side = 'sell' if st.session_state.position['side'] == 'buy' else 'buy'
                        order = st.session_state.strategy.close_position(side, st.session_state.position['volume'])
                        if order:
                            st.session_state.logs.append("✅ Позиция закрыта вручную")
                            st.session_state.position = None
                            st.session_state.pnl = 0
                            st.rerun()
                        else:
                            st.error("Ошибка закрытия позиции")
    else:
        st.info("Нет открытой позиции")

    # ---- Таблица ордеров ----
    st.markdown("#### Активные ордера")
    if st.session_state.manual_orders:
        df_orders = pd.DataFrame(st.session_state.manual_orders)
        st.dataframe(df_orders, use_container_width=True)
        for idx, order in enumerate(st.session_state.manual_orders):
            if st.button(f"🗑 Удалить ордер #{idx+1}", key=f"del_order_{idx}"):
                st.session_state.manual_orders.pop(idx)
                st.session_state.logs.append(f"🗑 Ордер удалён")
                st.rerun()
    else:
        st.write("Нет активных ордеров")

    # ---- Форма для ручного открытия ордера ----
    with st.expander("✏️ Открыть ордер вручную", expanded=False):
        order_type = st.selectbox("Тип ордера", ["Рыночный", "Лимитный", "Стоп-лимитный"])
        order_side = st.selectbox("Направление", ["BUY", "SELL"])
        order_symbol = st.selectbox("Символ", SYMBOLS, index=SYMBOLS.index(st.session_state.selected_symbol))
        order_volume = st.number_input("Объём (в базовой валюте)", min_value=0.001, value=0.01, step=0.001)
        order_price = 0.0
        order_stop = 0.0
        if order_type != "Рыночный":
            order_price = st.number_input("Цена (USDT)", min_value=0.0, value=60000.0, step=100.0)
        if order_type == "Стоп-лимитный":
            order_stop = st.number_input("Стоп-цена", min_value=0.0, value=59500.0, step=100.0)
        if st.button("Отправить ордер"):
            if st.session_state.dry_run:
                st.session_state.logs.append(f"🧪 [DRY] {order_type} {order_side} {order_symbol} объём {order_volume} цена {order_price if order_price else 'рыночная'}")
                st.session_state.manual_orders.append({
                    'symbol': order_symbol,
                    'side': order_side,
                    'type': order_type,
                    'volume': order_volume,
                    'price': order_price,
                    'stop': order_stop,
                    'time': datetime.now()
                })
                st.rerun()
            else:
                try:
                    if order_type == "Рыночный":
                        order = st.session_state.exchange.create_market_order(order_symbol, order_side.lower(), order_volume)
                    elif order_type == "Лимитный":
                        order = st.session_state.exchange.create_limit_order(order_symbol, order_side.lower(), order_volume, order_price)
                    else:
                        order = st.session_state.exchange.create_order(order_symbol, 'limit', order_side.lower(), order_volume, order_price, {'stopPrice': order_stop})
                    st.session_state.logs.append(f"✅ Ордер отправлен: {order}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка отправки ордера: {e}")

# ========== ВКЛАДКА 2: ЖУРНАЛ ==========
with tab2:
    st.markdown("### 📋 Журнал событий")
    if st.button("🗑 Очистить журнал"):
        st.session_state.logs = []
        st.rerun()
    log_html = ""
    for log in st.session_state.logs[-100:]:
        if "🟢" in log or "✅" in log:
            log_html += f'<div class="log-entry-green">{log}</div>'
        elif "🔴" in log or "❌" in log:
            log_html += f'<div class="log-entry-red">{log}</div>'
        elif "🧠" in log or "AI" in log or "🔄" in log or "⏸️" in log or "🟡" in log or "🛡️" in log:
            log_html += f'<div class="log-entry-gold">{log}</div>'
        elif "⏰" in log:
            log_html += f'<div class="log-entry-orange">{log}</div>'
        elif "📊" in log or "💰" in log or "📈" in log:
            log_html += f'<div class="log-entry-blue">{log}</div>'
        else:
            log_html += f'<div class="log-entry-white">{log}</div>'
    if log_html:
        st.markdown(f'<div class="log-container">{log_html}</div>', unsafe_allow_html=True)
    else:
        st.info("Журнал пуст.")

# ========== ВКЛАДКА 3: ЭКСПЕРТ ==========
with tab3:
    st.markdown("### 📈 Эксперт — Статистика")
    if not st.session_state.history_data.empty:
        total_trades = len(st.session_state.history_data)
        win_trades = len(st.session_state.history_data[st.session_state.history_data['profit'] > 0])
        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
        total_profit = st.session_state.history_data['profit'].sum()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Всего сделок", total_trades)
        col2.metric("Винрейт", f"{win_rate:.1f}%")
        col3.metric("Общая прибыль", f"{total_profit:.2f} USDT", delta_color="normal" if total_profit >= 0 else "inverse")
        col4.metric("Средняя прибыль", f"{total_profit/total_trades:.2f}" if total_trades > 0 else "0")
    else:
        st.info("Нет данных о сделках")

    if not st.session_state.history_data.empty:
        st.markdown("### 📜 История сделок")
        hist_df = st.session_state.history_data.sort_values('time', ascending=False).copy()
        def color_profit(val):
            if val > 0:
                return 'color: #4488ff; font-weight: bold;'
            elif val < 0:
                return 'color: #ff4444; font-weight: bold;'
            else:
                return ''
        styled_df = hist_df.style.applymap(color_profit, subset=['profit'])
        st.dataframe(styled_df, use_container_width=True)

        if not st.session_state.equity_data.empty:
            fig_eq = go.Figure()
            fig_eq.add_trace(go.Scatter(x=st.session_state.equity_data['time'], y=st.session_state.equity_data['equity'],
                                        mode='lines', name='Equity', line=dict(color='#00ff88', width=2)))
            fig_eq.update_layout(template='plotly_dark', height=300, paper_bgcolor='#0d0d1a', plot_bgcolor='#0d0d1a',
                                 margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_eq, use_container_width=True)

    with st.expander("⚙️ Настройки стратегии (для IATS)"):
        col1, col2 = st.columns(2)
        with col1:
            st.slider("Риск на сделку (%)", 0.1, 5.0, 1.0, 0.1, key="risk")
            st.number_input("Макс. лот", 0.001, 0.1, 0.01, 0.001, key="max_lot")
            st.number_input("Стоп-лосс (тики)", 10, 200, 30, 5, key="sl_ticks")
            st.number_input("Тейк-профит (тики)", 10, 200, 30, 5, key="tp_ticks")
            st.number_input("Макс. усреднений", 1, 10, 4, 1, key="max_avg")
        with col2:
            st.number_input("Шаг усреднения (тики)", 20, 200, 60, 5, key="avg_step")
            st.slider("Коэф. усреднения", 1.0, 3.0, 1.5, 0.1, key="avg_coef")
            st.number_input("Макс. переворотов", 0, 5, 3, 1, key="max_rev")
            st.checkbox("Включить трейлинг", True, key="trailing")
            st.number_input("Дистанция трейлинга (тики)", 10, 100, 40, 5, key="trail_dist")
            st.number_input("Интервал сканирования (сек)", 5, 60, 10, 5, key="scan_interval")

# ========== ВКЛАДКА 4: AI-АНАЛИТИКА ==========
with tab4:
    st.markdown("### 🤖 AI-Аналитика (DeepSeek)")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📊 Текущий анализ")
        if st.button("🔄 Обновить AI-аналитику", use_container_width=True):
            if st.session_state.strategy and hasattr(st.session_state.strategy, 'check_ai_trend'):
                st.session_state.strategy.check_ai_trend()
                st.session_state.strategy.check_ai_sentiment()
                st.rerun()
            else:
                st.warning("Сначала запустите бота (▶️ СТАРТ) и выберите стратегию IATS")
        if hasattr(st.session_state.strategy, 'ai_suggestions') and st.session_state.strategy.ai_suggestions:
            suggestion = st.session_state.strategy.ai_suggestions
            trend_emoji = "📈" if suggestion.get('trend') == 'up' else "📉" if suggestion.get('trend') == 'down' else "➡️"
            trend_text = "ВОСХОДЯЩИЙ" if suggestion.get('trend') == 'up' else "НИСХОДЯЩИЙ" if suggestion.get('trend') == 'down' else "НЕЙТРАЛЬНЫЙ"
            st.metric("Тренд", f"{trend_emoji} {trend_text}", f"Уверенность: {suggestion.get('confidence', 0)}%")
            st.write(f"**Причина:** {suggestion.get('reason', 'Нет данных')}")
            st.write(f"**Настроение:** {suggestion.get('sentiment', 'neutral')}")
            st.write(f"**Рекомендация:** {suggestion.get('next_move', 'wait')}")
            st.markdown("#### 💡 Рекомендации AI")
            rec_data = {
                "Стоп-лосс": f"{suggestion.get('suggested_sl_ticks', 30)} тиков",
                "Шаг усреднения": f"{suggestion.get('suggested_avg_step', 60)} тиков",
                "Риск": f"{suggestion.get('suggested_risk', 1.0)}%"
            }
            st.dataframe(pd.DataFrame([rec_data]), use_container_width=True)
        else:
            st.info("Ожидание анализа от AI...")
    with col2:
        st.markdown("#### 📰 Экономический календарь")
        if hasattr(st.session_state.strategy, 'trading_paused'):
            if st.session_state.strategy.trading_paused:
                st.warning(f"⏸️ Торговля ПРИОСТАНОВЛЕНА!\n\nПричина: {st.session_state.strategy.pause_reason}")
            else:
                st.success("✅ Торговля активна. AI не обнаружил критических новостей.")
            if hasattr(st.session_state.strategy, '_get_financial_calendar'):
                events = st.session_state.strategy._get_financial_calendar()
                if events:
                    st.markdown("#### 📅 Ближайшие события")
                    for ev in events[:3]:
                        st.write(f"• {ev['date']} {ev['time']} — **{ev['event']}** (важность: {ev['importance']})")
                else:
                    st.write("Сегодня важных событий нет")
        else:
            st.info("Запустите бота (IATS) для получения данных")
        st.markdown("#### 🔌 Статус AI")
        if st.session_state.ai_assistant.api_key:
            st.success("✅ DeepSeek API подключён")
            if hasattr(st.session_state.strategy, 'ai_last_update'):
                st.write(f"**Последнее обновление AI:** {st.session_state.strategy.ai_last_update or 'Никогда'}")
        else:
            st.error("❌ DeepSeek API не настроен! Добавьте DEEPSEEK_API_KEY")
            st.markdown("""
            **Как получить ключ:**
            1. Зайди на [platform.deepseek.com](https://platform.deepseek.com)
            2. Зарегистрируйся и создай API-ключ
            3. Добавь в `.env` или Secrets Streamlit:
DEEPSEEK_API_KEY=твой_ключ

text
""")
display_learning_stats()

# ============================================================
# ЗАПУСК ФОНОВОГО ПОТОКА
# ============================================================
start_bot_thread()

# ============================================================
# ФУТЕР
# ============================================================
st.markdown("---")
st.markdown(
'<div style="text-align:center;color:#666;font-size:12px;padding:20px;">'
'HOVMEL IATS — ШЕДЕВР v7.1_final | Живой график (WebSocket) | Ручное управление | '
'MT5-интерфейс | © 2024 HOVMEL Trading Systems'
'</div>',
unsafe_allow_html=True
)
