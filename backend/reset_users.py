import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "graph_db")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
session = Session()

try:
    from init_db import User, UserTheme
    
    # 删除旧用户
    print("删除旧用户...")
    session.query(UserTheme).delete()
    session.query(User).delete()
    session.commit()
    print("旧用户已删除")
    
    # 重新初始化数据库
    session.close()
    from init_db import init_database
    init_database()
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()
finally:
    session.close()
