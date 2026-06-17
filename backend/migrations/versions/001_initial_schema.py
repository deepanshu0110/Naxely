"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = NOW();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('avatar_url', sa.Text),
        sa.Column('auth_provider', sa.String(50), server_default='email'),
        sa.Column('tier', sa.String(20), server_default='free'),
        sa.Column('tier_expires_at', sa.DateTime(timezone=True)),
        sa.Column('dodo_customer_id', sa.String(255)),
        sa.Column('dodo_subscription_id', sa.String(255)),
        sa.Column('ai_provider', sa.String(20)),
        sa.Column('encrypted_api_key', sa.Text),
        sa.Column('api_key_iv', sa.Text),
        sa.Column('api_key_preview', sa.String(20)),
        sa.Column('logo_url', sa.Text),
        sa.Column('brand_color', sa.String(7), server_default='#6366F1'),
        sa.Column('company_name', sa.String(255)),
        sa.Column('reports_this_month', sa.Integer(), server_default='0'),
        sa.Column('usage_reset_at', sa.DateTime(timezone=True), server_default=sa.text("date_trunc('month', NOW() + interval '1 month')")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    op.execute("""
        CREATE TRIGGER users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
    """)

    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_tier', 'users', ['tier'])
    op.create_index('idx_users_dodo_customer', 'users', ['dodo_customer_id'])

    op.create_table(
        'uploads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_url', sa.Text, nullable=False),
        sa.Column('file_size_bytes', sa.Integer()),
        sa.Column('source_type', sa.String(20), server_default='csv'),
        sa.Column('row_count', sa.Integer()),
        sa.Column('column_count', sa.Integer()),
        sa.Column('columns_meta', postgresql.JSONB(), server_default='[]'),
        sa.Column('expires_at', sa.DateTime(timezone=True), server_default=sa.text("NOW() + interval '24 hours'")),
        sa.Column('used', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_index('idx_uploads_user_id', 'uploads', ['user_id'])
    op.create_index('idx_uploads_expires_at', 'uploads', ['expires_at'], postgresql_where=sa.text('used = FALSE'))

    op.create_table(
        'workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('client_name', sa.String(255)),
        sa.Column('logo_url', sa.Text),
        sa.Column('brand_color', sa.String(7)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_index('idx_workspaces_owner_id', 'workspaces', ['owner_id'])

    op.execute("""
        CREATE TRIGGER workspaces_updated_at
        BEFORE UPDATE ON workspaces
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
    """)

    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='SET NULL')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('template_type', sa.String(50), server_default='marketing'),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('source_type', sa.String(20), server_default='csv'),
        sa.Column('source_url', sa.Text),
        sa.Column('source_filename', sa.String(255)),
        sa.Column('row_count', sa.Integer()),
        sa.Column('column_count', sa.Integer()),
        sa.Column('config', postgresql.JSONB(), server_default='{}'),
        sa.Column('pdf_url', sa.Text),
        sa.Column('ppt_url', sa.Text),
        sa.Column('share_token', sa.String(64)),
        sa.Column('share_expires_at', sa.DateTime(timezone=True)),
        sa.Column('share_view_count', sa.Integer(), server_default='0'),
        sa.Column('ai_summary', sa.Text),
        sa.Column('ai_insights', postgresql.JSONB(), server_default='[]'),
        sa.Column('ai_anomalies', postgresql.JSONB(), server_default='[]'),
        sa.Column('generation_time_seconds', sa.Float()),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    op.create_index('idx_reports_user_id', 'reports', ['user_id'])
    op.create_index('idx_reports_status', 'reports', ['status'])
    op.create_index('idx_reports_created_at', 'reports', ['created_at'])
    op.create_index('idx_reports_share_token', 'reports', ['share_token'])
    op.execute("""
        CREATE UNIQUE INDEX idx_reports_share_token_unique
        ON reports (share_token) WHERE share_token IS NOT NULL;
    """)

    op.execute("""
        CREATE TRIGGER reports_updated_at
        BEFORE UPDATE ON reports
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
    """)

    op.create_table(
        'templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('template_type', sa.String(50), server_default='marketing'),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_index('idx_templates_user_id', 'templates', ['user_id'])

    op.execute("""
        CREATE TRIGGER templates_updated_at
        BEFORE UPDATE ON templates
        FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
    """)

    op.create_table(
        'workspace_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), server_default='member'),
        sa.Column('invited_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('workspace_id', 'user_id'),
    )

    op.create_table(
        'payment_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('dodo_event_id', sa.String(255), unique=True),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('processed', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_index('idx_payment_events_user_id', 'payment_events', ['user_id'])
    op.create_index('idx_payment_events_type', 'payment_events', ['event_type'])
    op.execute("""
        CREATE UNIQUE INDEX idx_payment_events_dodo_id
        ON payment_events (dodo_event_id);
    """)

    op.create_table(
        'scheduled_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('templates.id', ondelete='SET NULL')),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='SET NULL')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('frequency', sa.String(20), nullable=False),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True)),
        sa.Column('sheets_url', sa.Text),
        sa.Column('recipient_emails', postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.execute("""
        CREATE INDEX idx_scheduled_reports_next_run
        ON scheduled_reports (next_run_at) WHERE is_active = TRUE;
    """)


def downgrade() -> None:
    op.drop_table('scheduled_reports')
    op.drop_table('payment_events')
    op.drop_table('workspace_members')
    op.drop_table('templates')
    op.drop_table('reports')
    op.drop_table('workspaces')
    op.drop_table('uploads')
    op.drop_table('users')
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
