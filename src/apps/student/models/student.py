import uuid
from typing import Self
from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.types import RoleType
from core.utils.mixins import UUIDPrimaryKeyMixin
from apps.course.models.course import CourseModel

class StudentModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "students"

    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    phone: Mapped[str] = mapped_column(index=True, unique=True)
    password: Mapped[str] = mapped_column()
    hashed_pass: Mapped[str] = mapped_column()
    dob: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()

    courses: Mapped[List["CourseModel"]] = relationship("CourseModel",secondary="association", back_populates="students",   lazy="selectin")

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
        dob: str,
        role: str = RoleType.STUDENT,
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            phone=phone,
            password=password,
            hashed_pass=hashed_pass,
            dob = dob,
            role=role
        )