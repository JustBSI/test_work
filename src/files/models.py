from datetime import datetime
from sqlalchemy import DateTime
from src.base import Base
from sqlalchemy.orm import mapped_column, Mapped


class File(Base):
    __tablename__ = 'file'

    name: Mapped[str] = mapped_column(nullable=False)
    extension: Mapped[str] = mapped_column(nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)
    path: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    comment: Mapped[str | None] = mapped_column(default=None)

    def __repr__(self) -> str:
        return (f'id={self.id!r}, name={self.name!r}, extension={self.extension!r}, size={self.size!r}, '
                f'path={self.path!r}, created_at={self.created_at!r}, edited_at={self.updated_at!r},'
                f'comment={self.comment!r}')
