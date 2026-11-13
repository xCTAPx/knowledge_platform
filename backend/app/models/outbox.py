from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))
    item_id: Mapped[int] = mapped_column(Integer)
    gen: Mapped[int] = mapped_column(Integer, default=0)
