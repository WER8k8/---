path = r'backend/app/services/hermes/planner_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('executor="lead"', 'executor="trade_ai_agent"')
text = text.replace('capability="lead.search"', 'capability="prospect.scrape"')
text = text.replace('capability="lead.score"', 'capability="prospect.enrich"')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
