"""Add conversation_contexts table for Multi-turn Context Checking

Revision ID: 002_multi_turn_context
Revises: 001_initial_schema
Create Date: 2026-09-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002_multi_turn_context'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'conversation_contexts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('conversation_id', sa.String(), nullable=False, unique=True),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('customer_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('previous_refunds', sa.Text(), default='[]', nullable=False),
        sa.Column('complaint_count', sa.Integer(), default=0, nullable=False),
        sa.Column('order_lookups', sa.Text(), default='{}', nullable=False),
        sa.Column('last_updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_conversation_contexts_conversation_id', 'conversation_contexts', ['conversation_id'])
    op.create_index('ix_conversation_contexts_customer_id', 'conversation_contexts', ['customer_id'])

def downgrade() -> None:
    op.drop_index('ix_conversation_contexts_customer_id', table_name='conversation_contexts')
    op.drop_index('ix_conversation_contexts_conversation_id', table_name='conversation_contexts')
    op.drop_table('conversation_contexts')
