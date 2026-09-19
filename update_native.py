path = r'backend/app/services/tradeai/native_acquisition.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '"company_name": getattr(r, "name", None),',
    '"company_name": getattr(r, "name", None),\n                    "provenance": {"source": "youding_pg", "skill_id": "prospect.scrape", "original_id": str(r.id)},'
)
text = text.replace(
    'payload={"keyword": keyword, "country": country, "hit_count": len(prospects)},',
    'payload={"keyword": keyword, "country": country, "hit_count": len(prospects), "provenance_metadata": {"skill_id": "prospect.scrape"}},'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
