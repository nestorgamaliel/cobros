"""renombrar_comisiones_a_credito_comisiones

Revision ID: 6998ebe3ca93
Revises: 1deaf26c981a
Create Date: 2026-02-23 23:18:49.109846

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6998ebe3ca93'
down_revision: Union[str, Sequence[str], None] = '1deaf26c981a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Renombrar la tabla físicamente
    op.rename_table('comisiones_creditos', 'credito_comision')
    
    # 2. Renombrar la columna de la llave primaria para que coincida con el nuevo nombre
    op.alter_column('credito_comision', 'comision_credito_id', new_column_name='credito_comision_id')

    # NOTA: Eliminamos el alter_column de 'cancelado' porque ya lo 
    # gestionamos con el casting manual en la migración anterior.

def downgrade() -> None:
    # Revertir los nombres
    op.alter_column('credito_comision', 'credito_comision_id', new_column_name='comision_credito_id')
    op.rename_table('credito_comision', 'comisiones_creditos')
