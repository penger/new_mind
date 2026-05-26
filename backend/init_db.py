import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, ForeignKey, Text, JSON, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from passlib.context import CryptContext
import uuid

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "graph_db")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class NodeStyle(Base):
    __tablename__ = 'node_styles'
    id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    color = Column(String(20), nullable=False)
    shape = Column(String(20), nullable=False)
    opacity = Column(Float, default=1.0)


class EdgeStyle(Base):
    __tablename__ = 'edge_styles'
    id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    color = Column(String(20), nullable=False)
    line_style = Column(String(20), nullable=False)


class Theme(Base):
    __tablename__ = 'themes'
    id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    default_node_style_id = Column(Text)
    default_edge_style_id = Column(Text)
    sort_num = Column(Integer, default=0)


class Node(Base):
    __tablename__ = 'nodes'
    id = Column(String(50), primary_key=True)
    label = Column(String(255), nullable=False)
    size = Column(Float, default=22)
    theme_id = Column(String(50), ForeignKey('themes.id', ondelete='SET NULL'))
    node_style_id = Column(String(50), ForeignKey('node_styles.id', ondelete='SET NULL'))
    content = Column(Text, nullable=True)
    style = Column(JSON, nullable=True)


class Edge(Base):
    __tablename__ = 'edges'
    id = Column(String(50), primary_key=True)
    source_id = Column(String(50), ForeignKey('nodes.id', ondelete='CASCADE'))
    target_id = Column(String(50), ForeignKey('nodes.id', ondelete='CASCADE'))
    label = Column(String(255))
    width = Column(Float, default=2)
    theme_id = Column(String(50), ForeignKey('themes.id', ondelete='SET NULL'))
    edge_style_id = Column(String(50), ForeignKey('edge_styles.id', ondelete='SET NULL'))
    content = Column(Text, nullable=True)
    style = Column(JSON, nullable=True)


class User(Base):
    __tablename__ = 'users'
    id = Column(String(50), primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='viewer')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserTheme(Base):
    __tablename__ = 'user_themes'
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    theme_id = Column(String(50), ForeignKey('themes.id', ondelete='CASCADE'), nullable=False)
    can_edit = Column(String(10), default='false')
    created_at = Column(DateTime, default=datetime.now)


def init_database():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    print("正在创建数据库表...")
    Base.metadata.create_all(engine)
    print("数据库表创建成功！")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查是否已有admin用户
        existing_admin = session.query(User).filter_by(username='admin').first()
        if not existing_admin:
            print("正在创建默认用户...")
            
            # 创建默认管理员用户（密码加密）
            admin = User(
                id=f"U_{uuid.uuid4()}",
                username='admin',
                password=pwd_context.hash('happy0522'),  # 加密密码
                role='admin'
            )
            session.add(admin)
            
            # 创建默认游客用户（密码加密）
            viewer = User(
                id=f"U_{uuid.uuid4()}",
                username='viewer',
                password=pwd_context.hash('viewer123'),  # 加密密码
                role='viewer'
            )
            session.add(viewer)
            
            session.commit()
            print("默认用户创建成功！")
            print("  - admin (密码: happy0522, 角色: admin)")
            print("  - viewer (密码: viewer123, 角色: viewer)")
        else:
            print("用户已存在，跳过创建默认用户。")
        
        # 为所有主题创建与admin用户的关联
        admin_user = session.query(User).filter_by(username='admin').first()
        if admin_user:
            themes = session.query(Theme).all()
            for theme in themes:
                # 检查是否已有关联
                existing_link = session.query(UserTheme).filter_by(
                    user_id=admin_user.id,
                    theme_id=theme.id
                ).first()
                
                if not existing_link:
                    user_theme = UserTheme(
                        id=f"UT_{uuid.uuid4()}",
                        user_id=admin_user.id,
                        theme_id=theme.id,
                        can_edit='true'
                    )
                    session.add(user_theme)
            
            session.commit()
            print("用户-主题关联创建成功！")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    init_database()
