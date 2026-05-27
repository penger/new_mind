from sqlalchemy import Column, String, Text, Integer, DateTime
from datetime import datetime
from app.database import Base


class TimelinePerson(Base):
    __tablename__ = 'timeline_persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    birth_date = Column(String(50), nullable=True)
    death_date = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    life_span = Column(Integer, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'birth_date': self.birth_date,
            'death_date': self.death_date,
            'bio': self.bio,
            'life_span': self.life_span
        }


class TimelineEvent(Base):
    __tablename__ = 'timeline_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(200), nullable=False)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    event_category = Column(String(50), nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'event_name': self.event_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
            'event_category': self.event_category,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }
