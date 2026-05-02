"""Convert specifications field to JSON type

Revision ID: 005_specifications_json
Revises: 004_add_case_product_relation
Create Date: 2026-05-01 12:00:00

"""
from alembic import op
import sqlalchemy as sa
import json

# revision identifiers, used by Alembic.
revision = '005_specifications_json'
down_revision = '004_add_case_product_relation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # For SQLite, we'll handle the data conversion in Python
    # The column type remains TEXT, but we ensure data is valid JSON
    conn = op.get_bind()
    
    # Get all products with specifications
    products = conn.execute(sa.text('SELECT id, specifications FROM products WHERE specifications IS NOT NULL')).fetchall()
    
    for product_id, specs in products:
        # Try to parse as JSON
        try:
            if specs:
                # Already valid JSON
                parsed = json.loads(specs)
                if isinstance(parsed, dict):
                    continue  # Already valid dict
                # If it's a string, wrap it as {"value": "string"}
                specs = json.dumps({"value": specs})
            else:
                specs = json.dumps({})
        except json.JSONDecodeError:
            # Not valid JSON, wrap as {"value": "original string"}
            specs = json.dumps({"value": specs})
        
        # Update the record
        conn.execute(
            sa.text('UPDATE products SET specifications = :specs WHERE id = :id'),
            {'specs': specs, 'id': product_id}
        )


def downgrade() -> None:
    # No need to change column type, just leave as is
    pass
