"""Add ad expiration date

Revision ID: 005
Revises: 004
Create Date: 2024-01-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем дату истечения объявления (по умолчанию через 30 дней)
    op.add_column('ads', sa.Column('expires_at', sa.DateTime(timezone=True), 
                                    server_default=sa.text("now() + interval '30 days'"), nullable=True))
    
    # Добавляем поле для автоматического продления
    op.add_column('ads', sa.Column('auto_renew', sa.Boolean(), server_default='false', nullable=False))
    
    # Индекс для поиска истекающих объявлений
    op.create_index(op.f('ix_ads_expires_at'), 'ads', ['expires_at'], unique=False)
    
    # Добавляем поле для количества продлений
    op.add_column('ads', sa.Column('renew_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_index(op.f('ix_ads_expires_at'), table_name='ads')
    op.drop_column('ads', 'renew_count')
    op.drop_column('ads', 'auto_renew')
    op.drop_column('ads', 'expires_at')