"""add_game_mode_to_player_stats_pk

Revision ID: 8376fc61ca90
Revises: a6607aae6f3c
Create Date: 2025-05-07 18:47:33.706690

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8376fc61ca90'
down_revision = 'a6607aae6f3c' # Make sure this matches your previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add the new column as nullable
    with op.batch_alter_table('player_stats', schema=None) as batch_op:
        batch_op.add_column(sa.Column('game_mode', sa.String(length=50), nullable=True))

    # Step 2: Populate the new column for existing rows.
    op.execute("UPDATE player_stats SET game_mode = 'Classic' WHERE game_mode IS NULL")

    # Step 3: Alter the column to be non-nullable
    with op.batch_alter_table('player_stats', schema=None) as batch_op:
        batch_op.alter_column('game_mode',
               existing_type=sa.String(length=50),
               nullable=False)

    # Step 4: Recreate primary key as composite.
    # For SQLite, batch_alter_table handles PK changes by recreating the table.
    # Simply defining the new primary key should be sufficient.
    with op.batch_alter_table('player_stats', schema=None) as batch_op:
        # Define the new composite primary key
        # The old PK is implicitly handled by SQLite's table recreation in batch mode.
        batch_op.create_primary_key('pk_player_stats', ['player_uuid', 'game_mode'])


def downgrade():
    with op.batch_alter_table('player_stats', schema=None) as batch_op:
        # Drop the composite primary key
        # For SQLite, batch_alter_table will recreate the table.
        # We need to tell it what the new PK should be after dropping the composite one.
        batch_op.drop_constraint('pk_player_stats', type_='primary')
        
        # Drop the game_mode column
        batch_op.drop_column('game_mode')
        
        # Recreate the old primary key on player_uuid only
        # The name 'pk_player_stats' here is what we want the new (old-style) PK to be named.
        batch_op.create_primary_key('pk_player_stats_downgrade', ['player_uuid']) # Use a distinct name if issues arise, or stick to 'pk_player_stats'
