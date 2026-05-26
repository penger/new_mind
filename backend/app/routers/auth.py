from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from passlib.context import CryptContext
import uuid

from app.database import get_db
from app.models import User, UserTheme, Theme

router = APIRouter(prefix="/auth", tags=["认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    themes: list


class Token(BaseModel):
    access_token: str
    token_type: str


class PasswordUpdate(BaseModel):
    password: str


class ThemeAssign(BaseModel):
    theme_id: str
    can_edit: bool = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def get_user_themes(db: Session, user_id: str):
    user_themes = db.query(UserTheme).filter(UserTheme.user_id == user_id).all()
    themes_info = []
    
    for ut in user_themes:
        theme = db.query(Theme).filter(Theme.id == ut.theme_id).first()
        if theme:
            themes_info.append({
                "theme_id": theme.id,
                "theme_name": theme.name,
                "can_edit": ut.can_edit == 'true'
            })
    
    return themes_info


@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    themes = get_user_themes(db, user.id)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        themes=themes
    )


@router.post("/register", response_model=UserResponse)
def register(request: LoginRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    hashed_password = get_password_hash(request.password)
    new_user = User(
        id=f"U_{uuid.uuid4()}",
        username=request.username,
        password=hashed_password,
        role='viewer'
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    all_themes = db.query(Theme).all()
    for theme in all_themes:
        user_theme = UserTheme(
            id=f"UT_{uuid.uuid4()}",
            user_id=new_user.id,
            theme_id=theme.id,
            can_edit='false'
        )
        db.add(user_theme)
    
    db.commit()
    
    themes = get_user_themes(db, new_user.id)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        themes=themes
    )


@router.get("/users", response_model=list)
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []
    
    for user in users:
        themes = get_user_themes(db, user.id)
        result.append(UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            themes=themes
        ))
    
    return result


@router.put("/users/{user_id}/role")
def update_user_role(user_id: str, role: str, db: Session = Depends(get_db)):
    if role not in ['admin', 'viewer']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的角色"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.role = role
    db.commit()
    
    return {"message": "角色更新成功", "user_id": user_id, "role": role}


@router.put("/users/{user_id}/password")
def update_user_password(user_id: str, request: PasswordUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.password = get_password_hash(request.password)
    user.updated_at = datetime.now()
    db.commit()
    
    return {"message": "密码修改成功", "user_id": user_id}


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if user.username == 'admin':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除管理员账户"
        )
    
    db.query(UserTheme).filter(UserTheme.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    
    return {"message": "用户删除成功", "user_id": user_id}


@router.post("/users/{user_id}/themes")
def add_user_theme(user_id: str, request: ThemeAssign, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    
    theme = db.query(Theme).filter(Theme.id == request.theme_id).first()
    if not theme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="主题不存在")
    
    existing = db.query(UserTheme).filter(
        UserTheme.user_id == user_id,
        UserTheme.theme_id == request.theme_id
    ).first()
    
    if existing:
        existing.can_edit = 'true' if request.can_edit else 'false'
        db.commit()
        return {"message": "主题权限更新成功", "user_theme_id": existing.id}
    
    user_theme = UserTheme(
        id=f"UT_{uuid.uuid4()}",
        user_id=user_id,
        theme_id=request.theme_id,
        can_edit='true' if request.can_edit else 'false'
    )
    
    db.add(user_theme)
    db.commit()
    
    return {"message": "主题关联成功", "user_theme_id": user_theme.id}


@router.delete("/users/{user_id}/themes/{theme_id}")
def remove_user_theme(user_id: str, theme_id: str, db: Session = Depends(get_db)):
    user_theme = db.query(UserTheme).filter(
        UserTheme.user_id == user_id,
        UserTheme.theme_id == theme_id
    ).first()
    
    if not user_theme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关联不存在")
    
    db.delete(user_theme)
    db.commit()
    
    return {"message": "主题关联已删除"}


@router.get("/themes")
def get_all_themes(db: Session = Depends(get_db)):
    themes = db.query(Theme).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "sort_num": t.sort_num
        }
        for t in themes
    ]
