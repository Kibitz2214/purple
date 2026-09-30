from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean
from typing import Optional, List, TYPE_CHECKING
from models.base import Base, TimestampMixin
import enum


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

if TYPE_CHECKING:
    from models.account import Account
    from models.guardian import Guardian
    from models.report import Report
    from models.notification import Notification


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_vulnerable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 취약계층 여부
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.USER, nullable=False)

    # relationships
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="reporter", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    # 피보호자로서의 관계
    guardian_links: Mapped[List["Guardian"]] = relationship(
        "Guardian", foreign_keys="Guardian.user_id", back_populates="user", cascade="all, delete-orphan"
    )
    # 보호자로서의 관계
    ward_links: Mapped[List["Guardian"]] = relationship(
        "Guardian", foreign_keys="Guardian.guardian_id", back_populates="guardian", cascade="all, delete-orphan"
    )
