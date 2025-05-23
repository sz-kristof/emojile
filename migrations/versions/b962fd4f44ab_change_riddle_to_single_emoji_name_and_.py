"""Change Riddle to single emoji name and category

Revision ID: b962fd4f44ab
Revises: 7a52c7c080db
Create Date: 2025-05-04 15:27:33.475533

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b962fd4f44ab'
down_revision = '7a52c7c080db'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('riddle', schema=None) as batch_op:
        # Add columns as nullable initially
        batch_op.add_column(sa.Column('emoji', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('category', sa.String(length=50), nullable=True))

        # Drop old columns BEFORE trying to make new ones non-nullable if copying data
        # (Order matters less here as batch mode copies first, then applies constraints usually)
        batch_op.drop_column('emojis')
        batch_op.drop_column('answer')

        # Create constraint (name added previously)
        batch_op.create_unique_constraint('uq_riddle_emoji', ['emoji'])

        # Now, alter columns to be non-nullable AFTER the implicit data copy
        # Note: This assumes you will repopulate. If you needed to keep old data,
        # you'd need to add UPDATE statements here before making them non-nullable.
        batch_op.alter_column('emoji', existing_type=sa.String(length=10), nullable=False)
        batch_op.alter_column('name', existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column('category', existing_type=sa.String(length=50), nullable=False)


    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('riddle', schema=None) as batch_op:
        # Add old columns back (assuming they were non-nullable)
        batch_op.add_column(sa.Column('answer', sa.VARCHAR(length=200), nullable=False))
        batch_op.add_column(sa.Column('emojis', sa.VARCHAR(length=100), nullable=False))

        # Drop constraint using the correct name
        batch_op.drop_constraint('uq_riddle_emoji', type_='unique')

        # Drop the new columns
        batch_op.drop_column('category')
        batch_op.drop_column('name')
        batch_op.drop_column('emoji')

    # ### end Alembic commands ###
