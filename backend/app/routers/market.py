"""
Router de Market Data
Endpoints para datos de mercado
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

from app.services.market_service import (
    get_multiple_stocks,
    get_crypto_market_data,
    get_market_indices,
    get_top_movers,
    get_heatmap_data,
    get_technical_indicators,
    get_usa_stocks,
    get_arg_stocks,
    get_cedears
)


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/stocks")
async def get_stocks(
    request: Request,  # ← Agregar este parámetro
    country: Optional[str] = None,
    sector: Optional[str] = None,
):
    """
    Obtiene lista de acciones con filtros opcionales
    
    - **country**: ARG o USA
    - **sector**: Tech, Financiero, Energía, etc.
    """
    
    # Lista completa de tickers
    tickers = [
        # USA
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD',
        'NFLX', 'DIS', 'BA', 'INTC', 'CSCO', 'ORCL', 'IBM', 'QCOM',
        # Argentina
        'GGAL.BA', 'YPF.BA', 'PAMP.BA', 'BBAR.BA', 'SUPV.BA', 'BMA.BA'
    ]
    
    stocks = get_multiple_stocks(tickers)
    
    # Aplicar filtros
    if country:
        stocks = [s for s in stocks if s['pais'] == country.upper()]
    
    if sector:
        stocks = [s for s in stocks if s['sector'].lower() == sector.lower()]
    
    return stocks


@router.get("/cryptos")
@limiter.limit("100/hour")
async def get_cryptos(
    request: Request,
):
    """Obtiene datos del mercado crypto"""
    return get_crypto_market_data()


@router.get("/indices-reales")
@limiter.limit("100/hour")
async def get_indices(
    request: Request,
):
    """Obtiene índices principales del mercado"""
    return get_market_indices()


@router.get("/top-movers")
@limiter.limit("100/hour")
async def get_movers(
    request: Request,
):
    """Obtiene las acciones con mayor movimiento del día"""
    return get_top_movers()


@router.get("/heatmap")
@limiter.limit("60/hour")
async def get_heatmap(
    request: Request,
    market: str = "sp500",
):
    """
    Obtiene datos para el heatmap
    
    - **market**: sp500, nasdaq, crypto, merval
    """
    return get_heatmap_data(market)


@router.get("/cotizaciones")
@limiter.limit("200/hour")
async def get_cotizaciones(
    request: Request,
    tickers: str,
):
    """
    Obtiene cotizaciones de múltiples tickers
    
    - **tickers**: Lista de tickers separados por coma (ej: AAPL,TSLA,MSFT)
    """
    ticker_list = [t.strip().upper() for t in tickers.split(',')]
    
    if len(ticker_list) > 20:
        raise HTTPException(
            status_code=400,
            detail="Máximo 20 tickers por request"
        )
    
    stocks = get_multiple_stocks(ticker_list)
    
    # Formatear respuesta como diccionario ticker: datos
    return {stock['ticker']: {
        'precio': stock['precio'],
        'variacion': stock['cambio']
    } for stock in stocks}




@router.get("/stocks/usa")
@limiter.limit("30/hour")
async def get_stocks_usa(request: Request):
    """Obtiene 75 acciones del S&P500"""
    return get_usa_stocks()


@router.get("/stocks/arg")
@limiter.limit("30/hour")
async def get_stocks_arg(request: Request):
    """Obtiene acciones del Merval"""
    return get_arg_stocks()


@router.get("/stocks/cedears")
@limiter.limit("30/hour")
async def get_stocks_cedears(request: Request):
    """Obtiene CEDEARs con precio en ARS"""
    return get_cedears()

@router.get("/indicators/{ticker}")
@limiter.limit("60/hour")
async def get_indicators(
    request: Request,
    ticker: str,
):
    """
    Obtiene indicadores técnicos de un ticker
    
    - **ticker**: Símbolo del activo (ej: AAPL, BTC-USD)
    """
    indicators = get_technical_indicators(ticker.upper())
    
    if not indicators:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudieron obtener indicadores para {ticker}"
        )
    
    return indicators

@router.get("/economic-calendar")
async def get_economic_calendar(request: Request):
    """Calendario económico de la semana"""
    import json
    from datetime import datetime, timedelta
    from pathlib import Path
    
    try:
        calendar_file = Path(__file__).resolve().parent.parent / "economic_events.json"
        if not calendar_file.exists():
            return []
        
        data = json.loads(calendar_file.read_text(encoding="utf-8"))
        scheduled = data.get("scheduled_2026", {})
        
        today = datetime.utcnow()
        events = []
        
        # Buscar eventos de los próximos 7 días
        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            if date_str in scheduled:
                for evt in scheduled[date_str]:
                    events.append({
                        "date": date_str,
                        "day_name": date.strftime("%A"),
                        "event": evt["event"],
                        "time": evt.get("time", ""),
                        "impact": evt.get("impact", "medium"),
                        "country": evt.get("country", "US"),
                        "actual": evt.get("actual", ""),
                        "estimate": evt.get("estimate", ""),
                        "prev": evt.get("prev", "")
                    })
        
        return events
        
    except Exception as e:
        print(f"Error loading economic calendar: {e}")
        return []
    
@router.get("/dolar-watch")
async def get_dolar_watch(request: Request):
    """Cotizaciones de todos los tipos de dólar"""
    import httpx
    import json
    from datetime import datetime, timedelta
    from pathlib import Path
    
    cache_file = Path(__file__).resolve().parent.parent / "dolar_cache.json"
    
    # Cache de 5 minutos
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
            cache_time = datetime.fromisoformat(cache.get("cached_at", "2000-01-01"))
            if datetime.utcnow() - cache_time < timedelta(minutes=5):
                return cache.get("data", [])
        except:
            pass
    
    dolares = []
    tipos = [
        {"slug": "oficial", "nombre": "Oficial", "icono": "🏛️"},
        {"slug": "blue", "nombre": "Blue", "icono": "💵"},
        {"slug": "contadoconliqui", "nombre": "CCL", "icono": "📊"},
        {"slug": "bolsa", "nombre": "MEP (Bolsa)", "icono": "📈"},
        {"slug": "mayorista", "nombre": "Mayorista", "icono": "🏦"},
        {"slug": "cripto", "nombre": "Crypto", "icono": "₿"},
        {"slug": "tarjeta", "nombre": "Tarjeta", "icono": "💳"}
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            for tipo in tipos:
                try:
                    res = await client.get(
                        f"https://dolarapi.com/v1/dolares/{tipo['slug']}",
                        timeout=5
                    )
                    if res.status_code == 200:
                        data = res.json()
                        dolares.append({
                            "nombre": tipo["nombre"],
                            "icono": tipo["icono"],
                            "compra": data.get("compra", 0),
                            "venta": data.get("venta", 0),
                            "spread": round(((data.get("venta", 0) - data.get("compra", 0)) / data.get("compra", 1)) * 100, 2) if data.get("compra") else 0,
                            "fuente": data.get("casa", tipo["slug"]),
                            "fecha": data.get("fechaActualizacion", "")
                        })
                except:
                    continue
        
        # Guardar cache
        cache_file.write_text(json.dumps({
            "cached_at": datetime.utcnow().isoformat(),
            "data": dolares
        }, ensure_ascii=False), encoding="utf-8")
        
    except Exception as e:
        print(f"Error fetching dolar watch: {e}")
    
    return dolares

@router.get("/cedear-info/{ticker}")
async def get_cedear_info(ticker: str, request: Request):
    """Info de CEDEAR: ratio y precio teórico en ARS"""
    import httpx
    from app.services.market_service import CEDEARS_DATA
    
    ticker = ticker.upper()
    if ticker not in CEDEARS_DATA:
        return {"has_cedear": False}
    
    cedear = CEDEARS_DATA[ticker]
    
    # Obtener dólar CCL
    dolar_ccl = 1000  # fallback
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get("https://dolarapi.com/v1/dolares/contadoconliqui", timeout=5)
            if res.status_code == 200:
                dolar_ccl = float(res.json().get("venta", 1000))
    except:
        pass
    
    return {
        "has_cedear": True,
        "ticker": ticker,
        "nombre": cedear["nombre"],
        "ratio": cedear["ratio"],
        "dolar_ccl": dolar_ccl
    }