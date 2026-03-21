"""Add search indexes for better performance

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Индексы для ускорения поиска
    op.create_index('ix_ads_brand_search', 'ads', ['brand'], postgresql_using='gin', 
                    postgresql_ops={'brand': 'gin_trgm_ops'})
    op.create_index('ix_ads_model_search', 'ads', ['model'], postgresql_using='gin',
                    postgresql_ops={'model': 'gin_trgm_ops'})
    
    # Составной индекс для фильтрации по цене и году
    op.create_index('ix_ads_price_year', 'ads', ['price', 'year'], unique=False)
    
    # Включаем расширение pg_trgm для полнотекстового поиска
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')


def downgrade() -> None:
    op.drop_index('ix_ads_price_year', table_name='ads')
    op.drop_index('ix_ads_model_search', table_name='ads')
    op.drop_index('ix_ads_brand_search', table_name='ads')
    # Расширение pg_trgm не удаляем, так как оно может использоваться другими таблицами