import re
import os

path_inq = r'frontend/admin/src/views/client/queues/inquiries.vue'
with open(path_inq, 'r', encoding='utf-8') as f:
    inq_text = f.read()
inq_text = re.sub(r'\s*<a-button[^>]*click="router\.push\(\'/client/annex/goodjob/customers\'\)"[^>]*>.*?</a-button>', '', inq_text, flags=re.DOTALL)
with open(path_inq, 'w', encoding='utf-8') as f:
    f.write(inq_text)

path_ful = r'frontend/admin/src/views/client/queues/fulfillment.vue'
with open(path_ful, 'r', encoding='utf-8') as f:
    ful_text = f.read()
ful_text = ful_text.replace("router.push('/client/annex/goodjob');", "router.push('/client/tasks');")
with open(path_ful, 'w', encoding='utf-8') as f:
    f.write(ful_text)

path_layout = r'frontend/admin/src/layout/ClientShellLayout.vue'
with open(path_layout, 'r', encoding='utf-8') as f:
    layout_text = f.read()
layout_text = re.sub(r'\s*\{\s*label:\s*\'履约工作台\'.*?\},', '', layout_text)
layout_text = re.sub(r'\s*\{\s*label:\s*\'外贸单证\'.*?\},', '', layout_text)
layout_text = re.sub(r'\s*\{\s*label:\s*\'客户档案\'.*?\},', '', layout_text)
with open(path_layout, 'w', encoding='utf-8') as f:
    f.write(layout_text)
