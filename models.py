import enum
from typing import List, Optional
import sys
from datetime import datetime
from sqlalchemy import create_engine, String, Text, DateTime, Enum
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

"""
definitions and variables
"""

class Status(enum.Enum):
    PENDING = 1
    RETRY = 2
    DELIVERED = 3
    RECEIVED = 4
    COMPLETED = 5
    
engine = create_engine("sqlite+pysqlite:///sct.db", echo=True)

class Base(DeclarativeBase):
    pass

# id, sending facility, receiving_facility, content, created_at, delivered_at, status
class MessageQueue(Base):
    __tablename__ = "message_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    sending_facility: Mapped[str] = mapped_column(String(100), nullable=False)
    receiving_facility: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now, nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False)

    def __repr__(self) -> str:
        return f"MessageQueue(id={self.id!r}, sending_facility={self.sending_facility!r}, receiving_facility={self.receiving_facility!r}, content={self.content!r}, created_at={self.created_at!r}, updated_at={self.updated_at!r}, delivered_at={self.delivered_at!r}, status={self.status!r})"

"""
functions
"""

def createTables():
    Base.metadata.create_all(engine)

def insertMessage(sending_facility, receiving_facility, content, status):
    new_message = MessageQueue(sending_facility=sending_facility, receiving_facility=receiving_facility, content=content, status=status)
    session = Session(engine)
    session.add(new_message)
    session.flush()
    session.commit()
    session.close()