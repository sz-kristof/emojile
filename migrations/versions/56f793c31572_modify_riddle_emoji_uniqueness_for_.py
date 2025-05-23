"""Modify Riddle.emoji uniqueness for multi-mode support

Revision ID: 56f793c31572
Revises: 1358e899cec4
Create Date: 2025-05-06 18:11:08.271554

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '56f793c31572'
down_revision = '1358e899cec4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('riddle', schema=None) as batch_op:
        batch_op.drop_constraint('uq_riddle_emoji', type_='unique')
        batch_op.create_unique_constraint('uq_emoji_game_mode', ['emoji', 'game_mode'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('riddle', schema=None) as batch_op:
        batch_op.drop_constraint('uq_emoji_game_mode', type_='unique')
        batch_op.create_unique_constraint('uq_riddle_emoji', ['emoji'])

    # ### end Alembic commands ###
