"""
Add enable_tax column to pos_settings table

This script adds the enable_tax column to the pos_settings table
to support toggling tax calculation in the POS system.
"""
from sqlalchemy import Column, Boolean
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add enable_tax column to pos_settings table
    op.add_column('pos_settings', sa.Column('enable_tax', sa.Boolean(), nullable=True, server_default='0'))
    
    # Set default value for existing rows
    op.execute("UPDATE pos_settings SET enable_tax = 0")

def downgrade():
    # Remove enable_tax column from pos_settings table
    op.drop_column('pos_settings', 'enable_tax')
