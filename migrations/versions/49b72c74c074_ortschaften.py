"""ortschaften

Revision ID: 49b72c74c074
Revises: 615daca391cd
Create Date: 2020-06-02 00:02:01.181080

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49b72c74c074'
down_revision = '615daca391cd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ortschaften',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ort', sa.String(length=200), nullable=True),
    sa.Column('laenge', sa.String(length=200), nullable=True),
    sa.Column('breite', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ortschaften')
    # ### end Alembic commands ###
