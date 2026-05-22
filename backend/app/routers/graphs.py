from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import NodeStyle, EdgeStyle, Theme, Node, Edge
from app.schemas import GraphDataModel, NodeModel, EdgeModel, ThemeModel, NodeStyleModel, EdgeStyleModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/api", tags=["graphs"])


@router.get("/data")
def get_graph_data(theme_id: str = None, db: Session = Depends(get_db)):
    try:
        themes = db.query(Theme).all()
        node_styles = db.query(NodeStyle).all()
        edge_styles = db.query(EdgeStyle).all()
        
        # 如果没有指定theme_id，则使用默认主题（sort_num最高的主题）
        if not theme_id and themes:
            # 找到sort_num最高的主题作为默认主题
            default_theme = max(themes, key=lambda t: t.sort_num if t.sort_num is not None else -1)
            theme_id = default_theme.id
        
        if theme_id:
            nodes = db.query(Node).filter(Node.theme_id == theme_id).all()
            edges = db.query(Edge).filter(
                Edge.theme_id == theme_id,
                Edge.source_id.in_([n.id for n in nodes]),
                Edge.target_id.in_([n.id for n in nodes])
            ).all()
        else:
            # 如果没有主题，返回空数据
            nodes = []
            edges = []
        
        # 格式化theme数据，包含分隔符字符串和解析后的数组
        formatted_themes = []
        for t in themes:
            theme_data = {
                "id": t.id,
                "name": t.name,
                "defaultNodeStyleId": t.default_node_style_id,
                "defaultEdgeStyleId": t.default_edge_style_id,
                "sortNum": t.sort_num if t.sort_num is not None else 0
            }
            # 添加解析后的数组
            if t.default_node_style_id:
                theme_data["defaultNodeStyleIds"] = ThemeModel.parse_style_ids(t.default_node_style_id)
            if t.default_edge_style_id:
                theme_data["defaultEdgeStyleIds"] = ThemeModel.parse_style_ids(t.default_edge_style_id)
            formatted_themes.append(theme_data)
        
        return {
            "themes": formatted_themes,
            "nodeStyles": [{"id": ns.id, "name": ns.name, "color": ns.color, "shape": ns.shape, "opacity": ns.opacity} for ns in node_styles],
            "edgeStyles": [{"id": es.id, "name": es.name, "color": es.color, "line_style": es.line_style} for es in edge_styles],
            "nodes": [{"id": n.id, "label": n.label, "size": n.size, "themeId": n.theme_id, "nodeStyleId": n.node_style_id, "content": n.content, "style": n.style} for n in nodes],
            "links": [{"id": e.id, "source": e.source_id, "target": e.target_id, "label": e.label, "width": e.width, "themeId": e.theme_id, "edgeStyleId": e.edge_style_id, "content": e.content, "style": e.style} for e in edges]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/data")
def update_graph_data(data: GraphDataModel, db: Session = Depends(get_db)):
    """增量更新图谱数据 - 使用 merge 而不是删除"""
    try:
        # 使用 merge 进行 upsert 操作（存在则更新，不存在则插入）

        # 更新或插入 NodeStyles
        for ns in data.nodeStyles:
            db.merge(NodeStyle(id=ns.id, name=ns.name, color=ns.color, shape=ns.shape, opacity=ns.opacity))

        # 更新或插入 EdgeStyles
        for es in data.edgeStyles:
            db.merge(EdgeStyle(id=es.id, name=es.name, color=es.color, line_style=es.line_style))

        # 更新或插入 Themes
        for t in data.themes:
            # 如果有数组格式的数据，优先使用数组序列化为分隔符字符串
            if t.defaultNodeStyleIds:
                node_style_str = ThemeModel.serialize_style_ids(t.defaultNodeStyleIds)
            else:
                node_style_str = t.defaultNodeStyleId
                
            if t.defaultEdgeStyleIds:
                edge_style_str = ThemeModel.serialize_style_ids(t.defaultEdgeStyleIds)
            else:
                edge_style_str = t.defaultEdgeStyleId
                
            db.merge(Theme(id=t.id, name=t.name, default_node_style_id=node_style_str, default_edge_style_id=edge_style_str, sort_num=t.sortNum))

        # 更新或插入 Nodes
        for n in data.nodes:
            db.merge(Node(id=n.id, label=n.label, size=n.size, theme_id=n.themeId, node_style_id=n.nodeStyleId, content=n.content, style=n.style))

        # 更新或插入 Edges
        for e in data.links:
            db.merge(Edge(id=e.id, source_id=e.source, target_id=e.target, label=e.label, width=e.width, theme_id=e.themeId, edge_style_id=e.edgeStyleId, content=e.content, style=e.style))

        db.commit()
        return {"status": "success", "message": "Graph data saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction failed: {str(e)}")


@router.post("/backup")
def backup_tables(db: Session = Depends(get_db)):
    """备份 themes、nodes、edges 三个表"""
    try:
        # 生成带日期时间戳的备份表名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 备份表名
        themes_backup = f"themes_backup_{timestamp}"
        nodes_backup = f"nodes_backup_{timestamp}"
        edges_backup = f"edges_backup_{timestamp}"

        # 使用原生SQL执行备份（CREATE TABLE AS SELECT）
        db.execute(text(f"CREATE TABLE {themes_backup} AS SELECT * FROM themes"))
        db.execute(text(f"CREATE TABLE {nodes_backup} AS SELECT * FROM nodes"))
        db.execute(text(f"CREATE TABLE {edges_backup} AS SELECT * FROM edges"))

        db.commit()

        return {
            "status": "success",
            "message": "Backup completed successfully",
            "backup_tables": {
                "themes": themes_backup,
                "nodes": nodes_backup,
                "edges": edges_backup
            },
            "timestamp": timestamp
        }
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


# 主题操作
@router.post("/themes")
def create_theme(theme: ThemeModel, db: Session = Depends(get_db)):
    """创建单个主题，使用UUID生成唯一ID"""
    try:
        # 总是生成UUID格式的主题ID，忽略前端发送的ID
        theme_id = f"T_{uuid.uuid4()}"

        # 处理样式ID
        if theme.defaultNodeStyleIds:
            node_style_str = ThemeModel.serialize_style_ids(theme.defaultNodeStyleIds)
        else:
            node_style_str = theme.defaultNodeStyleId

        if theme.defaultEdgeStyleIds:
            edge_style_str = ThemeModel.serialize_style_ids(theme.defaultEdgeStyleIds)
        else:
            edge_style_str = theme.defaultEdgeStyleId

        db_theme = Theme(
            id=theme_id,
            name=theme.name,
            default_node_style_id=node_style_str,
            default_edge_style_id=edge_style_str,
            sort_num=theme.sortNum or 0
        )
        db.add(db_theme)
        db.commit()
        return {"status": "success", "message": "Theme created", "id": theme_id}
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/themes/{theme_id}")
def update_theme(theme_id: str, theme: ThemeModel, db: Session = Depends(get_db)):
    """更新或插入单个主题（upsert）"""
    try:
        # 处理样式ID
        if theme.defaultNodeStyleIds:
            node_style_str = ThemeModel.serialize_style_ids(theme.defaultNodeStyleIds)
        else:
            node_style_str = theme.defaultNodeStyleId

        if theme.defaultEdgeStyleIds:
            edge_style_str = ThemeModel.serialize_style_ids(theme.defaultEdgeStyleIds)
        else:
            edge_style_str = theme.defaultEdgeStyleId

        db.merge(Theme(
            id=theme_id,
            name=theme.name,
            default_node_style_id=node_style_str,
            default_edge_style_id=edge_style_str,
            sort_num=theme.sortNum or 0
        ))
        db.commit()
        return {"status": "success", "message": "Theme updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/themes/{theme_id}")
def delete_theme(theme_id: str, db: Session = Depends(get_db)):
    """删除主题及其关联的节点和边"""
    try:
        # 先删除主题关联的节点和边
        db.query(Edge).filter(Edge.theme_id == theme_id).delete(synchronize_session=False)
        db.query(Node).filter(Node.theme_id == theme_id).delete(synchronize_session=False)

        # 再删除主题
        db.query(Theme).filter(Theme.id == theme_id).delete(synchronize_session=False)
        db.commit()
        return {"status": "success", "message": "Theme and related data deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 单个节点操作
@router.post("/nodes")
def create_node(node: NodeModel, db: Session = Depends(get_db)):
    """创建单个节点，使用UUID生成唯一ID"""
    try:
        # 生成UUID格式的节点ID
        node_id = f"N_{uuid.uuid4()}"

        db_node = Node(
            id=node_id,
            label=node.label,
            size=node.size,
            theme_id=node.themeId,
            node_style_id=node.nodeStyleId,
            content=node.content,
            style=node.style
        )
        db.add(db_node)
        db.commit()
        return {"status": "success", "message": "Node created", "id": node_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 节点样式操作
@router.post("/node-styles")
def create_node_style(node_style: NodeStyleModel, db: Session = Depends(get_db)):
    """创建单个节点样式，使用UUID生成唯一ID"""
    try:
        # 生成UUID格式的样式ID
        style_id = f"NS_{uuid.uuid4()}"

        db_style = NodeStyle(
            id=style_id,
            name=node_style.name,
            color=node_style.color,
            shape=node_style.shape,
            opacity=node_style.opacity or 1.0
        )
        db.add(db_style)
        db.commit()
        return {"status": "success", "message": "Node style created", "id": style_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/node-styles/{style_id}")
def update_node_style(style_id: str, node_style: NodeStyleModel, db: Session = Depends(get_db)):
    """更新或插入单个节点样式（upsert）"""
    try:
        db.merge(NodeStyle(
            id=style_id,
            name=node_style.name,
            color=node_style.color,
            shape=node_style.shape,
            opacity=node_style.opacity or 1.0
        ))
        db.commit()
        return {"status": "success", "message": "Node style updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/node-styles/{style_id}")
def delete_node_style(style_id: str, db: Session = Depends(get_db)):
    """删除节点样式"""
    try:
        db.query(NodeStyle).filter(NodeStyle.id == style_id).delete(synchronize_session=False)
        db.commit()
        return {"status": "success", "message": "Node style deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 边样式操作
@router.post("/edge-styles")
def create_edge_style(edge_style: EdgeStyleModel, db: Session = Depends(get_db)):
    """创建单个边样式，使用UUID生成唯一ID"""
    try:
        # 生成UUID格式的样式ID
        style_id = f"ES_{uuid.uuid4()}"

        db_style = EdgeStyle(
            id=style_id,
            name=edge_style.name,
            color=edge_style.color,
            line_style=edge_style.line_style
        )
        db.add(db_style)
        db.commit()
        return {"status": "success", "message": "Edge style created", "id": style_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/edge-styles/{style_id}")
def update_edge_style(style_id: str, edge_style: EdgeStyleModel, db: Session = Depends(get_db)):
    """更新或插入单个边样式（upsert）"""
    try:
        db.merge(EdgeStyle(
            id=style_id,
            name=edge_style.name,
            color=edge_style.color,
            line_style=edge_style.line_style
        ))
        db.commit()
        return {"status": "success", "message": "Edge style updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/edge-styles/{style_id}")
def delete_edge_style(style_id: str, db: Session = Depends(get_db)):
    """删除边样式"""
    try:
        db.query(EdgeStyle).filter(EdgeStyle.id == style_id).delete(synchronize_session=False)
        db.commit()
        return {"status": "success", "message": "Edge style deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/nodes/{node_id}")
def update_node(node_id: str, node: NodeModel, db: Session = Depends(get_db)):
    """更新或插入单个节点（upsert）"""
    try:
        db.merge(Node(id=node.id, label=node.label, size=node.size, theme_id=node.themeId, node_style_id=node.nodeStyleId, content=node.content, style=node.style))
        db.commit()
        return {"status": "success", "message": "Node updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes/{node_id}")
def delete_node(node_id: str, db: Session = Depends(get_db)):
    """删除节点及其关联的边"""
    try:
        # 先删除关联的边
        db.query(Edge).filter(
            (Edge.source_id == node_id) | (Edge.target_id == node_id)
        ).delete(synchronize_session=False)
        
        # 再删除节点
        db.query(Node).filter(Node.id == node_id).delete(synchronize_session=False)
        db.commit()
        return {"status": "success", "message": "Node and related edges deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges")
def create_edge(edge: EdgeModel, db: Session = Depends(get_db)):
    """创建单个边，使用UUID生成唯一ID"""
    try:
        # 生成UUID格式的边ID
        edge_id = f"E_{uuid.uuid4()}"
        
        db_edge = Edge(
            id=edge_id,
            source_id=edge.source,
            target_id=edge.target,
            label=edge.label,
            width=edge.width,
            theme_id=edge.themeId,
            edge_style_id=edge.edgeStyleId,
            content=edge.content,
            style=edge.style
        )
        db.add(db_edge)
        db.commit()
        return {"status": "success", "message": "Edge created", "id": edge_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/edges/{edge_id}")
def update_edge(edge_id: str, edge: EdgeModel, db: Session = Depends(get_db)):
    """更新或插入单个边（upsert）"""
    try:
        db.merge(Edge(id=edge.id, source_id=edge.source, target_id=edge.target, label=edge.label, width=edge.width, theme_id=edge.themeId, edge_style_id=edge.edgeStyleId, content=edge.content, style=edge.style))
        db.commit()
        return {"status": "success", "message": "Edge updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/edges/{edge_id}")
def delete_edge(edge_id: str, db: Session = Depends(get_db)):
    """删除边"""
    try:
        db.query(Edge).filter(Edge.id == edge_id).delete(synchronize_session=False)
        db.commit()
        return {"status": "success", "message": "Edge deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
