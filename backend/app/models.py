from sqlalchemy import Column, String, Float, ForeignKey, Text, JSON, Integer
from app.database import Base


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
    default_node_style_id = Column(Text)  # 使用Text类型存储分隔符字符串，支持更长的内容
    default_edge_style_id = Column(Text)  # 使用Text类型存储分隔符字符串，支持更长的内容
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
