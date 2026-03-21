"""Add user stats and views tracking

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле для статистики пользователя
    op.add_column('users', sa.Column('total_views', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('total_ads', sa.Integer(), server_default='0', nullable=False))
    
    # Добавляем поле для хранения последнего IP (опционально)
    op.add_column('users', sa.Column('last_ip', sa.String(length=45), nullable=True))
    
    # Добавляем индекс для быстрого поиска по is_active
    op.create_index(op.f('ix_ads_is_active'), 'ads', ['is_active'], unique=False)
    
    # Добавляем индекс для created_at для сортировки
    op.create_index(op.f('ix_ads_created_at'), 'ads', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ads_created_at'), table_name='ads')
    op.drop_index(op.f('ix_ads_is_active'), table_name='ads')
    op.drop_column('users', 'last_ip')
    op.drop_column('users', 'total_ads')
    op.drop_column('users', 'total_views')