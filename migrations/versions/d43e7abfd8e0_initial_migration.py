"""Initial migration

Revision ID: d43e7abfd8e0
Revises: 
Create Date: 2025-01-08 20:36:11.537311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd43e7abfd8e0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tournament')
    op.drop_table('player')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('player',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('tournament_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['tournament_id'], ['tournament.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tournament',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
