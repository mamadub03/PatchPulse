import httpx
import pytest

from app.clients.osv import OsvClient, OsvError


def test_batch_normalizes_findings_without_inventing_severity() -> None:
    payload = {
        "results": [
            {
                "vulns": [
                    {
                        "id": "OSV-1",
                        "summary": "Issue",
                        "references": [{"url": "https://a"}],
                        "affected": [{"ranges": [{"events": [{"fixed": "2.0"}]}]}],
                    }
                ]
            },
            {"vulns": []},
        ]
    }
    client = OsvClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    )
    results = client.query_batch([("a", "1"), ("b", "1")])
    assert results[0][0].severity is None
    assert results[0][0].fixed_version == "2.0"
    assert results[1] == []


@pytest.mark.parametrize("response", [httpx.Response(500), httpx.Response(200, json={"bad": []})])
def test_osv_failure_is_explicit(response: httpx.Response) -> None:
    client = OsvClient(transport=httpx.MockTransport(lambda request: response))
    with pytest.raises(OsvError):
        client.query_batch([("a", "1")])
