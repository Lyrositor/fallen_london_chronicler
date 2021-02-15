from sqlalchemy import String, Column

from fallen_london_chronicler.model import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    key = Column(String, primary_key=True)
    user_name = Column(String, nullable=False)
