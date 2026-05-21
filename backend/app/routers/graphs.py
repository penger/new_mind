from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models import NodeStyle, EdgeStyle, Theme, Node, Edge
from app.schemas import GraphDataModel, NodeModel, EdgeModel, ThemeModel, NodeStyleModel, EdgeStyleModel
from datetime import datetime

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


# 单个节点操作
@router.post("/nodes")
def create_node(node: NodeModel, db: Session = Depends(get_db)):
    """创建单个节点"""
    try:
        existing = db.query(Node).filter(Node.id == node.id).first()
        if existing:
            max_id = db.query(Node).order_by(Node.id.desc()).first()
            if max_id and max_id.id:
                try:
                    num = int(max_id.id.replace('N', ''))
                    new_id = f"N{num + 1}"
                except:
                    new_id = f"N{max_id.id}"
            else:
                new_id = node.id
            node = NodeModel(id=new_id, label=node.label, size=node.size, themeId=node.themeId, nodeStyleId=node.nodeStyleId, content=node.content, style=node.style)
        
        db_node = Node(
            id=node.id,
            label=node.label,
            size=node.size,
            theme_id=node.themeId,
            node_style_id=node.nodeStyleId,
            content=node.content,
            style=node.style
        )
        db.add(db_node)
        db.commit()
        return {"status": "success", "message": "Node created", "id": node.id}
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
    """创建单个边"""
    try:
        existing = db.query(Edge).filter(Edge.id == edge.id).first()
        if existing:
            max_id = db.query(Edge).order_by(Edge.id.desc()).first()
            if max_id and max_id.id:
                try:
                    num = int(max_id.id.replace('E', ''))
                    new_id = f"E{num + 1}"
                except:
                    new_id = f"E{max_id.id}"
            else:
                new_id = edge.id
            edge = EdgeModel(id=new_id, source=edge.source, target=edge.target, label=edge.label, width=edge.width, themeId=edge.themeId, edgeStyleId=edge.edgeStyleId, content=edge.content, style=edge.style)
        
        db_edge = Edge(
            id=edge.id,
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
        return {"status": "success", "message": "Edge created", "id": edge.id}
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
