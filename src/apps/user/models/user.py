from uuid import UUID
import uuid
from typing import Self

from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base
from core.enum import LanguageEnum
from core.utils.mixins import TimeStampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import ForeignKey
from sqlalchemy import Enum


class UserModel(Base, UUIDPrimaryKeyMixin, TimeStampMixin):
    """
    Model for representing user information.

    This SQLAlchemy model represents user information, including fields such as first_name, last_name, email, phone,
    password, and role. It is used to store and manage user data in the application's database.

    Attributes:
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        email (str): The user's email address (unique).
        phone (str): The user's phone number (unique).
        password (str): The user's hashed password.
        role (int): The user's role identifier.
    """

    __tablename__ = "users"
    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    phone: Mapped[str] = mapped_column(index=True, unique=True)
    password: Mapped[str] = mapped_column()
    # role: Mapped[RoleType] = mapped_column()
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_activated: Mapped[bool] = mapped_column(default=True, nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"))
    preferred_language: Mapped[LanguageEnum] = mapped_column(Enum(LanguageEnum, name="languageenum",create_type=False,
                                                                  values_callable=lambda enum: [e.value for e in enum]), nullable=True)

    role_ref: Mapped["RoleModel"] = relationship("RoleModel", back_populates="users")
    courses = relationship("CourseModel", secondary="association", back_populates="students", lazy="selectin")
    faculty_courses = relationship("CourseModel", back_populates="faculty")

    def __str__(self) -> str:
        """
        Return a string representation of the user.

        :return: A string with the user's first and last name.
        """
        return f"<{self.first_name} {self.last_name}>"
    
    @property
    def role(self) -> str | None:
        """
        Convenience property to get the user's role name.

        Returns:
            Optional[str]: The role string from the related RoleModel, or None
            if no role is associated.
        """
        return self.role_ref.role if self.role_ref else None

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        password: str,
        role_id: int,
        preferred_language: LanguageEnum
    ) -> Self:
        """
        Create a new user.

        :param first_name: The user's first name.
        :param last_name: The user's last name.
        :param phone: The user's phone number.
        :param email: The user's email address.
        :param password: The user's hashed password.
        :param role: The user's role identifier. Defaults to RoleType.USER.
        :return: An instance of UserModel.
        """
        return cls(
            id=uuid.uuid4(),
            first_name=first_name,
            last_name=last_name,
            email=email.lower(),
            phone=phone,
            password=password,
            role_id=role_id,
            preferred_language=preferred_language
        )
    




class RoleModel(Base):
    """
    Model representing user roles.

    Each role has a unique name and may be referenced by multiple users through
    a foreign key relationship.
    """
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(index=True, unique=True)

    users: Mapped[list[UserModel]] = relationship("UserModel", back_populates="role_ref")

    def __str__(self) -> str:
        return f"<{self.role}>"