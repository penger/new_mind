import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "graph_db")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

inspector = inspect(engine)

print("Database Tables:")
print("=" * 50)
tables = inspector.get_table_names()
for table in tables:
    print(f"[OK] {table}")
    columns = inspector.get_columns(table)
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")

print("\n" + "=" * 50)
print("Verify users and user_themes tables")
print("=" * 50)

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

try:
    from init_db import User, UserTheme
    
    users = session.query(User).all()
    print(f"\nUser count: {len(users)}")
    for user in users:
        print(f"  - {user.username} (role: {user.role})")
    
    user_themes = session.query(UserTheme).all()
    print(f"\nUser-theme links: {len(user_themes)}")
    for ut in user_themes:
        print(f"  - UserID: {ut.user_id}, ThemeID: {ut.theme_id}, CanEdit: {ut.can_edit}")
        
except Exception as e:
    print(f"Query error: {e}")
finally:
    session.close()
