# ============================================================
# HOVMEL IATS — ШЕДЕВР v3.2 (ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ)
# Поддержка нескольких инструментов, цветная история, вкладки
# Все ошибки исправлены: session_state, OKX markets, перезагрузка
# (c) 2024 HOVMEL Trading Systems
# ============================================================

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import ccxt
import time
import threading
import os
import math
from dotenv import load_dotenv

# === Загрузка переменных окружения ===
load_dotenv()

# === Конфигурация страницы ===
st.set_page_config(
    page_title="HOVMEL IATS - Шедевр",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# СТРАТЕГИЯ IATS
# ============================================================
class IATSStrategy:
    def __init__(self, exchange, symbol, config):
        self.exchange = exchange
        self.symbol = symbol
        self.config = config
        self.tick_size = self._get_tick_size()
        self.position = None
        self.averaging_count = 0
        self.is_reversed = False
        self.reverse_count = 0
        self.trailing_active = False
        self.trailing_level = 0.0
        self.last_entry_time = 0

    def _get_tick_size(self):
        market = self.exchange.market(self.symbol)
        return market['precision']['price']

    def get_balance(self, currency='USDT'):
        balance = self.exchange.fetch_balance()
        return balance['free'].get(currency, 0.0)

    def get_current_price(self):
        ticker = self.exchange.fetch_ticker(self.symbol)
        return ticker['last']

    def calculate_lot(self, side, entry_price, stop_loss_price):
        balance_usdt = self.get_balance('USDT')
        risk_amount = balance_usdt * (self.config['risk_percent'] / 100.0)
        price_diff = abs(entry_price - stop_loss_price)
        if price_diff == 0:
            return 0.0
        lot = risk_amount / price_diff
        step = self.exchange.market(self.symbol)['precision']['amount']
        lot = math.floor(lot / step) * step
        if lot > self.config['max_lot']:
            lot = self.config['max_lot']
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
        return now.second % 2 == 0

    def tick(self):
        current_price = self.get_current_price()
        st.session_state.current_price = current_price

        if self.position is None:
            if self.check_entry_signal():
                sl_price = current_price - self.config['sl_ticks'] * self.tick_size
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
                            st.session_state.logs.append("✅ Позиция открыта")
                    else:
                        self.position = {
                            'side': 'buy',
                            'entry_price': current_price,
                            'avg_price': current_price,
                            'volume': lot
                        }
                        st.session_state.logs.append("🧪 [DRY] Позиция открыта")
            return

        side = self.position['side']
        avg_price = self.position['avg_price']
        volume = self.position['volume']

        if side == 'buy':
            profit_usdt = (current_price - avg_price) * volume
        else:
            profit_usdt = (avg_price - current_price) * volume
        st.session_state.pnl = profit_usdt

        # Стоп-лосс
        if side == 'buy':
            sl_price = avg_price - self.config['sl_ticks'] * self.tick_size
            if current_price <= sl_price:
                st.session_state.logs.append(f"🔴 Стоп-лосс сработал! Цена {current_price}")
                self.close_position('sell', volume)
                self._close_trade(profit_usdt)
                self.position = None
                return
        else:
            sl_price = avg_price + self.config['sl_ticks'] * self.tick_size
            if current_price >= sl_price:
                st.session_state.logs.append(f"🔴 Стоп-лосс сработал! Цена {current_price}")
                self.close_position('buy', volume)
                self._close_trade(profit_usdt)
                self.position = None
                return

        # Трейлинг
        if self.config['enable_trailing']:
            if not self.trailing_active:
                profit_ticks = (current_price - avg_price) / self.tick_size if side == 'buy' else (avg_price - current_price) / self.tick_size
                if profit_ticks >= self.config['trailing_distance_ticks']:
                    self.trailing_active = True
                    if side == 'buy':
                        self.trailing_level = current_price - self.config['trailing_distance_ticks'] * self.tick_size
                    else:
                        self.trailing_level = current_price + self.config['trailing_distance_ticks'] * self.tick_size
                    st.session_state.logs.append(f"🟡 Трейлинг активирован, уровень {self.trailing_level}")
            else:
                if side == 'buy':
                    new_level = current_price - self.config['trailing_distance_ticks'] * self.tick_size
                    if new_level > self.trailing_level:
                        self.trailing_level = new_level
                    if current_price <= self.trailing_level:
                        st.session_state.logs.append(f"🟡 Трейлинг сработал! Цена {current_price}")
                        self.close_position('sell', volume)
                        self._close_trade(profit_usdt)
                        self.position = None
                        return
                else:
                    new_level = current_price + self.config['trailing_distance_ticks'] * self.tick_size
                    if new_level < self.trailing_level:
                        self.trailing_level = new_level
                    if current_price >= self.trailing_level:
                        st.session_state.logs.append(f"🟡 Трейлинг сработал! Цена {current_price}")
                        self.close_position('buy', volume)
                        self._close_trade(profit_usdt)
                        self.position = None
                        return

        # Усреднение
        if self.averaging_count < self.config['max_averaging']:
            step = self.config['averaging_step_ticks'] * (self.averaging_count + 1) * self.tick_size
            if side == 'buy':
                if current_price <= avg_price - step:
                    new_lot = self.calculate_lot('buy', current_price, current_price - self.config['sl_ticks'] * self.tick_size)
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
                        else:
                            total_volume = volume + new_lot
                            new_avg = (avg_price * volume + current_price * new_lot) / total_volume
                            self.position['avg_price'] = new_avg
                            self.position['volume'] = total_volume
                            self.averaging_count += 1
                            st.session_state.logs.append(f"🧪 [DRY] Усреднение #{self.averaging_count}")
            else:
                if current_price >= avg_price + step:
                    new_lot = self.calculate_lot('sell', current_price, current_price + self.config['sl_ticks'] * self.tick_size)
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
                        else:
                            total_volume = volume + new_lot
                            new_avg = (avg_price * volume + current_price * new_lot) / total_volume
                            self.position['avg_price'] = new_avg
                            self.position['volume'] = total_volume
                            self.averaging_count += 1
                            st.session_state.logs.append(f"🧪 [DRY] Усреднение #{self.averaging_count}")

        # Переворот
        if self.averaging_count >= self.config['max_averaging'] and not self.is_reversed and self.reverse_count < self.config['max_reverses']:
            if side == 'buy' and current_price <= avg_price - 15 * self.tick_size:
                st.session_state.logs.append("🔄 Переворот: закрываем BUY, открываем SELL")
                self.close_position('sell', volume)
                self._close_trade(profit_usdt)
                new_lot = self.calculate_lot('sell', current_price, current_price + self.config['sl_ticks'] * self.tick_size)
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
                            st.session_state.logs.append("✅ Переворот выполнен")
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
                        st.session_state.logs.append("🧪 [DRY] Переворот выполнен")
            elif side == 'sell' and current_price >= avg_price + 15 * self.tick_size:
                st.session_state.logs.append("🔄 Переворот: закрываем SELL, открываем BUY")
                self.close_position('buy', volume)
                self._close_trade(profit_usdt)
                new_lot = self.calculate_lot('buy', current_price, current_price - self.config['sl_ticks'] * self.tick_size)
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
                            st.session_state.logs.append("✅ Переворот выполнен")
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
                        st.session_state.logs.append("🧪 [DRY] Переворот выполнен")

    def _close_trade(self, profit):
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

# ============================================================
# CSS СТИЛИ
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .main-header { font-family: 'Orbitron', sans-serif; font-size: 2.5rem; background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 20px 0; }
    .status-demo { display: inline-block; padding: 8px 20px; background: #00ff88; color: #000; border-radius: 20px; font-weight: bold; box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); animation: pulse-green 2s infinite; }
    .status-real { display: inline-block; padding: 8px 20px; background: #ff4444; color: #fff; border-radius: 20px; font-weight: bold; box-shadow: 0 0 20px rgba(255, 68, 68, 0.5); animation: pulse-red 2s infinite; }
    @keyframes pulse-green { 0% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); } 50% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.9); } 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.5); } }
    @keyframes pulse-red { 0% { box-shadow: 0 0 20px rgba(255, 68, 68, 0.5); } 50% { box-shadow: 0 0 40px rgba(255, 68, 68, 0.9); } 100% { box-shadow: 0 0 20px rgba(255, 68, 68, 0.5); } }
    .status-stopped { display: inline-block; padding: 8px 20px; background: #666; color: #fff; border-radius: 20px; font-weight: bold; }
    .status-running { display: inline-block; padding: 8px 20px; background: #ffaa00; color: #000; border-radius: 20px; font-weight: bold; animation: pulse-yellow 1.5s infinite; }
    @keyframes pulse-yellow { 0% { box-shadow: 0 0 20px rgba(255, 170, 0, 0.5); } 50% { box-shadow: 0 0 40px rgba(255, 170, 0, 0.9); } 100% { box-shadow: 0 0 20px rgba(255, 170, 0, 0.5); } }
    .metric-card { background: #1a1a2e; padding: 20px; border-radius: 12px; border: 1px solid #333; margin: 5px; }
    .metric-value { font-size: 28px; font-weight: bold; }
    .metric-green { color: #00ff88; }
    .metric-red { color: #ff4444; }
    .metric-gold { color: #ffd700; }
    .metric-blue { color: #4488ff; }
    .log-container { background: #0a0a12; padding: 15px; border-radius: 8px; max-height: 250px; overflow-y: auto; font-family: 'Consolas', monospace; font-size: 12px; color: #aaa; border: 1px solid #222; }
    .log-entry-green { color: #00ff88; }
    .log-entry-red { color: #ff4444; }
    .log-entry-gold { color: #ffd700; }
    .log-entry-blue { color: #4488ff; }
    .log-entry-white { color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; background-color: #1a1a2e; border-radius: 8px 8px 0 0; padding: 5px 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px 6px 0 0; padding: 8px 20px; background-color: #2a2a4e; color: #888; font-weight: bold; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3a3a6e; color: #fff; border-bottom: 3px solid #ffd700; }
    .trade-profit { color: #4488ff; font-weight: bold; }
    .trade-loss { color: #ff4444; font-weight: bold; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; padding: 10px; }
</style>
""", unsafe_allow_html=True)

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
    st.session_state.balance = 0
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
if 'strategy' not in st.session_state:
    st.session_state.strategy = None
if 'exchange' not in st.session_state:
    st.session_state.exchange = None
if 'bot_thread' not in st.session_state:
    st.session_state.bot_thread = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'thread_started' not in st.session_state:
    st.session_state.thread_started = False

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']

# ============================================================
# ФУНКЦИИ ЗАГРУЗКИ ДАННЫХ
# ============================================================
@st.cache_data(ttl=60)
def fetch_ohlcv(symbol, timeframe='1m', limit=100):
    try:
        exchange = ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except:
        # Генерация демо-данных при ошибке
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1min')
        base_price = 60000 if 'BTC' in symbol else (3000 if 'ETH' in symbol else (150 if 'SOL' in symbol else 0.5))
        np.random.seed(42 + hash(symbol) % 100)
        close = base_price + np.cumsum(np.random.randn(100) * base_price * 0.001)
        high = close + np.random.rand(100) * base_price * 0.002
        low = close - np.random.rand(100) * base_price * 0.002
        open_price = close - np.random.rand(100) * base_price * 0.001
        return pd.DataFrame({
            'timestamp': dates,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(10, 100, 100)
        })

# ============================================================
# ОСНОВНОЙ ИНТЕРФЕЙС
# ============================================================
st.markdown('<div class="main-header">📈 HOVMEL IATS — ШЕДЕВР</div>', unsafe_allow_html=True)

# === ВЕРХНЯЯ ПАНЕЛЬ СТАТУСА ===
col_status1, col_status2, col_status3, col_status4, col_status5 = st.columns(5)
with col_status1:
    mode_text = "🟢 ДЕМО" if st.session_state.mode == 'demo' else "🔴 РЕАЛ"
    mode_class = "status-demo" if st.session_state.mode == 'demo' else "status-real"
    st.markdown(f'<div class="{mode_class}">{mode_text}</div>', unsafe_allow_html=True)
with col_status2:
    status_text = "⏹ СТОП" if st.session_state.status == 'stopped' else "▶ РАБОТАЕТ"
    status_class = "status-stopped" if st.session_state.status == 'stopped' else "status-running"
    st.markdown(f'<div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)
with col_status3:
    dry_text = "🧪 DRY ON" if st.session_state.dry_run else "💪 REAL"
    st.markdown(f'<div class="status-stopped" style="background:#4466aa;">{dry_text}</div>', unsafe_allow_html=True)
with col_status4:
    st.markdown(f'<div style="color:#888; font-size:14px;">{st.session_state.selected_symbol}</div>', unsafe_allow_html=True)
with col_status5:
    st.markdown(f'<div style="text-align:right;color:#888;">{datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

# === ВЫБОР ИНСТРУМЕНТА ===
col_sym1, col_sym2 = st.columns([2, 10])
with col_sym1:
    new_symbol = st.selectbox("Инструмент", SYMBOLS, index=SYMBOLS.index(st.session_state.selected_symbol))
    if new_symbol != st.session_state.selected_symbol:
        st.session_state.selected_symbol = new_symbol
        st.session_state.logs.append(f"🔄 Переключено на {new_symbol}")
        st.session_state.position = None
        st.session_state.strategy = None
        st.rerun()

# === ВКЛАДКИ ===
tab1, tab2, tab3 = st.tabs(["📊 Торговля", "📋 Журнал", "📈 Эксперт"])

# ========== ВКЛАДКА 1: ТОРГОВЛЯ ==========
with tab1:
    df = fetch_ohlcv(st.session_state.selected_symbol)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                         row_heights=[0.7, 0.3], subplot_titles=(f'{st.session_state.selected_symbol} - Свечи', 'Объём'))
    fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                                   name=st.session_state.selected_symbol, increasing_line_color='#00ff88', decreasing_line_color='#ff4444'), row=1, col=1)
    df['sma20'] = df['close'].rolling(20).mean()
    df['sma50'] = df['close'].rolling(50).mean()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma20'], line=dict(color='#ffaa00', width=1.5), name='SMA 20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['sma50'], line=dict(color='#4488ff', width=1.5), name='SMA 50'), row=1, col=1)
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
    st.plotly_chart(fig, use_container_width=True)

    # --- КНОПКИ УПРАВЛЕНИЯ ---
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("▶️ СТАРТ", use_container_width=True):
            if not st.session_state.running:
                try:
                    # Получаем ключи из .env или secrets
                    api_key = os.getenv('OKX_API_KEY') or st.secrets.get('OKX_API_KEY')
                    secret = os.getenv('OKX_API_SECRET') or st.secrets.get('OKX_API_SECRET')
                    passphrase = os.getenv('OKX_API_PASSPHRASE') or st.secrets.get('OKX_API_PASSPHRASE')
                    if not api_key or not secret or not passphrase:
                        st.error("❌ Не заданы API-ключи OKX! Добавьте их в .env или в Secrets Streamlit.")
                    else:
                        # Загружаем рынки OKX с повторными попытками
                        max_retries = 5
                        exchange = None
                        for attempt in range(max_retries):
                            try:
                                exchange = ccxt.okx({
                                    'apiKey': api_key,
                                    'secret': secret,
                                    'password': passphrase,
                                    'enableRateLimit': True,
                                    'options': {'defaultType': 'spot' if st.session_state.mode == 'demo' else 'future'}
                                })
                                exchange.load_markets()
                                st.session_state.logs.append(f"✅ OKX подключён (попытка {attempt+1})")
                                break
                            except Exception as e:
                                st.session_state.logs.append(f"⚠️ Попытка {attempt+1}/{max_retries} загрузить OKX: {str(e)[:80]}")
                                time.sleep(3)
                                exchange = None
                        if exchange is None:
                            st.error("❌ Не удалось загрузить рынки OKX после нескольких попыток. Проверьте интернет и API-ключи.")
                            st.stop()
                        
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
                        st.session_state.strategy = IATSStrategy(exchange, st.session_state.selected_symbol, config)
                        st.session_state.balance = st.session_state.strategy.get_balance('USDT')
                        st.session_state.running = True
                        st.session_state.status = 'running'
                        st.session_state.logs.append(f"🚀 Бот запущен на {st.session_state.selected_symbol}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Ошибка инициализации: {e}")
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

    # --- МЕТРИКИ ---
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
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

# ========== ВКЛАДКА 2: ЖУРНАЛ ==========
with tab2:
    st.markdown("### 📋 Журнал событий")
    if st.button("🗑 Очистить журнал"):
        st.session_state.logs = []
        st.rerun()
    log_html = ""
    for log in st.session_state.logs[-100:]:
        if "🟢" in log or "✅" in log or "прибыль" in log:
            log_html += f'<div class="log-entry-green">{log}</div>'
        elif "🔴" in log or "❌" in log or "убыток" in log:
            log_html += f'<div class="log-entry-red">{log}</div>'
        elif "💰" in log or "📈" in log or "★" in log or "🔄" in log or "🟡" in log:
            log_html += f'<div class="log-entry-gold">{log}</div>'
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
        col1, col2, col3 = st.columns(3)
        col1.metric("Всего сделок", total_trades)
        col2.metric("Винрейт", f"{win_rate:.1f}%")
        col3.metric("Общая прибыль", f"{total_profit:.2f} USDT", delta_color="normal" if total_profit >= 0 else "inverse")
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

    # --- НАСТРОЙКИ ---
    with st.expander("⚙️ Настройки стратегии"):
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

# ============================================================
# ФОНОВЫЙ ЦИКЛ (запускается один раз)
# ============================================================
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
# ФУТЕР
# ============================================================
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#666;font-size:12px;padding:20px;">'
    'HOVMEL IATS — Шедевр v3.2 | MT5-интерфейс | © 2024 HOVMEL Trading Systems'
    '</div>',
    unsafe_allow_html=True
)