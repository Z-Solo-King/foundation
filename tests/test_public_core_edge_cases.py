from types import SimpleNamespace
import pytest
from backend.persistence.cloudflare import CloudflarePersistence
from foundation_core.product_mapping import _image_provenance

class _ArtifactResponse:
    def __init__(self,payload:bytes): self.body=SimpleNamespace(arrayBuffer=lambda:_array_buffer(payload))
async def _array_buffer(payload:bytes)->bytes: return payload
class _ArtifactStore:
    def __init__(self): self.value=_ArtifactResponse(b"abc"); self.opaque=object(); self.deleted=[]
    async def get(self,key:str): return self.value if key=="response" else self.opaque if key=="opaque" else None
    async def put(self,key,content,*,content_type): return None
    async def delete(self,key): self.deleted.append(key)

@pytest.mark.asyncio
async def test_cloudflare_persistence_normalizes_runtime_artifact_response_shapes():
    store=_ArtifactStore(); persistence=CloudflarePersistence(SimpleNamespace(ARTIFACTS=store,DB=None))
    assert await persistence.get_artifact("response")==b"abc"
    assert await persistence.get_artifact("opaque") is store.opaque
    await persistence.delete_artifact("opaque"); assert store.deleted==["opaque"]

def test_product_image_provenance_covers_image_collection_selection():
    provenance=_image_provenance({"source":{"image":[],"images":["https://example.test/a.png"],"source_url":"https://example.test"}},("https://example.test/a.png",))
    assert provenance[0]["source_field"]=="images"
    assert _image_provenance({"source":{"image":[],"images":[]}},())==()
