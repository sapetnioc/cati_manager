from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
)

from .meta import Base


class User(Base):
    __tablename__ = 'user'
    login = Column(Text, primary_key=True)
    email = Column(Text)
    first_name = Column(Text)
    last_name = Column(Text)


Index('email_index', User.email, unique=True)
