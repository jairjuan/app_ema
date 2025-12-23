"""add entity_type and code to production_events and backfill from piece_code

Revision ID: 20251223_add_entity_type_and_code
Revises: 
Create Date: 2025-12-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251223_add_entity_type_and_code'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # check existing columns
    result = conn.execute(sa.text("PRAGMA table_info('production_events')")).fetchall()
    cols = [r[1] for r in result]

    # Add new columns only if missing
    to_add = []
    if 'entity_type' not in cols:
        to_add.append(sa.Column('entity_type', sa.String(), nullable=True))
    if 'code' not in cols:
        to_add.append(sa.Column('code', sa.String(), nullable=True))

    if to_add:
        with op.batch_alter_table('production_events') as batch_op:
            for c in to_add:
                batch_op.add_column(c)

    # create index on code if not present
    if 'code' in cols or any(getattr(c, 'name', None) == 'code' for c in to_add):
        # check if index exists
        idxs = conn.execute(sa.text("PRAGMA index_list('production_events')")).fetchall()
        idx_names = [r[1] for r in idxs]
        if 'ix_production_events_code' not in idx_names:
            op.create_index(op.f('ix_production_events_code'), 'production_events', ['code'], unique=False)

    # Backfill data from old column if present
    if 'piece_code' in cols:
        conn.execute(sa.text("UPDATE production_events SET entity_type = 'PIECE', code = piece_code WHERE piece_code IS NOT NULL AND piece_code != ''"))


def downgrade():
    # remove index
    op.drop_index(op.f('ix_production_events_code'), table_name='production_events')
    # drop columns (using batch_alter_table for sqlite safety)
    with op.batch_alter_table('production_events') as batch_op:
        batch_op.drop_column('code')
        batch_op.drop_column('entity_type')
