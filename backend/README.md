# 🚀 FINTECH ADVISOR - Backend Optimizado

Backend profesional construido con **FastAPI** para la plataforma educativa de trading.

## 📋 Características

### ✅ **Seguridad**
- 🔐 Autenticación JWT (Access + Refresh tokens)
- 🛡️ Rate limiting (por IP y por usuario)
- 🔒 Passwords hasheados con bcrypt
- 🌐 CORS configurado
- 🔑 Headers de seguridad (HSTS, CSP, X-Frame-Options)
- 🚫 Protección contra SQL Injection (ORM)
- ✅ Validación de inputs con Pydantic

### ⚡ **Performance**
- 💾 Caché con Redis (5-10 minutos)
- 🔄 Requests paralelos con ThreadPoolExecutor
- 📦 Compresión GZIP
- 🎯 Optimización de queries con SQLAlchemy

### 📊 **Funcionalidades**
- 📈 Datos de mercado en tiempo real (yfinance)
- ₿ Criptomonedas (Top 20)
- 📊 Índices (S&P 500, NASDAQ, Dow Jones, Russell 2000)
- 🔥 Heatmap personalizado
- 📉 Indicadores técnicos (RSI, MA50, MA200)
- 💼 Sistema de portfolio
- 📝 Historial de trades
- ⭐ Watchlist personalizado

---

## 🛠️ Instalación

### **Requisitos**
- Python 3.10+
- PostgreSQL 14+ (o SQLite para desarrollo)
- Redis 6+ (opcional pero recomendado)

### **Paso 1: Clonar repositorio**
```bash
git clone https://github.com/tu-usuario/fintech-advisor.git
cd fintech-advisor/backend
```

### **Paso 2: Crear entorno virtual**
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### **Paso 3: Instalar dependencias**
```bash
pip install -r requirements.txt
```

### **Paso 4: Configurar variables de entorno**
```bash
cp .env.example .env
nano .env  # o usa tu editor favorito
```

**Configuración mínima en `.env`:**
```env
SECRET_KEY="tu_clave_secreta_aqui_32_caracteres_minimo"
DATABASE_URL="sqlite:///./fintech.db"
REDIS_URL="redis://localhost:6379/0"
DEBUG=True
ENVIRONMENT="development"
CORS_ORIGINS="http://localhost:8000,http://localhost:3000"
```

**Generar SECRET_KEY segura:**
```bash
openssl rand -hex 32
```

### **Paso 5: Inicializar base de datos**
```bash
# SQLite (desarrollo)
python -c "from app.database import init_db; init_db()"

# PostgreSQL (producción)
# Crear base de datos primero:
# createdb fintech_db
# Luego:
python -c "from app.database import init_db; init_db()"
```

### **Paso 6: Iniciar servidor**
```bash
# Desarrollo (con auto-reload)
python main.py

# O con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

El servidor estará disponible en: **http://localhost:8000**

---

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuración (settings)
│   ├── database.py         # Conexión a DB
│   ├── models.py           # Modelos SQLAlchemy
│   ├── auth.py             # Sistema de autenticación
│   ├── cache.py            # Sistema de caché (Redis)
│   │
│   ├── routers/            # API Endpoints
│   │   ├── __init__.py
│   │   ├── auth.py         # Login, register, refresh
│   │   ├── market.py       # Datos de mercado
│   │   ├── portfolio.py    # Portfolio y trades
│   │   └── users.py        # Gestión de usuarios
│   │
│   └── services/           # Lógica de negocio
│       ├── __init__.py
│       ├── market_service.py    # Obtención de datos
│       └── portfolio_service.py # Lógica de portfolio
│
├── templates/              # HTML templates (Jinja2)
│   ├── index.html
│   ├── mercado_optimizado.html
│   ├── crypto_optimizado.html
│   ├── simulador_optimizado.html
│   └── ...
│
├── static/                 # Archivos estáticos
│   ├── css/
│   ├── js/
│   └── img/
│
├── logs/                   # Logs de la aplicación
│   └── app.log
│
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── .env.example           # Template de configuración
└── README.md              # Este archivo
```

---

## 🔌 API Endpoints

### **Autenticación**

#### `POST /api/auth/register`
Registra un nuevo usuario.
```json
{
  "email": "usuario@example.com",
  "username": "usuario123",
  "password": "Password123",
  "full_name": "Nombre Completo"
}
```

#### `POST /api/auth/login`
Inicia sesión.
```json
{
  "email": "usuario@example.com",
  "password": "Password123"
}
```

**Respuesta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1...",
  "refresh_token": "eyJ0eXAiOiJKV1...",
  "token_type": "bearer"
}
```

#### `GET /api/auth/me`
Obtiene información del usuario autenticado.
**Headers:** `Authorization: Bearer {access_token}`

---

### **Market Data**

#### `GET /api/stocks?country=USA&sector=Tech`
Obtiene lista de acciones con filtros.

**Parámetros:**
- `country`: ARG, USA (opcional)
- `sector`: Tech, Financiero, etc. (opcional)

#### `GET /api/cryptos`
Obtiene datos del mercado crypto (Top 20).

#### `GET /api/indices-reales`
Obtiene índices principales (S&P 500, NASDAQ, Dow Jones, Russell).

#### `GET /api/top-movers`
Obtiene las acciones con mayor movimiento del día.

#### `GET /api/heatmap?market=sp500`
Obtiene datos para el heatmap.

**Parámetros:**
- `market`: sp500, nasdaq, crypto, merval

#### `GET /api/cotizaciones?tickers=AAPL,TSLA,MSFT`
Obtiene cotizaciones de múltiples tickers.

#### `GET /api/indicators/{ticker}`
Obtiene indicadores técnicos (RSI, MA50, MA200, soporte, resistencia).

---

### **Portfolio (Requiere autenticación)**

#### `GET /api/portfolio`
Obtiene el portfolio del usuario.

#### `POST /api/portfolio/trade`
Ejecuta un trade (compra/venta).
```json
{
  "ticker": "AAPL",
  "trade_type": "BUY",
  "quantity": 10,
  "price": 185.50
}
```

#### `GET /api/portfolio/history`
Obtiene historial de trades.

---

## 🔒 Seguridad

### **Rate Limiting**
```python
# Configuración por defecto:
- API endpoints: 100 requests/hora
- HTML pages: 30 requests/minuto
- Cotizaciones: 200 requests/hora
```

### **CORS**
Configurado en `.env`:
```env
CORS_ORIGINS="https://tudominio.com,https://www.tudominio.com"
```

### **Headers de Seguridad**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HSTS en producción)
- `Content-Security-Policy`

### **Validación de Passwords**
- Mínimo 8 caracteres
- Al menos 1 mayúscula
- Al menos 1 número

---

## 🐳 Docker (Opcional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/fintech
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: fintech
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 🚀 Deployment

### **Railway (Recomendado)**
1. Conecta tu repo a Railway
2. Agrega PostgreSQL y Redis
3. Configura variables de entorno
4. Deploy automático

### **Render**
1. New Web Service → Connect Repo
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4`
4. Agrega PostgreSQL y Redis

### **DigitalOcean App Platform**
Similar a Railway/Render, sigue su wizard de deployment.

---

## 📊 Monitoreo

### **Sentry (Errores)**
Agrega en `.env`:
```env
SENTRY_DSN="https://tu-sentry-dsn.com"
```

### **Logs**
```bash
# Ver logs en tiempo real
tail -f logs/app.log
```

---

## 🧪 Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

---

## 📝 TODO

- [ ] Implementar routers de portfolio y users
- [ ] Agregar tests unitarios
- [ ] Implementar sistema de alertas de precio
- [ ] Integrar API de noticias
- [ ] Dashboard de admin
- [ ] Exportar reportes en PDF

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es privado y confidencial.

---

## 👤 Autor

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- Email: tu-email@example.com

---

## 🙏 Agradecimientos

- FastAPI por el excelente framework
- yfinance por los datos de mercado
- La comunidad de Python

---

## ⚠️ Disclaimer

Este es un proyecto educativo. No constituye asesoramiento financiero ni recomendación de inversión.
