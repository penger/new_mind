from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NodeStyle, EdgeStyle, Theme, Node, Edge
from app.schemas import GraphDataModel, NodeModel, EdgeModel, ThemeModel, NodeStyleModel, EdgeStyleModel

router = APIRouter(prefix="/api", tags=["graphs"])


@router.get("/data")
def get_graph_data(theme_id: str = None, db: Session = Depends(get_db)):
    """获取图谱完整数据，支持按主题过滤"""
    try:
        themes = db.query(Theme).all()
        node_styles = db.query(NodeStyle).all()
        edge_styles = db.query(EdgeStyle).all()
        
        if theme_id:
            nodes = db.query(Node).filter(Node.theme_id == theme_id).all()
            node_ids = [n.id for n in nodes]
            edges = db.query(Edge).filter(
                Edge.theme_id == theme_id,
                Edge.source_id.in_(node_ids),
                Edge.target_id.in_(node_ids)
            ).all()
        else:
            nodes = db.query(Node).all()
            edges = db.query(Edge).all()
        
        return {
            "themes": [{"id": t.id, "name": t.name, "defaultNodeStyleId": t.default_node_style_id, "defaultEdgeStyleId": t.default_edge_style_id, "sortNum": t.sort_num if t.sort_num is not None else 0} for t in themes],
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
            db.merge(Theme(id=t.id, name=t.name, default_node_style_id=t.defaultNodeStyleId, default_edge_style_id=t.defaultEdgeStyleId, sort_num=t.sortNum))

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
        return {"status": "success", "message": "Node saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes/{node_id}")
def delete_node(node_id: str, db: Session = Depends(get_db)):
    """删除单个节点（会级联删除相关的边）"""
    try:
        db_node = db.query(Node).filter(Node.id == node_id).first()
        if not db_node:
            raise HTTPException(status_code=404, detail="Node not found")

        db.delete(db_node)
        db.commit()
        return {"status": "success", "message": "Node deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 单个边操作
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
        return {"status": "success", "message": "Edge saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/edges/{edge_id}")
def delete_edge(edge_id: str, db: Session = Depends(get_db)):
    """删除单个边"""
    try:
        db_edge = db.query(Edge).filter(Edge.id == edge_id).first()
        if not db_edge:
            raise HTTPException(status_code=404, detail="Edge not found")

        db.delete(db_edge)
        db.commit()
        return {"status": "success", "message": "Edge deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 单个 Theme 操作
@router.post("/themes")
def create_theme(theme: ThemeModel, db: Session = Depends(get_db)):
    """创建单个主题，自动设置 sort_num 为当前最大值 + 1"""
    try:
        # 查询当前最大的 sort_num
        max_sort = db.query(Theme.sort_num).order_by(Theme.sort_num.desc()).first()
        new_sort_num = (max_sort[0] + 1) if max_sort and max_sort[0] is not None else 1
        
        db_theme = Theme(
            id=theme.id,
            name=theme.name,
            default_node_style_id=theme.defaultNodeStyleId,
            default_edge_style_id=theme.defaultEdgeStyleId,
            sort_num=new_sort_num
        )
        db.add(db_theme)
        db.commit()
        return {"status": "success", "message": "Theme created", "sortNum": new_sort_num}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/themes/{theme_id}")
def update_theme(theme_id: str, theme: ThemeModel, db: Session = Depends(get_db)):
    """更新或插入单个主题（upsert）"""
    try:
        db.merge(Theme(id=theme.id, name=theme.name, default_node_style_id=theme.defaultNodeStyleId, default_edge_style_id=theme.defaultEdgeStyleId, sort_num=theme.sortNum))
        db.commit()
        return {"status": "success", "message": "Theme saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/themes/{theme_id}")
def delete_theme(theme_id: str, db: Session = Depends(get_db)):
    """删除单个主题"""
    try:
        db_theme = db.query(Theme).filter(Theme.id == theme_id).first()
        if not db_theme:
            raise HTTPException(status_code=404, detail="Theme not found")

        db.delete(db_theme)
        db.commit()
        return {"status": "success", "message": "Theme deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 单个 NodeStyle 操作
@router.post("/node-styles")
def create_node_style(ns: NodeStyleModel, db: Session = Depends(get_db)):
    """创建单个节点样式"""
    try:
        db_ns = NodeStyle(
            id=ns.id,
            name=ns.name,
            color=ns.color,
            shape=ns.shape,
            opacity=ns.opacity
        )
        db.add(db_ns)
        db.commit()
        return {"status": "success", "message": "NodeStyle created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/node-styles/{ns_id}")
def update_node_style(ns_id: str, ns: NodeStyleModel, db: Session = Depends(get_db)):
    """更新或插入单个节点样式（upsert）"""
    try:
        db.merge(NodeStyle(id=ns.id, name=ns.name, color=ns.color, shape=ns.shape, opacity=ns.opacity))
        db.commit()
        return {"status": "success", "message": "NodeStyle saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/node-styles/{ns_id}")
def delete_node_style(ns_id: str, db: Session = Depends(get_db)):
    """删除单个节点样式"""
    try:
        db_ns = db.query(NodeStyle).filter(NodeStyle.id == ns_id).first()
        if not db_ns:
            raise HTTPException(status_code=404, detail="NodeStyle not found")

        db.delete(db_ns)
        db.commit()
        return {"status": "success", "message": "NodeStyle deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 单个 EdgeStyle 操作
@router.post("/edge-styles")
def create_edge_style(es: EdgeStyleModel, db: Session = Depends(get_db)):
    """创建单个连线样式"""
    try:
        db_es = EdgeStyle(
            id=es.id,
            name=es.name,
            color=es.color,
            line_style=es.line_style
        )
        db.add(db_es)
        db.commit()
        return {"status": "success", "message": "EdgeStyle created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/edge-styles/{es_id}")
def update_edge_style(es_id: str, es: EdgeStyleModel, db: Session = Depends(get_db)):
    """更新或插入单个连线样式（upsert）"""
    try:
        db.merge(EdgeStyle(id=es.id, name=es.name, color=es.color, line_style=es.line_style))
        db.commit()
        return {"status": "success", "message": "EdgeStyle saved"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/edge-styles/{es_id}")
def delete_edge_style(es_id: str, db: Session = Depends(get_db)):
    """删除单个连线样式"""
    try:
        db_es = db.query(EdgeStyle).filter(EdgeStyle.id == es_id).first()
        if not db_es:
            raise HTTPException(status_code=404, detail="EdgeStyle not found")

        db.delete(db_es)
        db.commit()
        return {"status": "success", "message": "EdgeStyle deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
