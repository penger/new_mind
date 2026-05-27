from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models_timeline import TimelinePerson, TimelineEvent
from typing import List, Optional
import logging

router = APIRouter(prefix="/api/timeline", tags=["时间线"])
logger = logging.getLogger(__name__)


@router.get("/persons")
def get_all_persons(db: Session = Depends(get_db)):
    """获取所有历史人物"""
    try:
        persons = db.query(TimelinePerson).all()
        return [p.to_dict() for p in persons]
    except Exception as e:
        logger.error(f"获取历史人物失败: {e}")
        return []


@router.get("/persons/{person_id}")
def get_person_by_id(person_id: int, db: Session = Depends(get_db)):
    """根据ID获取历史人物"""
    try:
        person = db.query(TimelinePerson).filter(TimelinePerson.id == person_id).first()
        if person:
            return person.to_dict()
        return {"error": "人物不存在"}
    except Exception as e:
        logger.error(f"获取人物详情失败: {e}")
        return {"error": str(e)}


@router.get("/events")
def get_all_events(db: Session = Depends(get_db)):
    """获取所有历史事件"""
    try:
        events = db.query(TimelineEvent).all()
        return [e.to_dict() for e in events]
    except Exception as e:
        logger.error(f"获取历史事件失败: {e}")
        return []


@router.get("/events/year/{year}")
def get_events_by_year(year: int, db: Session = Depends(get_db)):
    """获取指定年份的事件"""
    try:
        events = db.query(TimelineEvent).all()
        result = []
        
        for e in events:
            if e.start_date:
                try:
                    event_year = int(str(e.start_date).split('-')[0])
                    if event_year == year:
                        result.append({
                            'id': e.id,
                            'event_name': e.event_name,
                            'date': e.start_date,
                            'description': e.description,
                            'event_category': e.event_category
                        })
                except (ValueError, IndexError):
                    continue
        
        return result
    except Exception as e:
        logger.error(f"获取年份事件失败: {e}")
        return []


@router.get("/stats")
def get_timeline_stats(db: Session = Depends(get_db)):
    """获取时间线统计信息"""
    try:
        person_count = db.query(TimelinePerson).count()
        event_count = db.query(TimelineEvent).count()
        
        persons = db.query(TimelinePerson).all()
        years = []
        for p in persons:
            if p.birth_date:
                try:
                    year = int(str(p.birth_date).split('-')[0])
                    years.append(year)
                except (ValueError, IndexError):
                    continue
        
        return {
            'person_count': person_count,
            'event_count': event_count,
            'year_range': {
                'min': min(years) if years else 1800,
                'max': max(years) if years else 2025
            }
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {
            'person_count': 0,
            'event_count': 0,
            'year_range': {'min': 1800, 'max': 2025}
        }
