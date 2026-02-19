import uuid
from uuid import UUID
from typing import Self, TYPE_CHECKING,List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint

from core.db import Base
from core.types import RoleType
from core.utils.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from apps.student.models.student import StudentModel
    from apps.faculty.models.faculty import FacultyModel

class CourseModel(Base, UUIDPrimaryKeyMixin):
    __tablename__="courses"

    course_name: Mapped[str] = mapped_column(index=True)
    course_credit: Mapped[int] = mapped_column()
    faculty_id: Mapped[UUID] = mapped_column(ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True)
    # student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id",ondelete="SET NULL", onupdate="CASCADE"),  nullable=True)
    # faculty_id: Mapped[UUID] = mapped_column(ForeignKey("faculties.id"))

    # student: Mapped["StudentModel"] = relationship("StudentModel", back_populates="courses")
    faculty: Mapped["FacultyModel"] = relationship("FacultyModel", back_populates="courses")

    students: Mapped[List["StudentModel"]] = relationship("StudentModel",secondary="association", back_populates="courses", lazy="selectin")
    # faculty: Mapped["FacultyModel"] = relationship("FacultyModel", back_populates="courses")

    def __str__(self):
        return f"<Course {self.course_name}>"

    @classmethod
    def create(
        cls,
        # student_id: UUID,
        # faculty_id: UUID,
        course_name: str,
        course_credit: int,
        faculty_id: UUID | None = None
    ) -> Self:
        return cls(
            id=uuid.uuid4(),
            # student_id=student_id,
            faculty_id=faculty_id,
            course_name=course_name,
            course_credit=course_credit,
        )
    




class Association(Base, UUIDPrimaryKeyMixin):
    __tablename__="association"

    student_id: Mapped[UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    # faculty_id: Mapped[UUID] = mapped_column(ForeignKey("faculties.id"))


    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_student_course"
        ),
    )

    @classmethod
    def create(
        cls,
        student_id: UUID,
        course_id: UUID,
    ) -> Self:
        return cls(
            # id=uuid.uuid4(),
            student_id=student_id,
            course_id=course_id,
        )