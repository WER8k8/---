import re

def add_column(path, class_name):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    if 'provenance_metadata' in text:
        return
        
    # Ensure JSON is imported from sqlalchemy
    if 'from sqlalchemy import ' in text and ' JSON' not in text:
        text = re.sub(r'from sqlalchemy import (.*?)\n', r'from sqlalchemy import \1, JSON\n', text, count=1)
    elif 'from sqlalchemy.types import ' in text and ' JSON' not in text:
        text = re.sub(r'from sqlalchemy.types import (.*?)\n', r'from sqlalchemy.types import \1, JSON\n', text, count=1)
    else:
        text = 'from sqlalchemy import JSON\n' + text
        
    # Add column inside class
    col_def = f"    provenance_metadata = Column(JSON, nullable=True)\n\n"
    
    # insert before __table_args__ if exists, else before the end of class
    if '    __table_args__' in text:
        text = text.replace('    __table_args__', col_def + '    __table_args__')
    else:
        # Just find created_at or updated_at and insert after
        text = re.sub(r'(    created_at = Column.*?)\n', r'\1\n' + col_def, text)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

add_column(r'backend/app/models/trade_fulfillment.py', 'ContactEvent')
add_column(r'backend/app/models/inquiry.py', 'Inquiry')
add_column(r'backend/app/models/prospect_lead.py', 'ProspectLead')
