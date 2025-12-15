"""
PostgreSQL models for users, authentication, and transactional data.
Following DATABASE_SCHEMA.md requirements: UUIDv7, soft delete, audit fields.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_postgres import Base


def generate_uuid7():
    """Generate UUIDv7 (time-sortable UUID)"""
    # For now using UUIDv4, but should be replaced with UUIDv7 when available
    # UUIDv7 is time-sortable and better for database indexes
    return uuid.uuid4()


class User(Base):
    """
    User model - PostgreSQL
    Stores user accounts, authentication, and basic profile info.
    """
    __tablename__ = "users"

    # Primary key - UUIDv7 (time-sortable)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid7,
        index=True,
    )

    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # NULL for OAuth-only users
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Profile
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="student",  # student | author | admin
        index=True,
    )

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Relationships
    refresh_tokens: Mapped[list["AuthRefreshToken"]] = relationship(
        "AuthRefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    verification_codes: Mapped[list["VerificationCode"]] = relationship(
        "VerificationCode",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class AuthRefreshToken(Base):
    """
    Refresh token model for JWT authentication.
    Stores refresh tokens with expiration and revocation.
    """
    __tablename__ = "auth_refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid7,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<AuthRefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class VerificationCode(Base):
    """
    Verification code model for email verification and password reset.
    Stores 6-digit codes with expiration.
    """
    __tablename__ = "verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid7,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(String(6), nullable=False, index=True)  # 6-digit code
    code_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # email_verification | password_reset
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="verification_codes")

    def __repr__(self):
        return f"<VerificationCode(id={self.id}, user_id={self.user_id}, code_type={self.code_type}, expires_at={self.expires_at})>"


class QuizAttempt(Base):
    """
    Quiz attempt model - PostgreSQL
    Stores quiz attempts and results linked to users.
    """
    __tablename__ = "quiz_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid7,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quiz_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Reference to quiz_content._id in MongoDB (e.g., 'quiz:system-analyst-assessment')",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="in_progress",
        index=True,
        comment="in_progress | completed | abandoned",
    )

    score: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Overall score (0-100)",
    )

    level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Level determined from score (e.g., 'junior', 'middle', 'senior')",
    )

    passed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether the quiz was passed (score >= passing_score)",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    time_spent_seconds: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Time spent on quiz in seconds",
    )

    # Category scores and analysis (JSONB for flexibility)
    category_scores: Mapped[Optional[dict]] = mapped_column(
        type_=Text,
        nullable=True,
        comment="JSON: category scores as {category: score}",
    )

    strengths: Mapped[Optional[dict]] = mapped_column(
        type_=Text,
        nullable=True,
        comment="JSON: list of strong categories",
    )

    weaknesses: Mapped[Optional[dict]] = mapped_column(
        type_=Text,
        nullable=True,
        comment="JSON: list of weak categories",
    )

    # Link to detailed results in MongoDB (optional)
    result_content_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Reference to MongoDB results collection _id for detailed results",
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self):
        return f"<QuizAttempt(id={self.id}, user_id={self.user_id}, quiz_id={self.quiz_id}, status={self.status}, score={self.score})>"

