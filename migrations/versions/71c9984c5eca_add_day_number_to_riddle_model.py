"""Add day_number to Riddle model

Revision ID: 71c9984c5eca
Revises: 6443e7c48233
Create Date: 2025-05-05 16:25:06.161400

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, String, select, update, func


# revision identifiers, used by Alembic.
revision = '71c9984c5eca'
down_revision = '6443e7c48233'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # This block correctly adds the column and index for SQLite
    with op.batch_alter_table('riddle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('day_number', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_riddle_day_number'), ['day_number'], unique=True)

    # --- Code to populate day_number for existing rows ---
    # Define minimal table structure for the update
    riddle_table = table('riddle',
        column('id', Integer),
        column('day_number', Integer)
    )
    conn = op.get_bind()
    # Select existing riddles ordered by ID (or another stable order)
    # Filter for those where day_number IS NULL to avoid re-assigning
    select_stmt = select(riddle_table.c.id)\
        .where(riddle_table.c.day_number.is_(None))\
        .order_by(riddle_table.c.id)

    results = conn.execute(select_stmt).fetchall()

    # Find the current max day_number to continue from
    max_day_num_result = conn.execute(select(func.max(riddle_table.c.day_number))).scalar()
    current_day_num = (max_day_num_result + 1) if max_day_num_result is not None else 0

    print(f"\nAssigning day_number to {len(results)} existing riddles starting from {current_day_num}...")
    for i, row in enumerate(results):
        riddle_id = row[0]
        assigned_day = current_day_num + i
        update_stmt = update(riddle_table)\
            .where(riddle_table.c.id == riddle_id)\
            .values(day_number=assigned_day)
        conn.execute(update_stmt)
        # print(f"  Assigned day_number {assigned_day} to riddle ID {riddle_id}") # Optional verbose output

    print("Finished assigning day_numbers.")
    # --- End population code ---

    # Optional: If you want to enforce non-nullability after populating
    # with op.batch_alter_table('riddle', schema=None) as batch_op:
    #     batch_op.alter_column('day_number',
    #                           existing_type=sa.INTEGER(),
    #                           nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('riddle', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_riddle_day_number'))
        batch_op.drop_column('day_number')

    # ### end Alembic commands ###
