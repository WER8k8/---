# DeerFlow 旁路 Mock 服务（开发环境）
# 提供 /health 和 /v1/research 接口，用于测试旁路功能

param(
    [int]$Port = 8002
)

$script = @'
import http.server
import json
import random
from urllib.parse import urlparse

class DeerFlowSidecarHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path in ('/health', '/api/health', '/v1/health'):
            self._send_json({'status': 'ok', 'service': 'deerflow-sidecar', 'version': '1.0.0'})
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path in ('/v1/research', '/api/research', '/research'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body)
                tenant_id = data.get('tenant_id', 'unknown')
                message = data.get('message', '')
            except:
                tenant_id = 'unknown'
                message = ''
            
            research_brief = {
                'id': 'research-' + str(random.randint(1000, 9999)),
                'tenant_id': tenant_id,
                'message': message,
                'executive_summary': 'Based on market analysis, focus on Southeast Asia and Middle East markets.',
                'category': 'market_research',
                'keywords': ['insulation', 'building materials', 'export'],
                'regions': ['VN', 'AE', 'SA'],
                'competitors': ['Company A', 'Company B'],
                'opportunities': [
                    {'region': 'Southeast Asia', 'reason': 'Infrastructure demand'},
                    {'region': 'Middle East', 'reason': 'Oil-driven construction'}
                ],
                'risks': [
                    {'region': 'Southeast Asia', 'risk': 'Tariff barriers'},
                    {'region': 'Middle East', 'risk': 'Political instability'}
                ],
                'created_at': '2026-07-17T12:00:00Z'
            }
            
            accio_actions = [
                {'type': 'find_customers', 'region': 'VN', 'count': 5},
                {'type': 'find_customers', 'region': 'AE', 'count': 3},
                {'type': 'send_develop_email', 'count': 10},
                {'type': 'social_post', 'platform': 'linkedin', 'count': 3}
            ]
            
            self._send_json({
                'research_brief': research_brief,
                'accio_actions': accio_actions
            })
        else:
            self._send_json({'error': 'Not found'}, 404)

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', ' + $Port + '), DeerFlowSidecarHandler)
    print('DeerFlow Sidecar Mock running on http://localhost:' + str(' + $Port + '))
    server.serve_forever()
'@

$env:PYTHONPATH = "."
python -c $script