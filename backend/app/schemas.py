from pydantic import BaseModel
from typing import List, Optional, Dict, Any, ClassVar


class NodeStyleModel(BaseModel):
    id: Optional[str] = None
    name: str
    color: str
    shape: str
    opacity: Optional[float] = 1.0


class EdgeStyleModel(BaseModel):
    id: Optional[str] = None
    name: str
    color: str
    line_style: str


class ThemeModel(BaseModel):
    id: Optional[str] = None
    name: str
    defaultNodeStyleId: Optional[str] = None  # 分隔符字符串：style_id_1,style_id_2,style_id_3
    defaultEdgeStyleId: Optional[str] = None  # 分隔符字符串：edge_style_1,edge_style_2
    defaultNodeStyleIds: Optional[List[str]] = None  # 解析后的数组 ["style_id_1", "style_id_2"]
    defaultEdgeStyleIds: Optional[List[str]] = None  # 解析后的数组 ["edge_style_1", "edge_style_2"]
    sortNum: Optional[int] = 0
    
    # 分隔符字符
    STYLE_ID_DELIMITER: ClassVar[str] = ','
    
    @classmethod
    def parse_style_ids(cls, style_ids_string: Optional[str]) -> List[str]:
        """将分隔符字符串解析为ID数组"""
        if not style_ids_string:
            return []
        return [id.strip() for id in style_ids_string.split(cls.STYLE_ID_DELIMITER) if id.strip()]
    
    @classmethod
    def serialize_style_ids(cls, style_ids: Optional[List[str]]) -> Optional[str]:
        """将ID数组序列化为分隔符字符串"""
        if not style_ids or len(style_ids) == 0:
            return None
        return cls.STYLE_ID_DELIMITER.join([id.strip() for id in style_ids if id.strip()])
    
    def model_post_init(self, __context: Any) -> None:
        """在初始化后解析styleId字符串为数组"""
        if self.defaultNodeStyleIds is None and self.defaultNodeStyleId is not None:
            self.defaultNodeStyleIds = self.parse_style_ids(self.defaultNodeStyleId)
        if self.defaultEdgeStyleIds is None and self.defaultEdgeStyleId is not None:
            self.defaultEdgeStyleIds = self.parse_style_ids(self.defaultEdgeStyleId)
    
    def dict(self, *args, **kwargs):
        """重写dict方法，确保输出包含解析后的数组"""
        result = super().dict(*args, **kwargs)
        # 如果字段名存在但数组不存在，进行解析
        if result.get('defaultNodeStyleId') and 'defaultNodeStyleIds' not in result:
            result['defaultNodeStyleIds'] = self.parse_style_ids(result['defaultNodeStyleId'])
        if result.get('defaultEdgeStyleId') and 'defaultEdgeStyleIds' not in result:
            result['defaultEdgeStyleIds'] = self.parse_style_ids(result['defaultEdgeStyleId'])
        return result


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
