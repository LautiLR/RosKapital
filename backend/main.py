"""
FINTECH ADVISOR - Backend con FastAPI
Aplicación principal optimizada y segura
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import sys
from pathlib import Path
from app.routers import community

from app.config import settings
from app.database import init_db

# Importar routers
from app.routers import auth, market, portfolio, users

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plataforma educativa de trading con datos en tiempo real",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# ============================================
# RATE LIMITING
# ============================================

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# MIDDLEWARE
# ============================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# GZIP Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host (seguridad contra host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["https://roskapital.up.railway.app", "*.up.railway.app", "localhost"]
    )

# Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # HSTS (solo en producción con HTTPS)
    if settings.ENABLE_HSTS and settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains"
    
    # Content Security Policy
    # response.headers["Content-Security-Policy"]
    
    return response

# ============================================
# TEMPLATES Y STATIC FILES
# ============================================

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================
# ROUTERS
# ============================================

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(market.router, prefix="/api", tags=["Market Data"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(community.router, prefix="/api/community", tags=["Community"])

# ============================================
# HTML ROUTES
# ============================================

@app.get("/")
async def home(request: Request):
    import requests as req
    
    import json
    from pathlib import Path

    MACRO_CACHE_FILE = Path("macro_cache.json")

    macro = {
        "dolar_ccl": "N/D",
        "inflacion": "N/A",
        "tasa_pf": "N/A",
        "riesgo_pais": "N/D"
    }

    def cargar_macro_cache():
        try:
            if MACRO_CACHE_FILE.exists():
                return json.loads(MACRO_CACHE_FILE.read_text())
        except Exception:
            pass
        return {}

    def guardar_macro_cache(datos):
        try:
            MACRO_CACHE_FILE.write_text(json.dumps(datos, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Error guardando caché macro: {e}")

    cache_macro = cargar_macro_cache()

    # 1. Dólar CCL
    try:
        r = req.get("https://dolarapi.com/v1/dolares/contadoconliqui", timeout=5)
        if r.status_code == 200:
            d = r.json()
            macro["dolar_ccl"] = f"${d.get('venta', 'N/D'):,.0f}"
            cache_macro["dolar_ccl"] = macro["dolar_ccl"]
    except Exception as e:
        logger.warning(f"Error obteniendo dólar: {e}")
        if "dolar_ccl" in cache_macro:
            macro["dolar_ccl"] = cache_macro["dolar_ccl"]

    # 2. Inflación y Tasa PF (BCRA)
    try:
        from datetime import datetime, timedelta

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        fecha_hasta = datetime.now().strftime("%Y-%m-%d")
        fecha_desde = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

        # Inflación Mensual (ID 27)
        url_inf = f"https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/27?Desde={fecha_desde}&Hasta={fecha_hasta}"
        r_inf = req.get(url_inf, headers=headers, timeout=10, verify=False)

        if r_inf.status_code == 200:
            data_inf = r_inf.json()
            results_inf = data_inf.get("results", [])
            if results_inf:
                detalle_inf = results_inf[0].get("detalle", [])
                if detalle_inf:
                    ultimo_dato = detalle_inf[-1]
                    macro["inflacion"] = f"{ultimo_dato.get('valor', 'N/A')}%"
                    cache_macro["inflacion"] = macro["inflacion"]
                    logger.info(f"Inflación: fecha={ultimo_dato.get('fecha')} valor={ultimo_dato.get('valor')}")
        else:
            logger.warning(f"Error Inflación BCRA: status {r_inf.status_code}")

        # Tasa BADLAR / Plazo Fijo (ID 7)
        url_tasa = f"https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/7?Desde={fecha_desde}&Hasta={fecha_hasta}"
        r_tasa = req.get(url_tasa, headers=headers, timeout=10, verify=False)

        if r_tasa.status_code == 200:
            data_tasa = r_tasa.json()
            results_tasa = data_tasa.get("results", [])
            if results_tasa:
                detalle_tasa = results_tasa[0].get("detalle", [])
                if detalle_tasa:
                    ultimo_dato = detalle_tasa[-1]
                    macro["tasa_pf"] = f"{ultimo_dato.get('valor', 'N/A')}%"
                    cache_macro["tasa_pf"] = macro["tasa_pf"]
                    logger.info(f"Tasa PF: fecha={ultimo_dato.get('fecha')} valor={ultimo_dato.get('valor')}")
        else:
            logger.warning(f"Error Tasa BCRA: status {r_tasa.status_code}")

    except Exception as e:
        logger.error(f"Error de conexión BCRA: {e}")
        
        
    # 3. Riesgo País
    try:
        r_rp = req.get("https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo", timeout=5)
        if r_rp.status_code == 200:
            data_rp = r_rp.json()
            macro["riesgo_pais"] = f"{data_rp.get('valor', 'N/D')}"
            cache_macro["riesgo_pais"] = macro["riesgo_pais"]
    except Exception as e:
        logger.warning(f"Error obteniendo riesgo país: {e}")
        if "riesgo_pais" in cache_macro:
            macro["riesgo_pais"] = cache_macro["riesgo_pais"]

    # Fallback: si algo quedó en N/A, usar caché
    if macro["inflacion"] == "N/A" and "inflacion" in cache_macro:
        macro["inflacion"] = cache_macro["inflacion"]
    if macro["tasa_pf"] == "N/A" and "tasa_pf" in cache_macro:
        macro["tasa_pf"] = cache_macro["tasa_pf"]

    # Guardar caché actualizado
    guardar_macro_cache(cache_macro)
        
    return templates.TemplateResponse("index.html", {
        "request": request,
        "data": {"macro": macro}
    })


@app.get("/mercado")
async def mercado(request: Request):
    """Monitor de mercado"""
    return templates.TemplateResponse("mercado_optimizado.html", {"request": request})


@app.get("/crypto")
async def crypto(request: Request):
    """Crypto wall"""
    return templates.TemplateResponse("crypto_optimizado.html", {"request": request})


@app.get("/explorar/{ticker}")
async def explorar(request: Request, ticker: str):
    """Terminal de análisis con datos completos + cálculo manual de PEG"""
    import yfinance as yf
    import requests as req_lib

    session = req_lib.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Valores por defecto
    precio = "0.00"
    nombre = ticker
    fundamentals = {}
    rendimientos = {
        "1D": "0.00",
        "1W": "0.00",
        "1M": "0.00",
        "3M": "0.00",
        "1Y": "0.00"
    }
    
    day_high = 0
    day_low = 0
    week52_high = 0
    week52_low = 0
    volumen = 0
    
    try:
        stock = yf.Ticker(ticker)
        
        # Obtener historia de 1 año para calcular rendimientos
        hist = stock.history(period="1y")
        
        if not hist.empty:
            # Precio actual
            current_price = hist['Close'].iloc[-1]
            precio = f"{current_price:.2f}"
            
            day_high = round(float(hist['High'].iloc[-1]), 2)
            day_low = round(float(hist['Low'].iloc[-1]), 2)
            
            # Rango 52 semanas
            week52_high = round(float(hist['High'].max()), 2)
            week52_low = round(float(hist['Low'].min()), 2)
            
            # Volumen
            volumen = int(hist['Volume'].iloc[-1])
            
            # Calcular rendimientos históricos
            try:
                # 1 día
                if len(hist) >= 2:
                    price_1d = hist['Close'].iloc[-2]
                    rendimientos["1D"] = f"{((current_price - price_1d) / price_1d * 100):.2f}"
                
                # 1 semana
                if len(hist) >= 7:
                    price_1w = hist['Close'].iloc[-7]
                    rendimientos["1W"] = f"{((current_price - price_1w) / price_1w * 100):.2f}"
                
                # 1 mes
                if len(hist) >= 30:
                    price_1m = hist['Close'].iloc[-30]
                    rendimientos["1M"] = f"{((current_price - price_1m) / price_1m * 100):.2f}"
                
                # 3 meses
                if len(hist) >= 90:
                    price_3m = hist['Close'].iloc[-90]
                    rendimientos["3M"] = f"{((current_price - price_3m) / price_3m * 100):.2f}"
                
                # 1 año
                if len(hist) >= 2:
                    price_1y = hist['Close'].iloc[0]
                    rendimientos["1Y"] = f"{((current_price - price_1y) / price_1y * 100):.2f}"
            except Exception as e:
                logger.warning(f"Error calculando rendimientos de {ticker}: {e}")
        
        # Obtener info y fundamentales
        try:
            info = stock.info
            
            # Nombre
            if 'longName' in info and info['longName']:
                nombre = info['longName']
            elif 'shortName' in info and info['shortName']:
                nombre = info['shortName']
            
            # Obtener métricas base
            pe_ratio = info.get('trailingPE', 0)
            earnings_growth = info.get('earningsGrowth', 0)  # Earnings growth rate
            
            # Calcular PEG manualmente si yfinance no lo da
            peg_ratio = info.get('pegRatio', 0)
            if not peg_ratio and pe_ratio and earnings_growth and earnings_growth > 0:
                # PEG = P/E / (Earnings Growth Rate * 100)
                # Si earningsGrowth es 0.15 (15%), lo multiplicamos por 100
                peg_ratio = pe_ratio / (earnings_growth * 100)
            
            earnings_date = None
            earnings_ts = info.get('earningsTimestampStart')
            if earnings_ts:
                from datetime import datetime
                earnings_date = datetime.fromtimestamp(earnings_ts).strftime('%d/%m/%Y')
            
            # Fundamentales
            fundamentals = {
                'marketCap': info.get('marketCap', 0),
                'peRatio': round(pe_ratio, 2) if pe_ratio else 0,
                'forwardPE': round(info.get('forwardPE', 0), 2) if info.get('forwardPE') else 0,
                'pegRatio': round(peg_ratio, 2) if peg_ratio else 0,
                'beta': round(info.get('beta', 0), 2) if info.get('beta') else 0,
                'dividendYield': round(info.get('dividendYield', 0), 2) if info.get('dividendYield') else 0,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'dayHigh': day_high if not hist.empty else info.get('dayHigh', 0),
                'dayLow': day_low if not hist.empty else info.get('dayLow', 0),
                'week52High': week52_high if not hist.empty else info.get('fiftyTwoWeekHigh', 0),
                'week52Low': week52_low if not hist.empty else info.get('fiftyTwoWeekLow', 0),
                'volume': volumen if not hist.empty else info.get('volume', 0),
                'previousClose': round(float(info.get('previousClose', 0)), 2),
                'open': round(float(info.get('open', 0)), 2),
                'preMarketPrice': round(float(info.get('preMarketPrice', 0)), 2) if info.get('preMarketPrice') else 0,
                'postMarketPrice': round(float(info.get('postMarketPrice', 0)), 2) if info.get('postMarketPrice') else 0,
                'ebitda': info.get('ebitda', 0),
                'evToEbitda': round(info.get('enterpriseToEbitda', 0), 2) if info.get('enterpriseToEbitda') else 0,
                'roe': round(info.get('returnOnEquity', 0) * 100, 2) if info.get('returnOnEquity') else 0,
                'roa': round(info.get('returnOnAssets', 0) * 100, 2) if info.get('returnOnAssets') else 0,
                'debtToEquity': round(info.get('debtToEquity', 0), 2) if info.get('debtToEquity') else None,
                'currentRatio': round(info.get('currentRatio', 0), 2) if info.get('currentRatio') else 0,
                'profitMargin': round(info.get('profitMargins', 0) * 100, 2) if info.get('profitMargins') else 0,
                'revenueGrowth': round(info.get('revenueGrowth', 0) * 100, 2) if info.get('revenueGrowth') else 0,
                'earningsDate': earnings_date,    
            }
            
            logger.info(f"PEG para {ticker}: {'calculado' if not info.get('pegRatio') else 'de yfinance'} = {fundamentals['pegRatio']}")
            
        except Exception as e:
            logger.warning(f"No se pudo obtener fundamentales de {ticker}: {e}")
        
        noticias = []
        try:
            raw_news = stock.news or []
            ticker_upper = ticker.upper().replace('.BA', '')
            nombre_corto = nombre.split()[0] if nombre else ''
    
            for n in raw_news[:20]:
                content = n.get('content', {})
                titulo = content.get('title', '')
                resumen = content.get('summary', '')
                texto = (titulo + ' ' + resumen).upper()
        
                if ticker_upper not in texto and nombre_corto.upper() not in texto:
                    continue
        
                url = content.get('clickThroughUrl', {})
                thumbnail = content.get('thumbnail', {})
                resolutions = thumbnail.get('resolutions', [])
                img_url = resolutions[0]['url'] if resolutions else None
        
                noticias.append({
                    'titulo': titulo,
                    'resumen': content.get('summary', ''),
                    'fuente': content.get('provider', {}).get('displayName', ''),
                    'fecha': content.get('pubDate', ''),
                    'url': url.get('url', '') if isinstance(url, dict) else '',
                    'imagen': img_url,
                })
        
                if len(noticias) >= 5:
                    break
        except Exception as e:
            logger.warning(f"Error obteniendo noticias de {ticker}: {e}")
            
    except Exception as e:
        logger.error(f"Error obteniendo datos de {ticker}: {e}")
    
    return templates.TemplateResponse("explorar.html", {
        "request": request,
        "data": {
            "ticker": ticker,
            "precio": precio,
            "nombre": nombre,
            "fundamentals": fundamentals,
            "noticias": noticias
        },
        "rend": rendimientos
    })
    

@app.get("/comunidad")
async def comunidad(request: Request):
    """Comunidad: Aprender + Blog"""
    return templates.TemplateResponse("comunidad.html", {"request": request})


@app.get("/comparar")
async def comparar(request: Request):
    """Comparador de activos"""
    return templates.TemplateResponse("comparar.html", {"request": request})    
    
    
@app.get("/api/fundamentals/{ticker}")
async def get_fundamentals(ticker: str):
    """API endpoint para obtener fundamentales de un ticker (usado por el comparador)"""
    import yfinance as yf
      
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        precio = 0
        rend_1y = 0
        volumen = 0
        day_high = 0
        day_low = 0
        
        if not hist.empty:
            precio = round(float(hist['Close'].iloc[-1]), 2)
            volumen = int(hist['Volume'].iloc[-1])
            day_high = round(float(hist['High'].iloc[-1]), 2)
            day_low = round(float(hist['Low'].iloc[-1]), 2)
            if len(hist) >= 2:
                price_1y = hist['Close'].iloc[0]
                rend_1y = round(((precio - price_1y) / price_1y * 100), 2)
        
        pe_ratio = info.get('trailingPE', 0)
        earnings_growth = info.get('earningsGrowth', 0)
        peg_ratio = info.get('pegRatio', 0)
        if not peg_ratio and pe_ratio and earnings_growth and earnings_growth > 0:
            peg_ratio = pe_ratio / (earnings_growth * 100)
        
        return {
            "ticker": ticker.upper(),
            "nombre": info.get('longName', info.get('shortName', ticker)),
            "precio": precio,
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "marketCap": info.get('marketCap', 0),
            "peRatio": round(pe_ratio, 2) if pe_ratio else 0,
            "forwardPE": round(info.get('forwardPE', 0), 2) if info.get('forwardPE') else 0,
            "pegRatio": round(peg_ratio, 2) if peg_ratio else 0,
            "beta": round(info.get('beta', 0), 2) if info.get('beta') else 0,
            'dividendYield': round(info.get('dividendYield', 0), 2) if info.get('dividendYield') else 0,
            "volume": volumen,
            "dayHigh": day_high,
            "dayLow": day_low,
            "rend1Y": rend_1y,
            'ebitda': info.get('ebitda', 0),
            'evToEbitda': round(info.get('enterpriseToEbitda', 0), 2) if info.get('enterpriseToEbitda') else 0,
            'roe': round(info.get('returnOnEquity', 0) * 100, 2) if info.get('returnOnEquity') else 0,
            'roa': round(info.get('returnOnAssets', 0) * 100, 2) if info.get('returnOnAssets') else 0,
            'debtToEquity': round(info.get('debtToEquity', 0), 2) if info.get('debtToEquity') else None,
            'currentRatio': round(info.get('currentRatio', 0), 2) if info.get('currentRatio') else 0,
            'profitMargin': round(info.get('profitMargins', 0) * 100, 2) if info.get('profitMargins') else 0,
            'revenueGrowth': round(info.get('revenueGrowth', 0) * 100, 2) if info.get('revenueGrowth') else 0,
        }
    except Exception as e:
        logger.error(f"Error en fundamentals de {ticker}: {e}")
        return JSONResponse(status_code=404, content={"detail": f"No se encontró {ticker}"})


@app.get("/heatmap")
async def heatmap(request: Request):
    """Heatmap del mercado"""
    return templates.TemplateResponse("heatmap.html", {"request": request})


@app.get("/simulador")
async def simulador(request: Request):
    """Simulador de trading"""
    return templates.TemplateResponse("simulador_optimizado.html", {"request": request})

@app.get("/about")
async def about(request: Request):
    """Landing page para nuevos usuarios"""
    return templates.TemplateResponse("about.html", {"request": request})


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/health")
async def api_health_check():
    """API health check con detalles"""
    from app.cache import redis_client
    
    redis_status = "connected" if redis_client else "disconnected"
    
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "cache": redis_status,
        "database": "connected"  # TODO: verificar DB
    }


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Recurso no encontrado"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Error interno del servidor: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"}
    )


# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    """Eventos al iniciar la aplicación"""
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌍 Entorno: {settings.ENVIRONMENT}")
    
    # Inicializar base de datos
    try:
        init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
    
    # Verificar Redis
    from app.cache import redis_client
    if redis_client:
        logger.info("✅ Redis conectado")
    else:
        logger.warning("⚠️ Redis no disponible - caché deshabilitado")


@app.on_event("shutdown")
async def shutdown_event():
    """Eventos al cerrar la aplicación"""
    logger.info("👋 Cerrando aplicación...")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
