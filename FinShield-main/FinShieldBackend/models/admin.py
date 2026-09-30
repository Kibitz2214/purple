from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from models.base import Base, TimestampMixin


class Admin(Base, TimestampMixin):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    permission_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # 1 = 일반 관리자, 2 = 슈퍼 관리자
