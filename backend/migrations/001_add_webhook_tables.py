"""Create webhook and scan profile tables for Phase 1

Revision ID: 001_add_webhook_tables
Revises:
Create Date: 2026-04-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_webhook_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create webhook configuration and event tables."""
    
    # 1. Add trigger_id and started_at columns to scans table
    op.add_column('scans', sa.Column('trigger_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('scans', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('scans', sa.Column('repo_url', sa.Text(), nullable=True))
    op.add_column('scans', sa.Column('violations_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('scans', sa.Column('metadata', sa.JSON(), nullable=True))
    
    # Change status default value to include 'in_progress'
    op.alter_column('scans', 'status',
                    existing_type=sa.String(50),
                    server_default='pending')
    
    # 2. Create webhook_configs table
    op.create_table(
        'webhook_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('webhook_url', sa.Text(), nullable=False),
        sa.Column('webhook_secret', sa.String(255), nullable=False),
        sa.Column('events', sa.JSON(), nullable=False, server_default='["push", "pull_request"]'),
        sa.Column('branches', sa.JSON(), nullable=False, server_default='["main", "master", "develop"]'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_trigger_status', sa.String(50), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_configs_org_id'), 'webhook_configs', ['org_id'])
    op.create_index(op.f('ix_webhook_configs_provider'), 'webhook_configs', ['provider'])
    
    # 3. Create webhook_events table
    op.create_table(
        'webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('webhook_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('repo_url', sa.Text(), nullable=False),
        sa.Column('branch', sa.String(255), nullable=False),
        sa.Column('commit_sha', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='received'),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['webhook_config_id'], ['webhook_configs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_events_webhook_config_id'), 'webhook_events', ['webhook_config_id'])
    op.create_index(op.f('ix_webhook_events_org_id'), 'webhook_events', ['org_id'])
    op.create_index(op.f('ix_webhook_events_commit_sha'), 'webhook_events', ['commit_sha'])
    op.create_index(op.f('ix_webhook_events_status'), 'webhook_events', ['status'])
    
    # 4. Create scan_triggers table
    op.create_table(
        'scan_triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_source', sa.String(50), nullable=True),
        sa.Column('webhook_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ci_pipeline_id', sa.String(255), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['webhook_event_id'], ['webhook_events.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scan_triggers_scan_id'), 'scan_triggers', ['scan_id'])
    op.create_index(op.f('ix_scan_triggers_trigger_type'), 'scan_triggers', ['trigger_type'])
    
    # 5. Add foreign key constraint for trigger_id in scans table
    op.create_foreign_key('fk_scans_trigger_id', 'scans', 'scan_triggers', ['trigger_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_scans_trigger_id'), 'scans', ['trigger_id'])
    
    # 6. Create scan_profiles table
    op.create_table(
        'scan_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scan_on_push', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scan_on_pr', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_approve', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enforcement_level', sa.String(50), nullable=False, server_default='warning'),
        sa.Column('policies', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('notifications', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('max_violations', sa.Integer(), nullable=True),
        sa.Column('min_risk_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scan_profiles_org_id'), 'scan_profiles', ['org_id'])
    op.create_index(op.f('ix_scan_profiles_environment'), 'scan_profiles', ['environment'])


def downgrade() -> None:
    """Downgrade migration - remove webhook tables."""
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_scan_profiles_environment'), table_name='scan_profiles')
    op.drop_index(op.f('ix_scan_profiles_org_id'), table_name='scan_profiles')
    op.drop_table('scan_profiles')
    
    op.drop_index(op.f('ix_scans_trigger_id'), table_name='scans')
    op.drop_constraint('fk_scans_trigger_id', 'scans', type_='foreignkey')
    
    op.drop_index(op.f('ix_scan_triggers_trigger_type'), table_name='scan_triggers')
    op.drop_index(op.f('ix_scan_triggers_scan_id'), table_name='scan_triggers')
    op.drop_table('scan_triggers')
    
    op.drop_index(op.f('ix_webhook_events_status'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_commit_sha'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_org_id'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_webhook_config_id'), table_name='webhook_events')
    op.drop_table('webhook_events')
    
    op.drop_index(op.f('ix_webhook_configs_provider'), table_name='webhook_configs')
    op.drop_index(op.f('ix_webhook_configs_org_id'), table_name='webhook_configs')
    op.drop_table('webhook_configs')
    
    op.drop_column('scans', 'metadata')
    op.drop_column('scans', 'violations_count')
    op.drop_column('scans', 'repo_url')
    op.drop_column('scans', 'started_at')
    op.drop_column('scans', 'trigger_id')
