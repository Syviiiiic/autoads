"""Add ad promotion and featured status

Revision ID: 006
Revises: 005
Create Date: 2024-01-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем статус VIP/продвижения
    op.add_column('ads', sa.Column('is_featured', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('ads', sa.Column('featured_until', sa.DateTime(timezone=True), nullable=True))
    
    # Добавляем поле для типа продвижения
    op.add_column('ads', sa.Column('promotion_type', sa.String(length=20), nullable=True))
    
    # Индекс для быстрого поиска продвигаемых объявлений
    op.create_index(op.f('ix_ads_is_featured'), 'ads', ['is_featured'], unique=False)
    
    # Создаём таблицу для истории продвижений
    op.create_table(
        'ad_promotions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ad_id', sa.Integer(), nullable=False),
        sa.Column('promotion_type', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('price_paid', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['ad_id'], ['ads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ad_promotions_ad_id'), 'ad_promotions', ['ad_id'], unique=False)


def downgrade() -> None:
    op.drop_table('ad_promotions')
    op.drop_index(op.f('ix_ads_is_featured'), table_name='ads')
    op.drop_column('ads', 'promotion_type')
    op.drop_column('ads', 'featured_until')
    op.drop_column('ads', 'is_featured')