import urllib.request

try:
    response = urllib.request.urlopen('http://127.0.0.1:8001/api/v1/health', timeout=10)
    content = response.read().decode('utf-8')
    print(f"Status: {response.status}")
    print(f"Content: {content}")
except Exception as e:
    print(f"Error: {e}")