import enum
from typing import List, Optional
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now, nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[Status] = mapped_column(Enum(Status), nullable=False)

    def __repr__(self) -> str:
        return f"MessageQueue(id={self.id!r}, sending_facility={self.sending_facility!r}, receiving_facility={self.receiving_facility!r}, content={self.content!r}, created_at={self.created_at!r}, updated_at={self.updated_at!r}, delivered_at={self.delivered_at!r}, status={self.status!r})"

"""
functions
"""

def createTables():
    Base.metadata.create_all(engine)

# function to insert a new message
# Parameters:
#   1. sending_facility - str
#   2. receiving_facility - str
#   3. content - str: A JSON string that containing 3 fields e.g., {"sending_facility":"AUXXREFSCR", "receiving_facility": "DIDGUGO", "content":"XXXX"}
#   4. status - str: One of the following: PENDING, RETRY, DELIVERED, RECEIVED, COMPLETED
def insertMessage(sending_facility, receiving_facility, content, status):
    try:
        new_message = MessageQueue(sending_facility=sending_facility, receiving_facility=receiving_facility, content=content, status=status)
        session = Session(engine)
        session.add(new_message)
        session.flush()
        session.commit()
    except Exception as error:
        print("An exception occured: ", error)
    finally:
        session.close()

# function to update a message based on the id
# Parameters:
#   1. id - int: row id
#   2. changes - dict: a dictionary containing all the changed columns, each pair of the key-value pairs is a pair of column name and changed value of the column
def updateMessage(id: int, changes: dict):
    try:
        session = Session(engine)
        message = session.get(MessageQueue, id)
        if not message:
            raise Exception(f"The row id {id} does not exist in the table message_queue")
        
        for column_name, column_value in changes.items():
            setattr(message, column_name, column_value)

        session.flush()
        session.commit()
    except Exception as error:
        print("An exception occured: ", error)
    finally:
        session.close()

# function to delete a message based on the id
# Parameters:
#   1. id - int: row id 
def deleteMessage(id: int):
    try:
        session = Session(engine)
        message = session.get(MessageQueue, id)
        if not message:
            raise Exception(f"The row id {id} does not exist in the table message_queue")
        
        session.delete(message)

        session.flush()
        session.commit()
    except Exception as error:
        print("An exception occured: ", error)
    finally:
        session.close()