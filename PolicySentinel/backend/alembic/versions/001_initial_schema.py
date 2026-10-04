"""Initial schema migration for AegisAI

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-25 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. conversations
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('customer_id', sa.String(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 2. messages
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('conversation_id', sa.String(), sa.ForeignKey('conversations.id'), nullable=False, index=True),
        sa.Column('sender', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 3. policies
    op.create_table(
        'policies',
        sa.Column('policy_id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 4. policy_versions
    op.create_table(
        'policy_versions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('policy_id', sa.String(), sa.ForeignKey('policies.policy_id'), nullable=False, index=True),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('definition_yaml', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 5. audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('request_id', sa.String(), nullable=False, index=True),
        sa.Column('conversation_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_message', sa.Text(), nullable=False),
        sa.Column('agent_a_response', sa.Text(), nullable=True),
        sa.Column('proposed_action', sa.Text(), nullable=True),
        sa.Column('agent_b_action', sa.Text(), nullable=True),
        sa.Column('policy_id', sa.String(), nullable=True, index=True),
        sa.Column('policy_version', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('decision', sa.String(), nullable=False, index=True),
        sa.Column('safe_response', sa.Text(), nullable=True),
        sa.Column('tool_executed', sa.Boolean(), nullable=False, default=False),
        sa.Column('tool_result', sa.Text(), nullable=True),
        sa.Column('escalation_status', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
    )

    # 6. incidents
    op.create_table(
        'incidents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('request_id', sa.String(), nullable=False, index=True),
        sa.Column('conversation_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_id', sa.String(), nullable=False, index=True),
        sa.Column('customer_message', sa.Text(), nullable=False),
        sa.Column('agent_a_proposal', sa.Text(), nullable=True),
        sa.Column('policy_id', sa.String(), nullable=False, index=True),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('decision', sa.String(), nullable=False),
        sa.Column('safe_response', sa.Text(), nullable=True),
        sa.Column('escalation_status', sa.String(), nullable=False, default="PENDING"),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 7. approvals
    op.create_table(
        'approvals',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('decision_id', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('request_id', sa.String(), nullable=False, index=True),
        sa.Column('conversation_id', sa.String(), nullable=False, index=True),
        sa.Column('policy_id', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('proposed_action', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default="PENDING"),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('approvals')
    op.drop_table('incidents')
    op.drop_table('audit_events')
    op.drop_table('policy_versions')
    op.drop_table('policies')
    op.drop_table('messages')
    op.drop_table('conversations')
