import http.server
import json
import random
import sys
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

        if path in ('/health', '/api/health', '/v1/health', '/api/v1/health'):
            self._send_json({
                'status': 'ok',
                'service': 'deerflow-sidecar',
                'version': '2.0.0',
                'is_v2': True,
                'services': {
                    'gateway': 'running',
                    'langgraph': 'running',
                    'sandbox': 'ready',
                    'memory': 'active'
                }
            })
        elif path.startswith('/threads/'):
            parts = path.split('/')
            if len(parts) >= 4:
                thread_id = parts[2]
                run_id = parts[4] if len(parts) > 4 else None
                if run_id:
                    self._send_json({
                        'thread_id': thread_id,
                        'run_id': run_id,
                        'status': 'completed',
                        'output': {
                            'summary': '基于市场分析，建议重点关注东南亚和中东市场。',
                            'research_brief': {
                                'executive_summary': '基于市场分析，建议重点关注东南亚和中东市场。',
                                'category': 'market_research'
                            }
                        }
                    })
                else:
                    self._send_json({
                        'thread_id': thread_id,
                        'status': 'active',
                        'messages': []
                    })
            else:
                self._send_json({'error': 'Not found'}, 404)
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body)
        except:
            data = {}

        tenant_id = data.get('tenant_id', 'unknown')
        message = data.get('message', '')
        skill = data.get('skill', 'deep-search')
        mode = data.get('mode', 'ultra')

        if path in ('/v1/research', '/api/research', '/research'):
            research_brief = {
                'id': 'research-' + str(random.randint(1000, 9999)),
                'tenant_id': tenant_id,
                'message': message,
                'executive_summary': '基于市场分析，建议重点关注东南亚和中东市场。',
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
                'created_at': '2026-07-17T12:00:00Z',
                'version': '2.0'
            }

            accio_actions = [
                {'type': 'find_customers', 'region': 'VN', 'count': 5},
                {'type': 'find_customers', 'region': 'AE', 'count': 3},
                {'type': 'send_develop_email', 'count': 10},
                {'type': 'social_post', 'platform': 'linkedin', 'count': 3}
            ]

            self._send_json({
                'research_brief': research_brief,
                'accio_actions': accio_actions,
                'mode': 'deerflow_sidecar_v2',
                'skill': skill,
                'execution_mode': mode
            })

        elif path in ('/v1/chat', '/api/v1/chat', '/chat/completions'):
            self._send_json({
                'content': '基于市场分析，建议重点关注东南亚和中东市场。',
                'research_brief': {
                    'executive_summary': '基于市场分析，建议重点关注东南亚和中东市场。',
                    'category': 'market_research',
                    'version': '2.0'
                },
                'accio_actions': [],
                'mode': 'deerflow_sidecar_v2',
                'skill': skill
            })

        elif path == '/threads':
            thread_id = 'thread-' + str(random.randint(100000, 999999))
            self._send_json({
                'thread_id': thread_id,
                'status': 'created',
                'configurable': {'tenant_id': tenant_id}
            })

        elif path.startswith('/threads/') and '/runs' in path:
            parts = path.split('/')
            thread_id = parts[2] if len(parts) > 2 else 'unknown'
            run_id = 'run-' + str(random.randint(100000, 999999))
            self._send_json({
                'thread_id': thread_id,
                'run_id': run_id,
                'status': 'queued',
                'input': {'message': message}
            })

        else:
            self._send_json({'error': 'Not found'}, 404)

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8002
    server = http.server.HTTPServer(('localhost', port), DeerFlowSidecarHandler)
    print(f'DeerFlow 2.0 Sidecar Mock running on http://localhost:{port}')
    server.serve_forever()