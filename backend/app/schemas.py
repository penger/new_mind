from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class NodeStyleModel(BaseModel):
    id: str
    name: str
    color: str
    shape: str
    opacity: float


class EdgeStyleModel(BaseModel):
    id: str
    name: str
    color: str
    line_style: str


class ThemeModel(BaseModel):
    id: str
    name: str
    defaultNodeStyleId: Optional[str] = None
    defaultEdgeStyleId: Optional[str] = None
    sortNum: Optional[int] = 0


class NodeModel(BaseModel):
    id: str
    label: str
    size: float
    themeId: Optional[str] = None
    nodeStyleId: Optional[str] = None
    content: Optional[str] = None
    style: Optional[Dict[str, Any]] = None


class EdgeModel(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = ''
    width: Optional[float] = 2.0
    themeId: Optional[str] = None
    edgeStyleId: Optional[str] = None
    content: Optional[str] = None
    style: Optional[Dict[str, Any]] = None


class GraphDataModel(BaseModel):
    themes: List[ThemeModel] = []
    nodeStyles: List[NodeStyleModel] = []
    edgeStyles: List[EdgeStyleModel] = []
    nodes: List[NodeModel] = []
    links: List[EdgeModel] = []
