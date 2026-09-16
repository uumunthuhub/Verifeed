"""add dual verdict system to verification logs

Revision ID: add_dual_verdict_system
Revises: enhance_institution_registry
Create Date: 2026-09-13

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_dual_verdict_system'
down_revision = 'enhance_institution_registry'
branch_labels = None
depends_on = None


def upgrade():
    # Add dual verdict columns
    op.add_column('verification_logs', sa.Column('claim_verdict', sa.String(length=50), nullable=True))
    op.add_column('verification_logs', sa.Column('message_authenticity_verdict', sa.String(length=50), nullable=True))
    
    # Add risk level
    op.add_column('verification_logs', sa.Column('risk_level', sa.String(length=20), nullable=True))
    
    # Add extracted entity columns
    op.add_column('verification_logs', sa.Column('extracted_sender', sa.String(length=255), nullable=True))
    op.add_column('verification_logs', sa.Column('extracted_numbers', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('verification_logs', sa.Column('extracted_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('verification_logs', sa.Column('extracted_institutions', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add verification result columns
    op.add_column('verification_logs', sa.Column('sender_verified', sa.Boolean(), nullable=True))
    op.add_column('verification_logs', sa.Column('channel_verified', sa.Boolean(), nullable=True))
    
    # Add user guidance column
    op.add_column('verification_logs', sa.Column('recommended_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Create indexes for new verdict columns
    op.create_index('ix_verification_logs_claim_verdict', 'verification_logs', ['claim_verdict'])
    op.create_index('ix_verification_logs_message_authenticity_verdict', 'verification_logs', ['message_authenticity_verdict'])


def downgrade():
    # Remove indexes
    op.drop_index('ix_verification_logs_message_authenticity_verdict', table_name='verification_logs')
    op.drop_index('ix_verification_logs_claim_verdict', table_name='verification_logs')
    
    # Remove columns
    op.drop_column('verification_logs', 'recommended_actions')
    op.drop_column('verification_logs', 'channel_verified')
    op.drop_column('verification_logs', 'sender_verified')
    op.drop_column('verification_logs', 'extracted_institutions')
    op.drop_column('verification_logs', 'extracted_urls')
    op.drop_column('verification_logs', 'extracted_numbers')
    op.drop_column('verification_logs', 'extracted_sender')
    op.drop_column('verification_logs', 'risk_level')
    op.drop_column('verification_logs', 'message_authenticity_verdict')
    op.drop_column('verification_logs', 'claim_verdict')
