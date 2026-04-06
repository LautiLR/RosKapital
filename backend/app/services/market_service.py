"""
Servicio de datos de mercado con caché
"""
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import logging

from app.cache import cache_get, cache_set
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================
# STOCKS DATA
# ============================================

def get_stock_data(ticker: str) -> Optional[Dict]:
    """Obtiene datos de una acción individual con % de cambio correcto"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")  # Obtener últimos 5 días
        
        if hist.empty:
            logger.warning(f"No hay datos históricos para {ticker}")
            return None
        
        # Precio actual (último cierre)
        current_price = hist['Close'].iloc[-1]
        
        # Calcular cambio % correctamente usando el cierre anterior
        if len(hist) >= 2:
            # Usar el cierre del día anterior
            previous_close = hist['Close'].iloc[-2]
            change_pct = ((current_price - previous_close) / previous_close) * 100
        else:
            # Si solo hay 1 día de datos, usar el open del mismo día
            previous_close = hist['Open'].iloc[0]
            change_pct = ((current_price - previous_close) / previous_close) * 100
            
        rsi_value = None
        if len(hist) >= 15: 
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            rsi_value = round(float(rsi_series.iloc[-1]), 1)
        
        return {
            'ticker': ticker,
            'nombre': info.get('longName', ticker),
            'precio': round(float(current_price), 2),
            'cambio': round(float(change_pct), 2),
            'volumen': int(info.get('volume', 0)),
            'marketCap': info.get('marketCap', 0),
            'sector': info.get('sector', 'N/A'),
            'pais': 'ARG' if ticker.endswith('.BA') else 'USA',
            'rsi': rsi_value
        }
    except Exception as e:
        logger.error(f"Error obteniendo datos de {ticker}: {e}")
        return None


def get_multiple_stocks(tickers: List[str]) -> List[Dict]:
    """Obtiene datos de múltiples acciones en paralelo"""
    
    # Intentar obtener del caché
    cache_key = f"stocks:{'_'.join(sorted(tickers))}"
    cached_data = cache_get(cache_key)
    
    if cached_data:
        logger.info(f"Datos de stocks obtenidos del caché")
        return cached_data
    
    logger.info(f"Obteniendo datos frescos de {len(tickers)} stocks...")
    
    # Obtener en paralelo
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_stock_data, tickers))
    
    # Filtrar None
    stocks = [r for r in results if r is not None]
    
    # Guardar en caché por 5 minutos
    cache_set(cache_key, stocks, expire=300)
    
    return stocks


# ============================================
# CRYPTO DATA
# ============================================

def get_crypto_data(ticker: str) -> Optional[Dict]:
    """Obtiene datos de una criptomoneda con % de cambio correcto"""
    try:
        crypto = yf.Ticker(ticker)
        hist = crypto.history(period="5d")  # Obtener últimos 5 días
        
        # Si no hay datos históricos, skip esta crypto
        if hist.empty:
            logger.warning(f"No hay datos históricos para {ticker}")
            return None
        
        # Obtener precio actual
        current_price = hist['Close'].iloc[-1]
        
        # Calcular cambio 24h correctamente
        if len(hist) >= 2:
            # Usar el cierre del día anterior (correcto)
            previous_close = hist['Close'].iloc[-2]
            change_24h = ((current_price - previous_close) / previous_close) * 100
        else:
            # Fallback: usar open del día actual
            if hist['Open'].iloc[0] > 0:
                change_24h = ((current_price - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
            else:
                change_24h = 0.0
        
        # Symbol limpio (sin -USD)
        symbol = ticker.replace('-USD', '').replace('USDT', 'USDT')
        
        # Intentar obtener info adicional (puede fallar)
        market_cap = 0
        volume = 0
        name = symbol
        
        try:
            info = crypto.info
            market_cap = info.get('marketCap', 0)
            volume = info.get('volume', 0)
            name = info.get('name', symbol)
        except Exception as info_error:
            logger.debug(f"No se pudo obtener info de {ticker}: {info_error}")
        
        return {
            'ticker': ticker,
            'nombre': name,
            'simbolo': symbol,
            'precio': round(float(current_price), 2),
            'cambio24h': round(float(change_24h), 2),
            'volumen24h': int(volume) if volume else 0,
            'marketCap': market_cap if market_cap else 0,
            'dominance': None
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de {ticker}: {str(e)}")
        return None


def get_crypto_market_data() -> Dict:
    """Obtiene datos del mercado crypto completo"""
    
    # Intentar obtener del caché
    cached_data = cache_get("crypto:market_data")
    if cached_data:
        logger.info("Datos de crypto obtenidos del caché")
        return cached_data
    
    logger.info("Obteniendo datos frescos de cryptos...")
    
    # Top cryptos (solo las más confiables en yfinance)
    crypto_tickers = [
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD',
        'XRP-USD', 'ADA-USD', 'DOGE-USD', 'DOT-USD',
        'LINK-USD', 'AVAX-USD', 'ATOM-USD',
        'LTC-USD', 'ETC-USD', 'BCH-USD',
        'ALGO-USD', 'FIL-USD', 'ICP-USD', 'NEAR-USD'
    ]
    
    # Obtener datos en paralelo
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_crypto_data, crypto_tickers))
    
    # Filtrar None (cryptos que fallaron)
    cryptos = [r for r in results if r is not None]
    
    logger.info(f"Cryptos cargadas exitosamente: {len(cryptos)}/{len(crypto_tickers)}")
    
    # Si no se pudo cargar ninguna crypto, retornar datos vacíos
    if len(cryptos) == 0:
        logger.error("No se pudo cargar ninguna criptomoneda")
        return {
            'stats': {
                'totalMarketCap': 0,
                'totalVolume': 0,
                'btcDominance': 0,
                'fearGreed': 50
            },
            'cryptos': []
        }
    
    # Calcular stats globales
    total_market_cap = sum(c['marketCap'] for c in cryptos if c['marketCap'])
    total_volume = sum(c['volumen24h'] for c in cryptos if c['volumen24h'])
    
    # BTC Dominance
    btc_market_cap = next((c['marketCap'] for c in cryptos if c['simbolo'] == 'BTC'), 0)
    btc_dominance = round((btc_market_cap / total_market_cap * 100), 1) if total_market_cap > 0 else 0
    
    # Agregar dominance a BTC y ETH
    for crypto in cryptos:
        if crypto['simbolo'] == 'BTC':
            crypto['dominance'] = btc_dominance
        elif crypto['simbolo'] == 'ETH':
            eth_dominance = round((crypto['marketCap'] / total_market_cap * 100), 1) if total_market_cap > 0 else 0
            crypto['dominance'] = eth_dominance
    
    # Preparar respuesta
    data = {
        'stats': {
            'totalMarketCap': total_market_cap,
            'totalVolume': total_volume,
            'btcDominance': btc_dominance,
            'fearGreed': 50  # Placeholder - integrar Fear & Greed Index API si quieres
        },
        'cryptos': cryptos
    }
    
    # Cachear por 5 minutos
    cache_set("crypto:market_data", data, expire=300)
    logger.info(f"Datos de crypto cacheados por 5 minutos")
    
    return data


# ============================================
# INDICES
# ============================================

def get_market_indices() -> List[Dict]:
    """Obtiene datos de índices principales"""
    
    # Intentar caché
    cached_data = cache_get("indices:main")
    if cached_data:
        return cached_data
    
    indices_tickers = ['SPY', 'DIA', 'QQQ', 'IWM']
    indices_names = {
        'SPY': 'S&P 500',
        'DIA': 'Dow Jones',
        'QQQ': 'Nasdaq 100',
        'IWM': 'Russell 2000'
    }
    
    def get_index_data(ticker):
        try:
            index = yf.Ticker(ticker)
            hist = index.history(period="1d")
            
            if hist.empty:
                return None
            
            price = hist['Close'].iloc[-1]
            change = ((price - hist['Open'].iloc[0]) / hist['Open'].iloc[0]) * 100
            
            # Volumen del día
            volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
            
            return {
                't': ticker,
                'n': indices_names.get(ticker, ticker),
                'p': round(float(price), 2),
                'v': round(float(change), 2),
                'vol': volume
            }
        except Exception as e:
            logger.error(f"Error obteniendo índice {ticker}: {e}")
            return None
    
    # Obtener en paralelo
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(get_index_data, indices_tickers))
    
    indices = [r for r in results if r is not None]
    
    # Cachear por 5 minutos
    cache_set("indices:main", indices, expire=300)
    
    return indices


# ============================================
# TOP MOVERS
# ============================================

def get_top_movers() -> Dict:
    """Obtiene las acciones con mayor movimiento del día"""
    
    # Intentar caché
    cached_data = cache_get("movers:daily")
    if cached_data:
        return cached_data
    
    # Lista de acciones populares para analizar
    popular_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD',
        'NFLX', 'DIS', 'BA', 'INTC', 'CSCO', 'ORCL', 'IBM', 'QCOM'
    ]
    
    stocks_data = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_stock_data, popular_tickers))
    
    stocks_data = [r for r in results if r is not None]
    
    # Ordenar por cambio porcentual
    sorted_stocks = sorted(stocks_data, key=lambda x: x['cambio'], reverse=True)
    
    data = {
        'gainers': sorted_stocks[:3],  # Top 3 subas
        'losers': sorted_stocks[-3:][::-1]  # Top 3 bajas
    }
    
    # Cachear por 10 minutos
    cache_set("movers:daily", data, expire=600)
    
    return data


# ============================================
# HEATMAP DATA
# ============================================

def get_heatmap_data(market: str = "sp500") -> List[Dict]:
    """Obtiene datos para el heatmap"""
    
    cache_key = f"heatmap:{market}"
    cached_data = cache_get(cache_key)
    if cached_data:
        return cached_data
    
    # SP500 top stocks por sector
    sp500_tickers = {
        'Tech': ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'AVGO', 'CSCO', 'ADBE', 'CRM', 'INTC'],
        'Financiero': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'AXP', 'USB'],
        'Salud': ['UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'PFE', 'BMY'],
        'Consumo': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TGT', 'TJX', 'DG'],
        'Energía': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PXD', 'MPC', 'PSX', 'VLO', 'OXY']
    }
    
    heatmap_data = []
    
    for sector, tickers in sp500_tickers.items():
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(get_stock_data, tickers))
        
        for stock in results:
            if stock:
                heatmap_data.append({
                    'ticker': stock['ticker'],
                    'nombre': stock['nombre'],
                    'sector': sector,
                    'marketCap': stock['marketCap'],
                    'cambio': stock['cambio'],
                    'precio': stock['precio']
                })
    
    # Cachear por 10 minutos
    cache_set(cache_key, heatmap_data, expire=600)
    
    return heatmap_data


# ============================================
# TECHNICAL INDICATORS
# ============================================

def calculate_rsi(ticker: str, period: int = 14) -> Optional[float]:
    """Calcula RSI de un ticker"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        if len(hist) < period:
            return None
        
        # Calcular cambios
        delta = hist['Close'].diff()
        
        # Ganancias y pérdidas
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(float(rsi.iloc[-1]), 2)
    except Exception as e:
        logger.error(f"Error calculando RSI para {ticker}: {e}")
        return None


def get_technical_indicators(ticker: str) -> Dict:
    """Obtiene indicadores técnicos de un ticker"""
    
    cache_key = f"indicators:{ticker}"
    cached_data = cache_get(cache_key)
    if cached_data:
        return cached_data
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if len(hist) < 50:
            return {}
        
        close = hist['Close']
        high = hist['High']
        low = hist['Low']
        
        # RSI
        rsi = calculate_rsi(ticker)
        
        # Medias móviles
        sma20 = close.rolling(window=20).mean().iloc[-1]
        ma50 = close.rolling(window=50).mean().iloc[-1]
        ma200 = close.rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None
        
        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_histogram = macd_line - signal_line
        
        macd_val = round(float(macd_line.iloc[-1]), 2)
        signal_val = round(float(signal_line.iloc[-1]), 2)
        histogram_val = round(float(macd_histogram.iloc[-1]), 2)
        
        # Bollinger Bands (20, 2)
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        current_price = close.iloc[-1]
        bb_position = None
        if bb_upper.iloc[-1] != bb_lower.iloc[-1]:
            bb_position = round(((current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100, 1)
        
        # ATR (14)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        atr_pct = round((atr / current_price) * 100, 2)
        
        # Soporte/Resistencia (últimos 3 meses)
        recent = hist.tail(60)
        support = recent['Low'].min()
        resistance = recent['High'].max()
        
        indicators = {
            'rsi': round(float(rsi), 2) if rsi else None,
            'sma20': round(float(sma20), 2),
            'ma50': round(float(ma50), 2),
            'ma200': round(float(ma200), 2) if ma200 else None,
            'macd': macd_val,
            'macdSignal': signal_val,
            'macdHistogram': histogram_val,
            'bbUpper': round(float(bb_upper.iloc[-1]), 2),
            'bbMiddle': round(float(bb_middle.iloc[-1]), 2),
            'bbLower': round(float(bb_lower.iloc[-1]), 2),
            'bbPosition': bb_position,
            'atr': round(float(atr), 2),
            'atrPercent': atr_pct,
            'support': round(float(support), 2),
            'resistance': round(float(resistance), 2)
        }
        
        # Cachear por 30 minutos
        cache_set(cache_key, indicators, expire=1800)
        
        return indicators
        
    except Exception as e:
        logger.error(f"Error obteniendo indicadores para {ticker}: {e}")
        return {}


# ============================================
# SECCIONES MERCADO: USA / CEDEARs / ARG
# ============================================

# 75 acciones del S&P500 por sector
SP500_TICKERS = [
    # Tech (20)
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'AMZN', 'TSLA', 'AMD',
    'AVGO', 'ORCL', 'CRM', 'ADBE', 'INTC', 'QCOM', 'IBM', 'CSCO',
    'TXN', 'NOW', 'AMAT', 'MU',
    # Financiero (15)
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW',
    'AXP', 'USB', 'PNC', 'COF', 'TFC', 'BK', 'STT',
    # Salud (15)
    'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT',
    'DHR', 'PFE', 'BMY', 'AMGN', 'GILD', 'VRTX', 'REGN', 'ISRG',
    # Consumo (15)
    'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TGT', 'TJX',
    'DG', 'COST', 'WMT', 'PG', 'KO', 'PEP', 'PM', 'MO',
    # Energía / Otros (10)
    'XOM', 'CVX', 'COP', 'SLB', 'EOG',
    'NFLX', 'DIS', 'BA', 'CAT', 'GE'
]

# 50 CEDEARs más operados en Argentina con sus ratios de conversión
# ratio = cuántas acciones locales equivalen a 1 acción en NYSE
CEDEARS_DATA = {
    'AAPL':  {'ratio': 20,  'nombre': 'Apple Inc.'},
    'MSFT':  {'ratio': 30,  'nombre': 'Microsoft Corp.'},
    'GOOGL': {'ratio': 58,  'nombre': 'Alphabet Inc.'},
    'AMZN':  {'ratio': 144, 'nombre': 'Amazon.com Inc.'},
    'NVDA':  {'ratio': 24,  'nombre': 'NVIDIA Corp.'},
    'TSLA':  {'ratio': 15,  'nombre': 'Tesla Inc.'},
    'META':  {'ratio': 24,  'nombre': 'Meta Platforms'},
    'AMD':   {'ratio': 10,  'nombre': 'Advanced Micro Devices'},
    'NFLX':  {'ratio': 48,  'nombre': 'Netflix Inc.'},
    'BABA':  {'ratio': 9,   'nombre': 'Alibaba Group'},
    'MELI':  {'ratio': 120, 'nombre': 'MercadoLibre Inc.'},
    'NKE':   {'ratio': 12,  'nombre': 'Nike Inc.'},
    'DIS':   {'ratio': 12,  'nombre': 'Walt Disney Co.'},
    'PYPL':  {'ratio': 8,   'nombre': 'PayPal Holdings'},
    'INTC':  {'ratio': 5,   'nombre': 'Intel Corp.'},
    'CSCO':  {'ratio': 5,   'nombre': 'Cisco Systems'},
    'ORCL':  {'ratio': 3,   'nombre': 'Oracle Corp.'},
    'IBM':   {'ratio': 15,  'nombre': 'IBM Corp.'},
    'TXN':   {'ratio': 5,   'nombre': 'Texas Instruments'},
    'BA':    {'ratio': 24,  'nombre': 'Boeing Co.'},
    'XOM':   {'ratio': 10,  'nombre': 'Exxon Mobil Corp.'},
    'CVX':   {'ratio': 16,  'nombre': 'Chevron Corp.'},
    'JPM':   {'ratio': 15,  'nombre': 'JPMorgan Chase'},
    'OXY':   {'ratio': 5,   'nombre': 'Occidental Petroleum'},
    'WFC':   {'ratio': 5,   'nombre': 'Wells Fargo'},
    'GS':    {'ratio': 13,  'nombre': 'Goldman Sachs'},
    'VIST':  {'ratio': 3,   'nombre': 'Vista Energy'},
    'JNJ':   {'ratio': 15,  'nombre': 'Johnson & Johnson'},
    'PFE':   {'ratio': 4,   'nombre': 'Pfizer Inc.'},
    'ASML':  {'ratio': 146, 'nombre': 'ASML Holding'},
    'LLY':   {'ratio': 56,  'nombre': 'Eli Lilly & Co.'},
    'PG':    {'ratio': 15,  'nombre': 'Procter & Gamble'},
    'KO':    {'ratio': 5,   'nombre': 'Coca-Cola Co.'},
    'PEP':   {'ratio': 18,  'nombre': 'PepsiCo Inc.'},
    'WMT':   {'ratio': 18,  'nombre': 'Walmart Inc.'},
    'TGT':   {'ratio': 24,  'nombre': 'Target Corp.'},
    'MCD':   {'ratio': 24,  'nombre': "McDonald's Corp."},
    'SBUX':  {'ratio': 12,  'nombre': 'Starbucks Corp.'},
    'V':     {'ratio': 18,  'nombre': 'Visa Inc.'},
    'MA':    {'ratio': 33,  'nombre': 'Mastercard Inc.'},
    'ADBE':  {'ratio': 44,  'nombre': 'Adobe Inc.'},
    'CRM':   {'ratio': 18,  'nombre': 'Salesforce Inc.'},
    'AVGO':  {'ratio': 39,  'nombre': 'Broadcom Inc.'},
    'PAGS':  {'ratio': 3,   'nombre': 'PagSeguro Digital'},
    'SLV':   {'ratio': 6,   'nombre': 'iShares Silver Trust'},
    'MU':    {'ratio': 5,   'nombre': 'Micron Technology'},
    'VZ':    {'ratio': 4,   'nombre': 'Verizon Communications'},
    'GLD':   {'ratio': 50,  'nombre': 'SPDR Gold Shares'},
}

# Merval completo
MERVAL_TICKERS = [
    'GGAL.BA', 'YPF.BA', 'PAMP.BA', 'BBAR.BA', 'SUPV.BA', 'BMA.BA',
    'TXAR.BA', 'ALUA.BA', 'CRES.BA', 'IRSA.BA', 'LOMA.BA', 'MIRG.BA',
    'TECO2.BA', 'TGNO4.BA', 'TGSU2.BA', 'VALO.BA', 'BYMA.BA', 'EDN.BA',
    'HARG.BA', 'METR.BA', 'CEPU.BA', 'CVH.BA', 'AGRO.BA', 'COME.BA'
]


def get_usa_stocks() -> List[Dict]:
    """Obtiene los 75 stocks del S&P500"""
    cache_key = "mercado:usa"
    cached = cache_get(cache_key)
    if cached:
        logger.info("USA stocks desde caché")
        return cached

    logger.info(f"Fetching {len(SP500_TICKERS)} USA stocks...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(get_stock_data, SP500_TICKERS))

    stocks = [r for r in results if r is not None]
    cache_set(cache_key, stocks, expire=300)
    logger.info(f"USA stocks cargados: {len(stocks)}/{len(SP500_TICKERS)}")
    return stocks


def get_arg_stocks() -> List[Dict]:
    """Obtiene acciones del Merval"""
    cache_key = "mercado:arg"
    cached = cache_get(cache_key)
    if cached:
        logger.info("ARG stocks desde caché")
        return cached

    logger.info(f"Fetching {len(MERVAL_TICKERS)} ARG stocks...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_stock_data, MERVAL_TICKERS))

    stocks = [r for r in results if r is not None]
    cache_set(cache_key, stocks, expire=300)
    logger.info(f"ARG stocks cargados: {len(stocks)}/{len(MERVAL_TICKERS)}")
    return stocks


def get_cedears() -> List[Dict]:
    """
    Obtiene CEDEARs con precio en ARS.
    Precio ARS = precio_usd * ratio * dolar_ccl
    """
    cache_key = "mercado:cedears"
    cached = cache_get(cache_key)
    if cached:
        logger.info("CEDEARs desde caché")
        return cached

    # 1. Obtener dólar CCL
    dolar_ccl = 1000  # fallback
    try:
        import requests as req
        r = req.get("https://dolarapi.com/v1/dolares/contadoconliqui", timeout=20)
        if r.status_code == 200:
            dolar_ccl = float(r.json().get('venta', 1000))
            logger.info(f"Dólar ccl: ${dolar_ccl}")
    except Exception as e:
        logger.warning(f"No se pudo obtener dólar ccl: {e}")

    # 2. Obtener precios USD de todos los tickers
    tickers = list(CEDEARS_DATA.keys())
    logger.info(f"Fetching {len(tickers)} CEDEARs...")

    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(get_stock_data, tickers))

    cedears = []
    for stock in results:
        if stock is None:
            continue
        ticker = stock['ticker']
        info = CEDEARS_DATA.get(ticker, {})
        ratio = info.get('ratio', 1)

        # Precio en ARS = precio_usd / ratio * dolar_ccl
        precio_ars = round((stock['precio'] * dolar_ccl) / ratio, 2)

        cedears.append({
            'ticker': ticker,
            'nombre': info.get('nombre', stock['nombre']),
            'precio_usd': stock['precio'],
            'precio_ars': precio_ars,
            'ratio': ratio,
            'cambio': stock['cambio'],
            'volumen': stock['volumen'],
            'marketCap': stock['marketCap'],
            'sector': stock['sector'],
            'dolar_ccl': dolar_ccl,
        })

    cache_set(cache_key, cedears, expire=300)
    logger.info(f"CEDEARs cargados: {len(cedears)}/{len(tickers)}")
    return cedears
