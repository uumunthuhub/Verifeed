"""enhance institution registry with official channels

Revision ID: enhance_institution_registry
Revises: 3bf2588aef25
Create Date: 2026-09-13

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'enhance_institution_registry'
down_revision = '5a56bc5f4dd4'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to institutions table
    op.add_column('institutions', sa.Column('official_phone_numbers', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('official_sms_sender_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('official_short_codes', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('official_ussd_codes', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('official_email_domains', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('verified_social_accounts', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('customer_care_channels', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('fraud_reporting_channels', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('legitimate_message_templates', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('institutions', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove the new columns
    op.drop_column('institutions', 'legitimate_message_templates')
    op.drop_column('institutions', 'fraud_reporting_channels')
    op.drop_column('institutions', 'customer_care_channels')
    op.drop_column('institutions', 'verified_social_accounts')
    op.drop_column('institutions', 'official_email_domains')
    op.drop_column('institutions', 'official_ussd_codes')
    op.drop_column('institutions', 'official_short_codes')
    op.drop_column('institutions', 'official_sms_sender_ids')
    op.drop_column('institutions', 'official_phone_numbers')
    op.drop_column('institutions', 'updated_at')
