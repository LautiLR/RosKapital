"""
Router para la comunidad: Posts y Comentarios
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db
from app.models import Post, Comment

router = APIRouter()


@router.get("/posts")
async def get_posts(
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Obtener todos los posts, opcionalmente filtrados por tag"""
    query = db.query(Post).order_by(Post.created_at.desc())
    
    if tag and tag != 'all':
        query = query.filter(Post.tag == tag)
    
    posts = query.limit(50).all()
    
    return [{
        "id": p.id,
        "autor": p.autor_nombre,
        "titulo": p.titulo,
        "contenido": p.contenido,
        "tag": p.tag,
        "imagen": p.imagen_url,
        "likes": p.likes,
        "fecha": p.created_at.isoformat(),
        "comentarios_count": len(p.comentarios)
    } for p in posts]


@router.get("/posts/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Obtener un post con sus comentarios"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    return {
        "id": post.id,
        "autor": post.autor_nombre,
        "titulo": post.titulo,
        "contenido": post.contenido,
        "tag": post.tag,
        "imagen": post.imagen_url,
        "likes": post.likes,
        "fecha": post.created_at.isoformat(),
        "comentarios": [{
            "id": c.id,
            "autor": c.autor_nombre,
            "contenido": c.contenido,
            "fecha": c.created_at.isoformat()
        } for c in post.comentarios]
    }


@router.post("/posts")
async def create_post(
    autor: str = Form(...),
    titulo: str = Form(...),
    contenido: str = Form(...),
    tag: str = Form(...),
    imagen: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Crear un nuevo post"""
    # Validaciones
    if len(autor.strip()) < 2:
        raise HTTPException(status_code=400, detail="El nombre debe tener al menos 2 caracteres")
    if len(titulo.strip()) < 5:
        raise HTTPException(status_code=400, detail="El título debe tener al menos 5 caracteres")
    if len(contenido.strip()) < 20:
        raise HTTPException(status_code=400, detail="El contenido debe tener al menos 20 caracteres")
    
    tags_validos = ['Análisis', 'Merval', 'Crypto', 'CEDEARs', 'Consulta', 'Opinión', 'Educativo']
    if tag not in tags_validos:
        raise HTTPException(status_code=400, detail=f"Tag inválido. Opciones: {', '.join(tags_validos)}")
    
    # Guardar imagen si existe
    imagen_url = None
    if imagen and imagen.filename:
        # Validar que sea imagen
        ext = imagen.filename.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            raise HTTPException(status_code=400, detail="Solo se permiten imágenes (jpg, png, gif, webp)")
        
        # Validar tamaño (max 5MB)
        contents = await imagen.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="La imagen no puede superar 5MB")
        
        # Guardar archivo
        upload_dir = "static/uploads/posts"
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(contents)
        
        imagen_url = f"/static/uploads/posts/{filename}"
    
    # Crear post
    post = Post(
        autor_nombre=autor.strip(),
        titulo=titulo.strip(),
        contenido=contenido.strip(),
        tag=tag,
        imagen_url=imagen_url
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return {"id": post.id, "message": "Post creado exitosamente"}


@router.post("/posts/{post_id}/comment")
async def create_comment(
    post_id: int,
    autor: str = Form(...),
    contenido: str = Form(...),
    db: Session = Depends(get_db)
):
    """Agregar comentario a un post"""
    from app.models import User, Notification
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    if len(autor.strip()) < 2:
        raise HTTPException(status_code=400, detail="El nombre debe tener al menos 2 caracteres")
    if len(contenido.strip()) < 5:
        raise HTTPException(status_code=400, detail="El comentario debe tener al menos 5 caracteres")
    
    comment = Comment(
        post_id=post_id,
        autor_nombre=autor.strip(),
        contenido=contenido.strip()
    )
    db.add(comment)
    
    # Notificar al autor del post si es un usuario registrado y no se comenta a sí mismo
    if post.autor_nombre != autor.strip():
        post_author = db.query(User).filter(User.username == post.autor_nombre).first()
        if post_author:
            notif = Notification(
                user_id=post_author.id,
                tipo="comunidad",
                titulo=f"{autor.strip()} comentó en tu post",
                mensaje=f'"{post.titulo}" — {contenido.strip()[:80]}',
                link="/comunidad"
            )
            db.add(notif)
    
    db.commit()
    
    return {"message": "Comentario agregado"}


@router.post("/posts/{post_id}/like")
async def like_post(post_id: int, db: Session = Depends(get_db)):
    """Dar like a un post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    post.likes = (post.likes or 0) + 1
    db.commit()
    
    return {"likes": post.likes}

@router.post("/posts/{post_id}/unlike")
async def unlike_post(post_id: int, db: Session = Depends(get_db)):
    """Quitar like a un post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    if post.likes > 0:
        post.likes = post.likes - 1
    db.commit()
    
    return {"likes": post.likes}

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """Eliminar un post (solo el autor)"""
    from app.auth import verify_token
    from app.models import User
    
    # Verificar token
    payload = verify_token(credentials.credentials)
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    if post.autor_nombre != user.username:
        raise HTTPException(status_code=403, detail="Solo el autor puede eliminar este post")
    
    db.delete(post)
    db.commit()
    
    return {"message": "Post eliminado"}