import uuid
from typing import Self,List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.types import RoleType
from core.utils.mixins import UUIDPrimaryKeyMixin
from apps.course.models.course import CourseModel

class FacultyModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "faculties"

    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    phone: Mapped[str] = mapped_column(index=True, unique=True)
    password: Mapped[str] = mapped_column()
    hashed_pass: Mapped[str] = mapped_column()
    dept_name: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()

    courses: Mapped[List["CourseModel"]] = relationship("CourseModel", back_populates="faculty")

    def __str__(self):
        return f"<{self.first_name} {self.last_name}>"
    
    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        password: str,
        hashed_pass: str,
        dept_name: str,
        role: str = RoleType.FACULTY,
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            phone=phone,
            password=password,
            hashed_pass=hashed_pass,
            dept_name= dept_name,
            role=role
        )