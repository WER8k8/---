import urllib.request

print("=== Testing Vite Proxy ===")
print()

try:
    response = urllib.request.urlopen('http://localhost:5173/api/v1/health', timeout=10)
    content = response.read().decode('utf-8')
    print(f"✅ Proxy request succeeded!")
    print(f"Status: {response.status}")
    print(f"Content: {content}")
    print(f"Headers: {dict(response.headers)}")
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code} - {e.reason}")
    print(f"Content: {e.read().decode('utf-8')[:200]}")
except urllib.error.URLError as e:
    print(f"❌ URL Error: {e.reason}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=== Testing Direct Backend ===")
print()

try:
    response = urllib.request.urlopen('http://127.0.0.1:8001/api/v1/health', timeout=10)
    content = response.read().decode('utf-8')
    print(f"✅ Direct request succeeded!")
    print(f"Status: {response.status}")
    print(f"Content: {content}")
except Exception as e:
    print(f"❌ Error: {e}")