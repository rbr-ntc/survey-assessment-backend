"""Add quiz_attempts table

Revision ID: 002_add_quiz_attempts
Revises: 001_initial
Create Date: 2025-12-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '002_add_quiz_attempts'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if tables already exist (idempotent migration)
    conn = op.get_bind()
    
    def table_exists(table_name: str) -> bool:
        try:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :table_name)"
            ), {"table_name": table_name})
            return result.scalar()
        except Exception as e:
            print(f"[migration] Error checking table {table_name}: {e}")
            return False
    
    # Create quiz_attempts table if it doesn't exist
    if not table_exists('quiz_attempts'):
        op.create_table(
            'quiz_attempts',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('quiz_id', sa.String(length=255), nullable=False, comment="Reference to quiz_content._id in MongoDB"),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='in_progress', comment="in_progress | completed | abandoned"),
            sa.Column('score', sa.Integer(), nullable=True, comment="Overall score (0-100)"),
            sa.Column('level', sa.String(length=50), nullable=True, comment="Level determined from score"),
            sa.Column('passed', sa.Boolean(), nullable=True, comment="Whether the quiz was passed"),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('time_spent_seconds', sa.Integer(), nullable=True, comment="Time spent on quiz in seconds"),
            sa.Column('category_scores', sa.Text(), nullable=True, comment="JSON: category scores"),
            sa.Column('strengths', sa.Text(), nullable=True, comment="JSON: list of strong categories"),
            sa.Column('weaknesses', sa.Text(), nullable=True, comment="JSON: list of weak categories"),
            sa.Column('result_content_id', sa.String(length=255), nullable=True, comment="Reference to MongoDB results collection"),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_quiz_attempts_id'), 'quiz_attempts', ['id'], unique=False)
        op.create_index(op.f('ix_quiz_attempts_user_id'), 'quiz_attempts', ['user_id'], unique=False)
        op.create_index(op.f('ix_quiz_attempts_quiz_id'), 'quiz_attempts', ['quiz_id'], unique=False)
        op.create_index(op.f('ix_quiz_attempts_status'), 'quiz_attempts', ['status'], unique=False)
        op.create_index(op.f('ix_quiz_attempts_started_at'), 'quiz_attempts', ['started_at'], unique=False)
        op.create_index(op.f('ix_quiz_attempts_completed_at'), 'quiz_attempts', ['completed_at'], unique=False)
        op.create_index(op.f('ix_quiz_attempts_deleted_at'), 'quiz_attempts', ['deleted_at'], unique=False)
    else:
        print("[migration] Table 'quiz_attempts' already exists, skipping creation")


def downgrade() -> None:
    op.drop_index(op.f('ix_quiz_attempts_deleted_at'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_completed_at'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_started_at'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_status'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_quiz_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_user_id'), table_name='quiz_attempts')
    op.drop_index(op.f('ix_quiz_attempts_id'), table_name='quiz_attempts')
    op.drop_table('quiz_attempts')

