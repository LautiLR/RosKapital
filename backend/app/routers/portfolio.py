"""
Router de Portfolio
Endpoints para gestión de portfolio, trades, watchlist y alertas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.models import User, Portfolio, Position, Trade, Watchlist, Alert, EquitySnapshot, Notification
from app.database import get_db
from app.auth import get_current_user

router = APIRouter()


# ── Schemas ──
class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    price: float
    trade_type: str  # BUY, SELL

class AlertCreate(BaseModel):
    ticker: str
    precio: float
    direccion: str


# ── PORTFOLIO ──

@router.get("/")
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")
    
    positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
    
    return {
        "id": portfolio.id,
        "initial_capital": portfolio.initial_capital,
        "positions": [{
            "ticker": p.ticker,
            "q": p.quantity,
            "price": p.average_price,
            "nombre": p.asset_name or p.ticker
        } for p in positions]
    }


@router.post("/trade")
async def execute_trade(
    data: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")
    
    ticker = data.ticker.upper()
    total = data.quantity * data.price
    
    if data.trade_type == "BUY":
        position = db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.ticker == ticker
        ).first()
        
        if position:
            new_qty = position.quantity + data.quantity
            new_avg = ((position.quantity * position.average_price) + total) / new_qty
            position.quantity = new_qty
            position.average_price = new_avg
        else:
            position = Position(
                portfolio_id=portfolio.id,
                ticker=ticker,
                quantity=data.quantity,
                average_price=data.price
            )
            db.add(position)
    
    elif data.trade_type == "SELL":
        position = db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.ticker == ticker
        ).first()
        
        if not position or position.quantity < data.quantity:
            raise HTTPException(status_code=400, detail="No tenés suficientes acciones")
        
        position.quantity -= data.quantity
        if position.quantity <= 0:
            db.delete(position)
    
    # Registrar trade
    trade = Trade(
        user_id=current_user.id,
        portfolio_id=portfolio.id,
        ticker=ticker,
        trade_type=data.trade_type,
        quantity=data.quantity,
        price=data.price,
        total_amount=total
    )
    db.add(trade)
    db.commit()
    
    return {"message": f"{data.trade_type} {data.quantity} {ticker} @ ${data.price}"}


@router.get("/trades")
async def get_trades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trades = db.query(Trade).filter(Trade.user_id == current_user.id).order_by(Trade.executed_at.desc()).all()
    return [{
        "id": t.id,
        "tipo": t.trade_type,
        "ticker": t.ticker,
        "cantidad": t.quantity,
        "precio": t.price,
        "total": t.total_amount,
        "timestamp": t.executed_at.isoformat()
    } for t in trades]


# ── WATCHLIST ──

@router.get("/watchlist")
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    return [item.ticker for item in items]


@router.post("/watchlist/{ticker}")
async def add_to_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticker = ticker.upper()
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id, Watchlist.ticker == ticker
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya está en tu watchlist")
    
    count = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).count()
    if count >= 15:
        raise HTTPException(status_code=400, detail="Máximo 15 activos")
    
    db.add(Watchlist(user_id=current_user.id, ticker=ticker))
    db.commit()
    return {"message": f"{ticker} agregado"}


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticker = ticker.upper()
    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id, Watchlist.ticker == ticker
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(item)
    db.commit()
    return {"message": f"{ticker} eliminado"}


# ── ALERTAS ──

@router.get("/alertas")
async def get_alertas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alertas = db.query(Alert).filter(Alert.user_id == current_user.id).all()
    return [{
        "id": a.id, "ticker": a.ticker, "precio": a.precio,
        "direccion": a.direccion, "creadaEl": a.created_at.isoformat() if a.created_at else None
    } for a in alertas]


@router.post("/alertas")
async def create_alerta(
    data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Alert).filter(Alert.user_id == current_user.id).count()
    if count >= 4:
        raise HTTPException(status_code=400, detail="Máximo 4 alertas (plan free)")
    
    alerta = Alert(user_id=current_user.id, ticker=data.ticker.upper(), precio=data.precio, direccion=data.direccion)
    db.add(alerta)
    
    # Crear notificación
    dir_text = "supere" if data.direccion == "above" else "baje de"
    notif = Notification(
        user_id=current_user.id,
        tipo="alerta_precio",
        titulo="Alerta configurada",
        mensaje=f"Te avisaremos cuando {data.ticker.upper()} {dir_text} ${data.precio:.2f}",
        link=f"/explorar/{data.ticker.upper()}"
    )
    db.add(notif)
    db.commit()
    
    return {"message": "Alerta creada", "id": alerta.id}


@router.delete("/alertas/{alerta_id}")
async def delete_alerta(
    alerta_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alerta = db.query(Alert).filter(Alert.id == alerta_id, Alert.user_id == current_user.id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    db.delete(alerta)
    db.commit()
    return {"message": "Alerta eliminada"}

@router.delete("/reset")
async def reset_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reinicia el portfolio: borra posiciones, trades y resetea capital"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")
    
    # Borrar posiciones
    db.query(Position).filter(Position.portfolio_id == portfolio.id).delete()
    
    # Borrar trades
    db.query(Trade).filter(Trade.user_id == current_user.id).delete()
    
    db.query(EquitySnapshot).filter(EquitySnapshot.portfolio_id == portfolio.id).delete()
    
    # Resetear capital
    portfolio.initial_capital = 100000.0
    portfolio.current_equity = 100000.0
    portfolio.cash_available = 100000.0
    
    db.commit()
    return {"message": "Portfolio reiniciado"}

@router.get("/misiones")
async def get_misiones(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models import Mission
    missions = db.query(Mission).filter(Mission.user_id == current_user.id, Mission.completed == True).all()
    return [m.mission_key for m in missions]


@router.post("/misiones/{mission_key}")
async def complete_mission(
    mission_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models import Mission
    existing = db.query(Mission).filter(
        Mission.user_id == current_user.id, Mission.mission_key == mission_key
    ).first()
    if existing:
        return {"message": "Misión ya completada"}
    
    mission = Mission(user_id=current_user.id, mission_key=mission_key, completed=True, completed_at=datetime.utcnow())
    db.add(mission)
    
    # Crear notificación
    MISSION_NAMES = {
        'identidad': '🎭 Test de Inversor completado',
        'explorador': '🚀 Primeros Pasos',
        'curioso': '🔍 Curiosidad Financiera',
        'inversor': '📈 ¡Accionista!',
        'vigilante': '⭐ Ojo de Halcón',
        'alerta': '🔔 Alerta Activada',
        'analista': '🔬 Analista Junior',
        'comparador': '⚖️ Versus Mode',
        'diversificado': '🎯 Cartera Diversificada',
        'trader': '💹 Trader Activo',
        'ganador': '🏆 Primera Ganancia'
    }
    titulo = MISSION_NAMES.get(mission_key, f'Misión: {mission_key}')
    
    notif = Notification(
        user_id=current_user.id,
        tipo="mision",
        titulo="¡Misión cumplida!",
        mensaje=titulo,
        link="/simulador"
    )
    db.add(notif)
    db.commit()
    
    return {"message": f"Misión '{mission_key}' completada"}

# ── PERFIL INVERSOR ──

class PerfilUpdate(BaseModel):
    tipo: str
    personaje: str

@router.get("/perfil")
async def get_perfil(
    current_user: User = Depends(get_current_user)
):
    return {
        "investor_profile": current_user.investor_profile,
        "portfolio_public": current_user.portfolio_public if hasattr(current_user, 'portfolio_public') else False
    }

@router.put("/perfil")
async def update_perfil(
    data: PerfilUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.investor_profile = data.tipo
    db.commit()
    return {"message": "Perfil actualizado"}

@router.get("/snapshots")
async def get_snapshots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        return []
    
    snapshots = db.query(EquitySnapshot).filter(
        EquitySnapshot.portfolio_id == portfolio.id
    ).order_by(EquitySnapshot.snapshot_at.asc()).all()
    
    return [{"timestamp": int(s.snapshot_at.timestamp() * 1000), "equity": s.equity} for s in snapshots]


@router.post("/snapshots")
async def save_snapshot(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")
    
    positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
    invested = sum(p.quantity * p.average_price for p in positions)
    cash = portfolio.initial_capital - invested
    equity = cash + invested  # Se actualiza con precios reales desde el frontend
    
    snapshot = EquitySnapshot(
        portfolio_id=portfolio.id,
        equity=equity,
        cash=cash,
        invested=invested
    )
    db.add(snapshot)
    
    # Mantener máximo 200 snapshots
    count = db.query(EquitySnapshot).filter(EquitySnapshot.portfolio_id == portfolio.id).count()
    if count > 200:
        oldest = db.query(EquitySnapshot).filter(
            EquitySnapshot.portfolio_id == portfolio.id
        ).order_by(EquitySnapshot.snapshot_at.asc()).first()
        if oldest:
            db.delete(oldest)
    
    db.commit()
    return {"message": "Snapshot guardado"}

@router.get("/notificaciones")
async def get_notificaciones(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    return [{
        "id": n.id,
        "tipo": n.tipo,
        "titulo": n.titulo,
        "mensaje": n.mensaje,
        "link": n.link,
        "leida": n.leida,
        "created_at": n.created_at.isoformat()
    } for n in notifs]


@router.get("/notificaciones/count")
async def get_notificaciones_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.leida == False
    ).count()
    return {"count": count}


@router.put("/notificaciones/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.leida == False
    ).update({"leida": True})
    db.commit()
    return {"message": "Todas marcadas como leídas"}


@router.put("/notificaciones/{notif_id}/read")
async def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notif.leida = True
    db.commit()
    return {"message": "Marcada como leída"}


@router.delete("/notificaciones/{notif_id}")
async def delete_notificacion(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    db.delete(notif)
    db.commit()
    return {"message": "Notificación eliminada"}

# ── PORTFOLIO PÚBLICO ──

@router.put("/public-toggle")
async def toggle_public_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.portfolio_public = not current_user.portfolio_public
    db.commit()
    return {"public": current_user.portfolio_public}


@router.get("/public-portfolios")
async def get_public_portfolios(db: Session = Depends(get_db)):
    """Obtener todos los portfolios públicos con rendimiento"""
    users = db.query(User).filter(User.portfolio_public == True).all()
    
    result = []
    for user in users:
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
        if not portfolio:
            continue
        
        positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        if not positions:
            continue
        
        tickers = [p.ticker for p in positions]
        invested = sum(p.quantity * p.average_price for p in positions)
        
        # Calcular rendimiento ponderado real
        total_cost = sum(p.quantity * p.average_price for p in positions)
        weights = {}
        for p in positions:
            cost = p.quantity * p.average_price
            weights[p.ticker] = cost / total_cost if total_cost > 0 else 0
        
        result.append({
            "username": user.username,
            "investor_profile": portfolio.portfolio_profile or user.investor_profile,
            "tickers": tickers,
            "num_positions": len(positions),
            "cost_basis": {p.ticker: p.average_price for p in positions},
            "weights": weights,
            "member_since": user.created_at.isoformat() if user.created_at else None
        })
    
    return result

class PortfolioProfileUpdate(BaseModel):
    tipo: str

@router.put("/portfolio-profile")
async def update_portfolio_profile(
    data: PortfolioProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")
    portfolio.portfolio_profile = data.tipo
    db.commit()
    return {"message": "Perfil de cartera actualizado"}

@router.get("/portfolio-profile")
async def get_portfolio_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        return {"tipo": None}
    return {"tipo": portfolio.portfolio_profile}

@router.post("/streak")
async def update_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza la racha diaria del usuario"""
    from datetime import datetime, timedelta
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    last_visit = current_user.last_visit_date
    
    if last_visit == today:
        # Ya visitó hoy, no hacer nada
        return {"streak": current_user.streak_count, "updated": False}
    
    if last_visit == yesterday:
        # Visitó ayer, sumar racha
        current_user.streak_count = (current_user.streak_count or 0) + 1
    else:
        # Se rompió la racha, empezar de 1
        current_user.streak_count = 1
    
    current_user.last_visit_date = today
    db.commit()
    
    return {"streak": current_user.streak_count, "updated": True}


@router.get("/streak")
async def get_streak(
    current_user: User = Depends(get_current_user)
):
    return {"streak": current_user.streak_count or 0}

@router.post("/send-weekly-summary")
async def send_weekly_summary_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Envía el resumen semanal por email al usuario actual"""
    from app.auth import send_weekly_summary
    from app.models import Mission
    
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio no encontrado")
    
    positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
    
    # Obtener precios actuales
    import yfinance as yf
    positions_data = []
    total_value = 0
    total_cost = 0
    
    for pos in positions:
        try:
            ticker_data = yf.Ticker(pos.ticker)
            current_price = ticker_data.info.get('regularMarketPrice', pos.average_price)
        except:
            current_price = pos.average_price
        
        value = pos.quantity * current_price
        cost = pos.quantity * pos.average_price
        rend = ((current_price - pos.average_price) / pos.average_price) * 100 if pos.average_price > 0 else 0
        
        total_value += value
        total_cost += cost
        
        positions_data.append({
            "ticker": pos.ticker,
            "precio_actual": current_price,
            "rendimiento": rend,
            "pnl": value - cost
        })
    
    cash = portfolio.initial_capital - total_cost
    equity = cash + total_value
    pnl = equity - portfolio.initial_capital
    pnl_pct = (pnl / portfolio.initial_capital) * 100 if portfolio.initial_capital > 0 else 0
    
    # Misiones
    misiones_count = db.query(Mission).filter(Mission.user_id == current_user.id, Mission.completed == True).count()
    
    portfolio_data = {
        "positions": positions_data,
        "equity": equity,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "streak": current_user.streak_count or 0,
        "misiones": misiones_count
    }
    
    success = send_weekly_summary(current_user.email, current_user.username, portfolio_data)
    
    if success:
        return {"message": "Resumen enviado correctamente"}
    else:
        raise HTTPException(status_code=500, detail="Error enviando el email")