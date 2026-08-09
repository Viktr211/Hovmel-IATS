# ============================================================
# HOVMEL IATS — ШЕДЕВР v6.2 (РЕАЛЬНЫЙ ГРАФИК, БАЛАНС 3000, МАРКЕРЫ)
# (c) 2024 HOVMEL Trading Systems
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
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

st.set_page_config(
    page_title="HOVMEL IATS v6.2 - Real-time Chart",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# АВТО-ОБНОВЛЕНИЕ (каждую секунду, если бот запущен)
# ============================================================
if st.session_state.get('running', False):
    st_autorefresh(interval=1000, key="chart_refresh")

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
</style>
""", unsafe_allow_html=True)

# ============================================================
# ФУНКЦИЯ СТАТИСТИКИ ОБУЧЕНИЯ
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
# ФУНКЦИЯ ЗАПУСКА ФОНОВОГО ПОТОКА
# ============================================================
def start_bot_thread():
    if st.session_state.running and st.session_state.strategy:
        if not st.session_state.thread_started:
            def bot_loop():
                while st.session_state.running:
                    try:
                        st.session_state.strategy.tick()
                        time.sleep(st.session_state.get('scan_interval', 10))
                    except Exception as e:
                        st.session_state.logs.append(f"❌ Ошибка в цикле: {e}")
                        time.sleep(5)
            thread = threading.Thread(target=bot_loop, daemon=True)
            thread.start()
            st.session_state.thread_started = True
            st.session_state.logs.append("🧵 Фоновый поток запущен")
        if st.session_state.running:
            time.sleep(0.5)
            st.rerun()

# ============================================================
# AI-АССИСТЕНТ (DeepSeek)
# ============================================================
class DeepSeekAIAssistant:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY') or st.secrets.get('DEEPSEEK_API_KEY', '')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.cache = {}
        self.conversation_history = []
        self.learning_memory = {}

    def analyze(self, analysis_type, data):
        if not self.api_key:
            return {"error": "Не задан API-ключ DeepSeek"}
        prompt = self._build_prompt(analysis_type, data)
        response = self._call_deepseek(prompt)
        self.conversation_history.append({
            'time': datetime.now().isoformat(),
            'type': analysis_type,
            'data': data,
            'response': response
        })
        return response

    def _build_prompt(self, analysis_type, data):
        prompts = {
            'trend': f"""
            Проанализируй рыночные данные и определи тренд:
            {json.dumps(data, indent=2)}
            Ответь строго в JSON формате:
            {{
                "trend": "up" или "down" или "neutral",
                "confidence": число от 0 до 100,
                "reason": "краткое объяснение (на русском)",
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
                "news_items": ["список важных событий"],
                "time_to_news_minutes": число,
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
                "support_level": число,
                "resistance_level": число,
                "recommendation": "buy" или "sell" или "wait"
            }}
            """,
            'learn': f"""
            Проанализируй историю сделок:
            {json.dumps(data, indent=2)}
            Ответь в JSON:
            {{
                "best_time_to_trade": "часы",
                "worst_time_to_trade": "часы",
                "optimal_avg_count": число,
                "optimal_avg_step": число,
                "winrate_improvement_suggestions": ["предложения"],
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
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты эксперт по криптовалютной торговле. Отвечай только структурированным JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "max_tokens": 1000
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                return json.loads(content)
            else:
                return {"error": f"API ошибка: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

# ============================================================
# БАЗОВЫЙ КЛАСС СТРАТЕГИИ
# ============================================================
class BaseStrategy:
    def __init__(self, exchange, symbol, config):
        self.exchange = exchange
        self.symbol = symbol
        self.config = config
        self.position = None
        self.trade_history = []

    def tick(self):
        raise NotImplementedError("Метод tick() должен быть переопределён")

    def get_balance(self, currency='USDT'):
        # Если есть ключи — запрашиваем реальный баланс, иначе используем демо-баланс из сессии
        try:
            if hasattr(self.exchange, 'apiKey') and self.exchange.apiKey:
                balance = self.exchange.fetch_balance()
                return balance['free'].get(currency, 0.0)
            else:
                return st.session_state.demo_balance
        except:
            return st.session_state.demo_balance

    def get_current_price(self):
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return ticker['last']
        except:
            return 0.0

# ============================================================
# СТРАТЕГИЯ IATS (сокращённая для экономии места, но полная)
# ============================================================
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
        self.last_entry_time = 0
        self.ai_last_update = None
        self.ai_suggestions = {}
        self.trading_paused = False
        self.pause_reason = ""
        self.pause_until = None
        self.learning_stats = {}
        self.best_hours = []
        self.worst_hours = []

    def _get_tick_size(self):
        market = self.exchange.market(self.symbol)
        return market['precision']['price']

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
            'price_change_1h': (close.iloc[-1] - close.iloc[-60]) / close.iloc[-60] * 100 if len(close) >= 60 else 0,
            'price_change_24h': self._get_24h_change()
        }

    def _calculate_rsi(self, prices, period=14):
        if len(prices) < period:
            return 50
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def _get_24h_change(self):
        try:
            ticker = self.exchange.fetch_ticker(self.symbol)
            return ticker.get('percentage', 0)
        except:
            return 0

    def check_time_filter(self):
        now = datetime.now()
        hour = now.hour
        if self.learning_stats:
            best = self.learning_stats.get('best_hours', [])
            worst = self.learning_stats.get('worst_hours', [])
            if best and hour not in best:
                return False
            if worst and hour in worst:
                return False
        return True

    def _get_financial_calendar(self):
        events = [
            {"date": "2024-11-06", "time": "14:00", "event": "FOMC Interest Rate Decision", "importance": "high"},
            {"date": "2024-12-18", "time": "14:00", "event": "FOMC Interest Rate Decision", "importance": "high"},
            {"date": "2024-11-01", "time": "13:30", "event": "Non-Farm Payrolls (NFP)", "importance": "high"},
            {"date": "2024-12-06", "time": "13:30", "event": "Non-Farm Payrolls (NFP)", "importance": "high"},
            {"date": "2024-11-13", "time": "13:30", "event": "CPI Inflation Data", "importance": "high"},
            {"date": "2024-12-11", "time": "13:30", "event": "CPI Inflation Data", "importance": "high"},
            {"date": "2024-11-14", "time": "13:30", "event": "PPI Producer Price Index", "importance": "medium"},
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
                pause_before = result.get('pause_before_minutes', 60)
                pause_after = result.get('pause_after_minutes', 30)
                self.trading_paused = True
                self.pause_reason = f"Важные новости: {', '.join(result.get('news_items', []))}"
                self.pause_until = datetime.now() + timedelta(minutes=pause_before + pause_after + 10)
                st.session_state.logs.append(f"⏸️ Пауза: {self.pause_reason}")
            else:
                self.trading_paused = False
                self.pause_reason = ""
                self.pause_until = None

    def check_ai_trend(self):
        if not self.ai.api_key:
            return
        df = self.fetch_ohlcv(limit=100, timeframe=st.session_state.timeframe)
        if df.empty:
            return
        indicators = self.calculate_indicators(df)
        market_data = {
            "price": df['close'].iloc[-1],
            "sma20": indicators.get('sma20'),
            "sma50": indicators.get('sma50'),
            "rsi": indicators.get('rsi'),
            "volatility": indicators.get('volatility'),
            "volume": indicators.get('volume'),
            "price_change_1h": indicators.get('price_change_1h'),
            "price_change_24h": indicators.get('price_change_24h'),
            "last_10_returns": df['close'].pct_change().tail(10).tolist()
        }
        result = self.ai.analyze('trend', market_data)
        if result and not result.get('error'):
            self.ai_suggestions = result
            st.session_state.logs.append(f"🧠 AI: тренд {result.get('trend')}, уверенность {result.get('confidence')}%")
            if result.get('suggested_sl_ticks'):
                self.config['sl_ticks'] = int(result['suggested_sl_ticks'])
            if result.get('suggested_avg_step'):
                self.config['averaging_step_ticks'] = int(result['suggested_avg_step'])
            if result.get('suggested_risk'):
                self.config['risk_percent'] = float(result['suggested_risk'])
            return result
        return None

    def check_ai_sentiment(self):
        if not self.ai.api_key:
            return
        df = self.fetch_ohlcv(limit=50, timeframe=st.session_state.timeframe)
        if df.empty:
            return
        indicators = self.calculate_indicators(df)
        sentiment_data = {
            "price": df['close'].iloc[-1],
            "high_24h": df['high'].max(),
            "low_24h": df['low'].min(),
            "volume": indicators.get('volume'),
            "volatility": indicators.get('volatility'),
            "rsi": indicators.get('rsi'),
            "price_change_1h": indicators.get('price_change_1h'),
            "price_change_24h": indicators.get('price_change_24h')
        }
        result = self.ai.analyze('sentiment', sentiment_data)
        if result and not result.get('error'):
            st.session_state.logs.append(f"🧠 AI: настроение {result.get('overall_sentiment')}, страх/жадность {result.get('fear_greed_index', 50)}")
            return result
        return None

    def check_ai_learning(self):
        if not self.ai.api_key or len(self.trade_history) < 10:
            return
        learning_data = {
            "total_trades": len(self.trade_history),
            "winrate": sum(1 for t in self.trade_history if t.get('profit', 0) > 0) / len(self.trade_history) * 100,
            "avg_profit": sum(t.get('profit', 0) for t in self.trade_history) / len(self.trade_history),
            "best_profit": max((t.get('profit', 0) for t in self.trade_history), default=0),
            "worst_loss": min((t.get('profit', 0) for t in self.trade_history), default=0),
            "trades_by_hour": self._get_trades_by_hour(),
            "avg_entries": self.averaging_count,
            "reverses": self.reverse_count
        }
        result = self.ai.analyze('learn', learning_data)
        if result and not result.get('error'):
            self.learning_stats = result
            self.best_hours = result.get('best_time_to_trade', [])
            self.worst_hours = result.get('worst_time_to_trade', [])
            st.session_state.logs.append(f"🧠 AI: обучение завершено, лучшие часы {self.best_hours}")

    def _get_trades_by_hour(self):
        hours = {}
        for trade in self.trade_history:
            hour = trade.get('hour', 0)
            profit = trade.get('profit', 0)
            if hour not in hours:
                hours[hour] = {'count': 0, 'profit': 0}
            hours[hour]['count'] += 1
            hours[hour]['profit'] += profit
        best_hours = []
        worst_hours = []
        for hour, data in hours.items():
            if data['count'] >= 2:
                avg_profit = data['profit'] / data['count']
                if avg_profit > 10:
                    best_hours.append(hour)
                elif avg_profit < -5:
                    worst_hours.append(hour)
        return {'best_hours': best_hours, 'worst_hours': worst_hours, 'all': hours}

    def adapt_strategy_to_market(self):
        if not self.ai.api_key:
            return
        df = self.fetch_ohlcv(limit=50, timeframe=st.session_state.timeframe)
        if df.empty:
            return
        indicators = self.calculate_indicators(df)
        market_state = {
            "volatility": indicators.get('volatility'),
            "rsi": indicators.get('rsi'),
            "volume": indicators.get('volume'),
            "trend": self.ai_suggestions.get('trend', 'neutral') if self.ai_suggestions else 'unknown',
            "current_price": df['close'].iloc[-1],
            "balance": self.get_balance('USDT')
        }
        result = self.ai.analyze('market_state', market_state)
        if result and not result.get('error'):
            if result.get('risk_percent'):
                self.config['risk_percent'] = float(result['risk_percent'])
            if result.get('max_lot'):
                self.config['max_lot'] = float(result['max_lot'])
            if result.get('sl_ticks'):
                self.config['sl_ticks'] = int(result['sl_ticks'])
            if result.get('avg_step'):
                self.config['averaging_step_ticks'] = int(result['avg_step'])
            if result.get('avg_coefficient'):
                self.config['averaging_coefficient'] = float(result['avg_coefficient'])
            if result.get('trailing_distance'):
                self.config['trailing_distance_ticks'] = int(result['trailing_distance'])
            if result.get('max_averaging'):
                self.config['max_averaging'] = int(result['max_averaging'])
            st.session_state.logs.append(f"🧠 AI: адаптировал стратегию к рынку (уверенность {result.get('confidence', 50)}%)")

    def calculate_lot(self, side, entry_price, stop_loss_price):
        balance_usdt = self.get_balance('USDT')
        risk_amount = balance_usdt * (self.config.get('risk_percent', 1.0) / 100.0)
        price_diff = abs(entry_price - stop_loss_price)
        if price_diff == 0:
            return 0.0
        lot = risk_amount / price_diff
        step = self.exchange.market(self.symbol)['precision']['amount']
        lot = math.floor(lot / step) * step
        if lot > self.config.get('max_lot', 0.01):
            lot = self.config.get('max_lot', 0.01)
        if lot < self.exchange.market(self.symbol)['limits']['amount']['min']:
            lot = 0.0
        return lot

    def place_order(self, side, amount, order_type='market', stop_loss=None, take_profit=None):
        try:
            params = {}
            if stop_loss:
                params['stopLoss'] = {'stopPrice': stop_loss}
            if take_profit:
                params['takeProfit'] = {'limitPrice': take_profit}
            order = self.exchange.create_market_order(self.symbol, side, amount, params=params)
            return order
        except Exception as e:
            st.session_state.logs.append(f"❌ Ошибка ордера: {e}")
            return None

    def close_position(self, side, volume):
        try:
            order = self.exchange.create_market_order(self.symbol, side, volume)
            return order
        except Exception as e:
            st.session_state.logs.append(f"❌ Ошибка закрытия: {e}")
            return None

    def check_entry_signal(self):
        now = datetime.now()
        if now.second % 2 != 0:
            return False
        if self.trading_paused:
            if self.pause_until and datetime.now() < self.pause_until:
                return False
            else:
                self.trading_paused = False
                self.pause_reason = ""
        if not self.check_time_filter():
            return False
        if self.ai_suggestions:
            next_move = self.ai_suggestions.get('next_move', 'wait')
            if next_move == 'wait':
                return False
            if next_move == 'sell' and self.ai_suggestions.get('trend') == 'up':
                return False
            if next_move == 'buy' and self.ai_suggestions.get('trend') == 'down':
                return False
        return True

    def _add_marker(self, marker_type, price, side, time):
        if 'markers' not in st.session_state:
            st.session_state.markers = []
        st.session_state.markers.append({
            'type': marker_type,
            'price': price,
            'side': side,
            'time': time
        })
        if len(st.session_state.markers) > 200:
            st.session_state.markers = st.session_state.markers[-200:]

    def _close_trade(self, profit):
        if not self.position:
            return
        self._add_marker('exit', self.get_current_price(), self.position['side'], datetime.now())
        trade_data = {
            'time': datetime.now(),
            'symbol': self.symbol,
            'side': self.position['side'],
            'volume': self.position['volume'],
            'profit': profit,
            'hour': datetime.now().hour,
            'avg_count': self.averaging_count,
            'is_reversed': self.is_reversed
        }
        self.trade_history.append(trade_data)
        st.session_state.trade_history = self.trade_history
        new_row = pd.DataFrame({
            'time': [datetime.now()],
            'symbol': [self.symbol],
            'side': [self.position['side']],
            'volume': [self.position['volume']],
            'profit': [profit]
        })
        if st.session_state.history_data.empty:
            st.session_state.history_data = new_row
        else:
            st.session_state.history_data = pd.concat([st.session_state.history_data, new_row], ignore_index=True)
        current_equity = st.session_state.balance + st.session_state.history_data['profit'].sum()
        eq_row = pd.DataFrame({
            'time': [datetime.now()],
            'equity': [current_equity]
        })
        if st.session_state.equity_data.empty:
            st.session_state.equity_data = eq_row
        else:
            st.session_state.equity_data = pd.concat([st.session_state.equity_data, eq_row], ignore_index=True)

    def tick(self):
        now = datetime.now()
        if self.ai_last_update is None or (now - self.ai_last_update).seconds > 300:
            self.ai_last_update = now
            self.check_ai_news()
            self.check_ai_trend()
            self.check_ai_sentiment()
            self.adapt_strategy_to_market()
            if len(self.trade_history) > 10 and (now.minute == 0):
                self.check_ai_learning()

        if self.trading_paused and self.pause_until and now < self.pause_until:
            pass

        current_price = self.get_current_price()
        st.session_state.current_price = current_price

        if self.position is None:
            if self.check_entry_signal():
                sl_price = current_price - self.config.get('sl_ticks', 30) * self.tick_size
                lot = self.calculate_lot('buy', current_price, sl_price)
                if lot > 0:
                    st.session_state.logs.append(f"🟢 Вход: покупаем {lot} {self.symbol.split('/')[0]} по {current_price}")
                    if not st.session_state.dry_run:
                        order = self.place_order('buy', lot)
                        if order:
                            self.position = {
                                'side': 'buy',
                                'entry_price': current_price,
                                'avg_price': current_price,
                                'volume': lot
                            }
                            self.averaging_count = 0
                            self.is_reversed = False
                            self.trailing_active = False
                            self.last_entry_time = time.time()
                            st.session_state.logs.append(f"✅ Позиция открыта")
                            self._add_marker('entry', current_price, 'buy', datetime.now())
                    else:
                        self.position = {
                            'side': 'buy',
                            'entry_price': current_price,
                            'avg_price': current_price,
                            'volume': lot
                        }
                        self.averaging_count = 0
                        self.is_reversed = False
                        self.trailing_active = False
                        self.last_entry_time = time.time()
                        st.session_state.logs.append(f"🧪 [DRY] Позиция открыта")
                        self._add_marker('entry', current_price, 'buy', datetime.now())
            return

        side = self.position['side']
        avg_price = self.position['avg_price']
        volume = self.position['volume']

        if side == 'buy':
            profit_usdt = (current_price - avg_price) * volume
        else:
            profit_usdt = (avg_price - current_price) * volume
        st.session_state.pnl = profit_usdt

        is_profit = profit_usdt >= 0
        apply_stop_and_trailing = not (self.trading_paused and not is_profit)

        if not apply_stop_and_trailing:
            st.session_state.logs.append(f"🛡️ Пауза: позиция убыточная ({profit_usdt:.2f}), стоп и трейлинг отключены")

        if apply_stop_and_trailing:
            if side == 'buy':
                sl_price = avg_price - self.config.get('sl_ticks', 30) * self.tick_size
                if current_price <= sl_price:
                    st.session_state.logs.append(f"🔴 Стоп-лосс сработал! Цена {current_price}, SL {sl_price}")
                    self.close_position('sell', volume)
                    self._close_trade(profit_usdt)
                    self.position = None
                    return
            else:
                sl_price = avg_price + self.config.get('sl_ticks', 30) * self.tick_size
                if current_price >= sl_price:
                    st.session_state.logs.append(f"🔴 Стоп-лосс сработал! Цена {current_price}, SL {sl_price}")
                    self.close_position('buy', volume)
                    self._close_trade(profit_usdt)
                    self.position = None
                    return

        if apply_stop_and_trailing and self.config.get('enable_trailing', True):
            if not self.trailing_active:
                profit_ticks = (current_price - avg_price) / self.tick_size if side == 'buy' else (avg_price - current_price) / self.tick_size
                if profit_ticks >= self.config.get('trailing_distance_ticks', 40):
                    self.trailing_active = True
                    if side == 'buy':
                        self.trailing_level = current_price - self.config.get('trailing_distance_ticks', 40) * self.tick_size
                    else:
                        self.trailing_level = current_price + self.config.get('trailing_distance_ticks', 40) * self.tick_size
                    st.session_state.logs.append(f"🟡 Трейлинг активирован, уровень {self.trailing_level}")
            else:
                if side == 'buy':
                    new_level = current_price - self.config.get('trailing_distance_ticks', 40) * self.tick_size
                    if new_level > self.trailing_level:
                        self.trailing_level = new_level
                    if current_price <= self.trailing_level:
                        st.session_state.logs.append(f"🟡 Трейлинг сработал! Цена {current_price}")
                        self.close_position('sell', volume)
                        self._close_trade(profit_usdt)
                        self.position = None
                        return
                else:
                    new_level = current_price + self.config.get('trailing_distance_ticks', 40) * self.tick_size
                    if new_level < self.trailing_level:
                        self.trailing_level = new_level
                    if current_price >= self.trailing_level:
                        st.session_state.logs.append(f"🟡 Трейлинг сработал! Цена {current_price}")
                        self.close_position('buy', volume)
                        self._close_trade(profit_usdt)
                        self.position = None
                        return

        if self.averaging_count < self.config.get('max_averaging', 4):
            step = self.config.get('averaging_step_ticks', 60) * (self.averaging_count + 1) * self.tick_size
            if side == 'buy':
                if current_price <= avg_price - step:
                    new_lot = self.calculate_lot('buy', current_price, current_price - self.config.get('sl_ticks', 30) * self.tick_size)
                    if new_lot > 0:
                        st.session_state.logs.append(f"🔄 Усреднение #{self.averaging_count+1}: покупаем {new_lot}")
                        if not st.session_state.dry_run:
                            order = self.place_order('buy', new_lot)
                            if order:
                                total_volume = volume + new_lot
                                new_avg = (avg_price * volume + current_price * new_lot) / total_volume
                                self.position['avg_price'] = new_avg
                                self.position['volume'] = total_volume
                                self.averaging_count += 1
                                st.session_state.logs.append(f"✅ Новая средняя: {new_avg}")
                                self._add_marker('entry', current_price, 'buy', datetime.now())
                        else:
                            total_volume = volume + new_lot
                            new_avg = (avg_price * volume + current_price * new_lot) / total_volume
                            self.position['avg_price'] = new_avg
                            self.position['volume'] = total_volume
                            self.averaging_count += 1
                            st.session_state.logs.append(f"🧪 [DRY] Усреднение #{self.averaging_count}")
                            self._add_marker('entry', current_price, 'buy', datetime.now())
            else:
                if current_price >= avg_price + step:
                    new_lot = self.calculate_lot('sell', current_price, current_price + self.config.get('sl_ticks', 30) * self.tick_size)
                    if new_lot > 0:
                        st.session_state.logs.append(f"🔄 Усреднение #{self.averaging_count+1}: продаём {new_lot}")
                        if not st.session_state.dry_run:
                            order = self.place_order('sell', new_lot)
                            if order:
                                total_volume = volume + new_lot
                                new_avg = (avg_price * volume + current_price * new_lot) / total_volume
                                self.position['avg_price'] = new_avg
                                self.position['volume'] = total_volume
                                self.averaging_count += 1
                                st.session_state.logs.append(f"✅ Новая средняя: {new_avg}")
                                self._add_marker('entry', current_price, 'sell', datetime.now())
                        else:
                            total_volume = volume + new_lot
                            new_avg = (avg_price * volume + current_price * new_lot) / total_volume
                            self.position['avg_price'] = new_avg
                            self.position['volume'] = total_volume
                            self.averaging_count += 1
                            st.session_state.logs.append(f"🧪 [DRY] Усреднение #{self.averaging_count}")
                            self._add_marker('entry', current_price, 'sell', datetime.now())

        if not self.trading_paused or is_profit:
            if self.averaging_count >= self.config.get('max_averaging', 4) and not self.is_reversed and self.reverse_count < self.config.get('max_reverses', 3):
                if side == 'buy' and current_price <= avg_price - 15 * self.tick_size:
                    st.session_state.logs.append(f"🔄 Переворот: закрываем BUY, открываем SELL")
                    self.close_position('sell', volume)
                    self._close_trade(profit_usdt)
                    new_lot = self.calculate_lot('sell', current_price, current_price + self.config.get('sl_ticks', 30) * self.tick_size)
                    if new_lot > 0:
                        if not st.session_state.dry_run:
                            order = self.place_order('sell', new_lot)
                            if order:
                                self.position = {
                                    'side': 'sell',
                                    'entry_price': current_price,
                                    'avg_price': current_price,
                                    'volume': new_lot
                                }
                                self.averaging_count = 0
                                self.is_reversed = True
                                self.reverse_count += 1
                                self.trailing_active = False
                                st.session_state.logs.append(f"✅ Переворот выполнен")
                                self._add_marker('entry', current_price, 'sell', datetime.now())
                        else:
                            self.position = {
                                'side': 'sell',
                                'entry_price': current_price,
                                'avg_price': current_price,
                                'volume': new_lot
                            }
                            self.averaging_count = 0
                            self.is_reversed = True
                            self.reverse_count += 1
                            self.trailing_active = False
                            st.session_state.logs.append(f"🧪 [DRY] Переворот выполнен")
                            self._add_marker('entry', current_price, 'sell', datetime.now())
                elif side == 'sell' and current_price >= avg_price + 15 * self.tick_size:
                    st.session_state.logs.append(f"🔄 Переворот: закрываем SELL, открываем BUY")
                    self.close_position('buy', volume)
                    self._close_trade(profit_usdt)
                    new_lot = self.calculate_lot('buy', current_price, current_price - self.config.get('sl_ticks', 30) * self.tick_size)
                    if new_lot > 0:
                        if not st.session_state.dry_run:
                            order = self.place_order('buy', new_lot)
                            if order:
                                self.position = {
                                    'side': 'buy',
                                    'entry_price': current_price,
                                    'avg_price': current_price,
                                    'volume': new_lot
                                }
                                self.averaging_count = 0
                                self.is_reversed = True
                                self.reverse_count += 1
                                self.trailing_active = False
                                st.session_state.logs.append(f"✅ Переворот выполнен")
                                self._add_marker('entry', current_price, 'buy', datetime.now())
                        else:
                            self.position = {
                                'side': 'buy',
                                'entry_price': current_price,
                                'avg_price': current_price,
                                'volume': new_lot
                            }
                            self.averaging_count = 0
                            self.is_reversed = True
                            self.reverse_count += 1
                            self.trailing_active = False
                            st.session_state.logs.append(f"🧪 [DRY] Переворот выполнен")
                            self._add_marker('entry', current_price, 'buy', datetime.now())

# ============================================================
# ПРОСТАЯ СТРАТЕГИЯ (SMA-кроссовер) — ДЛЯ ПРИМЕРА
# ============================================================
class SMAStrategy(BaseStrategy):
    def __init__(self, exchange, symbol, config):
        super().__init__(exchange, symbol, config)
        self.position = None
        self.fast_period = config.get('fast_period', 10)
        self.slow_period = config.get('slow_period', 30)

    def tick(self):
        current_price = self.get_current_price()
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, st.session_state.timeframe, limit=50)
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
# ИНИЦИАЛИЗАЦИЯ СЕССИИ
# ============================================================
if 'mode' not in st.session_state:
    st.session_state.mode = 'demo'
if 'status' not in st.session_state:
    st.session_state.status = 'stopped'
if 'dry_run' not in st.session_state:
    st.session_state.dry_run = True
if 'logs' not in st.session_state:
    st.session_state.logs = []
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
if 'history_data' not in st.session_state:
    st.session_state.history_data = pd.DataFrame(columns=['time', 'symbol', 'side', 'volume', 'profit'])
if 'equity_data' not in st.session_state:
    st.session_state.equity_data = pd.DataFrame(columns=['time', 'equity'])
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = 'BTC/USDT'
if 'timeframe' not in st.session_state:
    st.session_state.timeframe = '1m'
if 'strategy' not in st.session_state:
    st.session_state.strategy = None
if 'exchange' not in st.session_state:
    st.session_state.exchange = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'ai_assistant' not in st.session_state:
    st.session_state.ai_assistant = DeepSeekAIAssistant()
if 'thread_started' not in st.session_state:
    st.session_state.thread_started = False
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = 'IATS'
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'markers' not in st.session_state:
    st.session_state.markers = []

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
STRATEGIES = ['IATS', 'SMA (простая)']
TIMEFRAMES = ['1m', '5m', '15m', '1h', '1d']

# ============================================================
# ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ (БЕЗ КЭШИРОВАНИЯ)
# ============================================================
def fetch_ohlcv(symbol, timeframe='1m', limit=150):
    try:
        exchange = ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        # Генерация демо-данных при отсутствии интернета
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
# ОСНОВНОЙ ИНТЕРФЕЙС
# ============================================================
st.markdown('<div class="main-header">🧠 HOVMEL v6.2 — РЕАЛЬНЫЙ ГРАФИК</div>', unsafe_allow_html=True)

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
    ai_status_text = "🧠 AI: ON" if st.session_state.ai_assistant.api_key else "🧠 AI: OFF"
    st.markdown(f'<div class="status-ai">{ai_status_text}</div>', unsafe_allow_html=True)

with col_status5:
    st.markdown(f'<div style="color:#888; font-size:14px;">{st.session_state.selected_symbol}</div>', unsafe_allow_html=True)

with col_status6:
    st.markdown(f'<div style="text-align:right;color:#888;">{datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# Выбор инструмента, таймфрейма и стратегии
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
    # Загружаем данные с выбранным таймфреймом (без кэша)
    df = fetch_ohlcv(st.session_state.selected_symbol, st.session_state.timeframe, limit=150)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                         row_heights=[0.7, 0.3], subplot_titles=(f'{st.session_state.selected_symbol} ({st.session_state.timeframe})', 'Объём'))
    fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                                   name=st.session_state.selected_symbol, increasing_line_color='#00ff88', decreasing_line_color='#ff4444'), row=1, col=1)
    # SMA
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma20'], line=dict(color='#ffaa00', width=1.5), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma50'], line=dict(color='#4488ff', width=1.5), name='SMA 50'), row=1, col=1)

    # Отображаем маркеры позиций из сессии
    if 'markers' in st.session_state and st.session_state.markers:
        entry_buy_x = []
        entry_buy_y = []
        entry_sell_x = []
        entry_sell_y = []
        exit_x = []
        exit_y = []
        for m in st.session_state.markers:
            if m['type'] == 'entry':
                if m['side'] == 'buy':
                    entry_buy_x.append(m['time'])
                    entry_buy_y.append(m['price'])
                else:
                    entry_sell_x.append(m['time'])
                    entry_sell_y.append(m['price'])
            else:  # exit
                exit_x.append(m['time'])
                exit_y.append(m['price'])
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

    # Текущая позиция (линии)
    if st.session_state.position:
        entry_price = st.session_state.position.get('entry_price', 0)
        avg_price = st.session_state.position.get('avg_price', entry_price)
        fig.add_hline(y=entry_price, line=dict(color='#ffd700', width=1, dash='dash'), annotation_text=f'Entry: {entry_price:.1f}', annotation_position='top left', row=1, col=1)
        fig.add_hline(y=avg_price, line=dict(color='#ff8800', width=1.5, dash='dashdot'), annotation_text=f'Avg: {avg_price:.1f}', annotation_position='bottom left', row=1, col=1)

    fig.add_trace(go.Bar(x=df['timestamp'], y=df['volume'], name='Volume', marker_color='#4466aa', opacity=0.6), row=2, col=1)
    fig.update_layout(template='plotly_dark', height=550, showlegend=True, hovermode='x unified',
                      paper_bgcolor='#0d0d1a', plot_bgcolor='#0d0d1a', margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    fig.update_xaxes(gridcolor='#1a1a2e', showgrid=True)
    fig.update_yaxes(gridcolor='#1a1a2e', showgrid=True)
    st.plotly_chart(fig, use_container_width=True, key="live_chart")

    # Панель управления
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
                            'apiKey': api_key,
                            'secret': secret,
                            'password': passphrase,
                            'enableRateLimit': True,
                            'options': {'defaultType': 'spot' if st.session_state.mode == 'demo' else 'future'}
                        })
                        st.session_state.logs.append("🔑 Подключение с API-ключами OKX")
                    else:
                        exchange = ccxt.okx({
                            'enableRateLimit': True,
                            'options': {'defaultType': 'spot'}
                        })
                        st.session_state.logs.append("🌐 Публичный доступ (без API-ключей) — только симуляция")
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
                    elif st.session_state.selected_strategy == 'SMA (простая)':
                        sma_config = {'lot': config.get('max_lot', 0.01), 'fast_period': 10, 'slow_period': 30}
                        st.session_state.strategy = SMAStrategy(exchange, st.session_state.selected_symbol, sma_config)
                    else:
                        st.error(f"Неизвестная стратегия: {st.session_state.selected_strategy}")
                        st.stop()
                    
                    # Убедимся, что баланс установлен
                    if not api_key:
                        st.session_state.balance = st.session_state.demo_balance
                    else:
                        st.session_state.balance = st.session_state.strategy.get_balance('USDT')
                    
                    st.session_state.running = True
                    st.session_state.status = 'running'
                    st.session_state.logs.append(f"🚀 Бот запущен на {st.session_state.selected_symbol} (стратегия: {st.session_state.selected_strategy}, режим: {'Dry Run' if st.session_state.dry_run else 'Реальный'})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка: {e}")
    with col2:
        if st.button("⏹ СТОП", use_container_width=True):
            st.session_state.running = False
            st.session_state.status = 'stopped'
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

    # Метрики
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">💰 Баланс USDT</div><div class="metric-value metric-green">{st.session_state.balance:.2f}</div></div>', unsafe_allow_html=True)
    with col_m2:
        color = 'metric-green' if st.session_state.pnl >= 0 else 'metric-red'
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">📈 P&L</div><div class="metric-value {color}">{st.session_state.pnl:.2f} USDT</div></div>', unsafe_allow_html=True)
    with col_m3:
        pos_text = f"{st.session_state.position['side'].upper()} {st.session_state.position['volume']:.3f}" if st.session_state.position else "—"
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">📊 Позиция</div><div class="metric-value metric-gold">{pos_text}</div></div>', unsafe_allow_html=True)
    with col_m4:
        price_text = f"{st.session_state.current_price:.1f}" if st.session_state.current_price else "—"
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">💹 Цена</div><div class="metric-value metric-blue">{price_text}</div></div>', unsafe_allow_html=True)
    with col_m5:
        ai_status = "Активен" if st.session_state.ai_assistant.api_key else "Неактивен"
        st.markdown(f'<div class="metric-card"><div style="color:#888;font-size:14px;">🧠 AI</div><div class="metric-value metric-purple">{ai_status}</div></div>', unsafe_allow_html=True)

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
'HOVMEL IATS — ШЕДЕВР v6.2 | Баланс 3000 USDT | Реальный график | Маркеры позиций | '
'MT5-интерфейс | Поддержка нескольких инструментов | © 2024 HOVMEL Trading Systems'
'</div>',
unsafe_allow_html=True
)
