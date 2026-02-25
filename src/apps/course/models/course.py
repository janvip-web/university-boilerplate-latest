import uuid
from uuid import UUID
from typing import Self, TYPE_CHECKING,List
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy import Enum, func

from core.db import Base
from core.utils.mixins import UUIDPrimaryKeyMixin
from core.enum import LanguageEnum


class CourseModel(Base, UUIDPrimaryKeyMixin):
    __tablename__="courses"

    course_name: Mapped[str] = mapped_column(index=True)
    course_credit: Mapped[int] = mapped_column()
    course_description: Mapped[str] = mapped_column(nullable=True)
    faculty_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=func.now(), nullable=True
    )

    students = relationship("UserModel", secondary="association", back_populates="courses", lazy="selectin")
    faculty = relationship("UserModel", back_populates="faculty_courses")
    translations: Mapped[List["CourseTranslationModel"]] = relationship("CourseTranslationModel", back_populates="course", cascade="all, delete-orphan")

    def __str__(self):
        return f"<Course {self.course_name}>"

    @classmethod
    def create(
        cls,
        course_name: str,
        course_credit: int,
        course_description: str | None = None,
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            course_name=course_name,
            course_credit=course_credit,
            course_description=course_description,
        )
    

class CourseTranslationModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "course_translations"

    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    course_name: Mapped[str] = mapped_column(index=True)
    language_code: Mapped[LanguageEnum] = mapped_column(
        Enum(
            LanguageEnum,
            name="languageenum",   # must match existing DB enum type
            create_type=False ,     # 🔥 prevents duplicate enum creation
            values_callable=lambda enum: [e.value for e in enum]
        ),
        nullable=False )

    __table_args__ = (
            UniqueConstraint("course_id", "language_code", name="uq_course_language"),
    )

    course: Mapped["CourseModel"] = relationship("CourseModel", back_populates="translations")

    # @classmethod
    # def create(
    #     cls
    # )


class Association(Base, UUIDPrimaryKeyMixin):
    __tablename__="association"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
   


    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "course_id",
            name="uq_user_course"
        ),
    )

    @classmethod
    def create(
        cls,
        user_id: UUID,
        course_id: UUID,
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            course_id=course_id,
        )