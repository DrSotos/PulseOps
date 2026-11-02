"""Initial schema migration for PulseOps.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-11-02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. monitored_endpoints
    op.create_table(
        'monitored_endpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('http_method', sa.String(10), server_default='GET', nullable=False),
        sa.Column('monitoring_interval', sa.Integer(), server_default='60', nullable=False),
        sa.Column('timeout', sa.Integer(), server_default='10', nullable=False),
        sa.Column('expected_status_codes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('performance_threshold_ms', sa.Integer(), nullable=True),
        sa.Column('custom_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('expected_content', sa.String(1024), nullable=True),
        sa.Column('expected_content_type', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_monitored_endpoints_user_id', 'monitored_endpoints', ['user_id'])

    # 3. monitoring_checks
    op.create_table(
        'monitoring_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('endpoint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('monitored_endpoints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=False),
        sa.Column('failure_type', sa.String(50), nullable=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('response_size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_monitoring_checks_endpoint_id', 'monitoring_checks', ['endpoint_id'])
    op.create_index('ix_monitoring_checks_created_at', 'monitoring_checks', ['created_at'])

    # 4. incidents
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('endpoint_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('monitored_endpoints.id', ondelete='CASCADE'), nullable=False),
        sa.Column('incident_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='open', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_incidents_endpoint_id', 'incidents', ['endpoint_id'])
    op.create_index('ix_incidents_status', 'incidents', ['status'])

    # 5. incident_events
    op.create_table(
        'incident_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_incident_events_incident_id', 'incident_events', ['incident_id'])

    # 6. notification_channels
    op.create_table(
        'notification_channels',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('channel_type', sa.String(50), nullable=False),
        sa.Column('destination', sa.String(1024), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_notification_channels_user_id', 'notification_channels', ['user_id'])

    # 7. notification_deliveries
    op.create_table(
        'notification_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('notification_channels.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('delivery_status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_notification_deliveries_incident_id', 'notification_deliveries', ['incident_id'])
    op.create_index('ix_notification_deliveries_channel_id', 'notification_deliveries', ['channel_id'])


def downgrade() -> None:
    op.drop_table('notification_deliveries')
    op.drop_table('notification_channels')
    op.drop_table('incident_events')
    op.drop_table('incidents')
    op.drop_table('monitoring_checks')
    op.drop_table('monitored_endpoints')
    op.drop_table('users')

