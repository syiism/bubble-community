import httpx

client = httpx.AsyncClient(follow_redirects=True, timeout=30.0)

avatar_client = httpx.AsyncClient(follow_redirects=False, timeout=10.0)