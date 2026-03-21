"""Add phone verification fields

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поля для верификации телефона
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('phone_verification_code', sa.String(length=6), nullable=True))
    op.add_column('users', sa.Column('phone_verification_expires', sa.DateTime(timezone=True), nullable=True))
    
    # Добавляем поле для количества попыток верификации
    op.add_column('users', sa.Column('verification_attempts', sa.Integer(), server_default='0', nullable=False))
    
    # Добавляем индекс для быстрого поиска по телефону
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_column('users', 'verification_attempts')
    op.drop_column('users', 'phone_verification_expires')
    op.drop_column('users', 'phone_verification_code')
    op.drop_column('users', 'phone_verified')