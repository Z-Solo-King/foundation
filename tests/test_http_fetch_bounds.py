import asyncio
import pytest

from backend.sources.http import FETCH_TIMEOUT_SECONDS, MAX_BYTES, fetch_public_url

class Headers(dict): pass
class Response:
    status = 200
    headers = Headers({'content-type': 'text/plain'})
    async def arrayBuffer(self): return b'ok'

def test_fetch_rejects_advertised_oversize_before_read():
    class Big(Response):
        headers = Headers({'content-length': str(MAX_BYTES + 1)})
        async def arrayBuffer(self): raise AssertionError('body should not be read')
    async def fetcher(url, options): return Big()
    async def resolve(host, record_type): return ['8.8.8.8']
    with pytest.raises(RuntimeError, match='size budget'):
        asyncio.run(fetch_public_url('https://example.com', fetcher=fetcher, dns_resolver=resolve))

def test_fetch_times_out_slow_transport():
    class Slow(Response):
        async def arrayBuffer(self):
            await asyncio.sleep(FETCH_TIMEOUT_SECONDS + 0.05)
            return b'late'
    async def fetcher(url, options): return Slow()
    async def resolve(host, record_type): return ['8.8.8.8']
    with pytest.raises(RuntimeError, match='timed out'):
        asyncio.run(fetch_public_url('https://example.com', fetcher=fetcher, dns_resolver=resolve))
