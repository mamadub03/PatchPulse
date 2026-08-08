import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OsvError(Exception):
    error_code = "osv_unavailable"
    safe_message = "The vulnerability service could not complete the scan."


@dataclass(frozen=True)
class OsvVulnerability:
    osv_id: str
    summary: str | None
    details: str | None
    severity: str | None
    advisory_url: str | None
    fixed_version: str | None
    raw_data: dict[str, Any]


class OsvClient:
    """Synchronous OSV batch client for exact PyPI package versions."""

    def __init__(
        self,
        api_url: str = "https://api.osv.dev",
        connect_timeout: float = 5,
        read_timeout: float = 20,
        transport=None,
    ) -> None:
        self._client = httpx.Client(
            base_url=api_url,
            timeout=httpx.Timeout(read_timeout, connect=connect_timeout),
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def query_batch(self, dependencies: list[tuple[str, str]]) -> list[list[OsvVulnerability]]:
        """Return results aligned by index with the submitted dependency sequence."""
        if not dependencies:
            return []
        queries = [
            {"package": {"ecosystem": "PyPI", "name": name}, "version": version}
            for name, version in dependencies
        ]
        try:
            response = self._client.post("/v1/querybatch", json={"queries": queries})
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning("OSV batch request failed (error_type=%s)", type(exc).__name__)
            raise OsvError() from exc
        if response.is_error:
            logger.warning("OSV batch request failed (status_code=%s)", response.status_code)
            raise OsvError()
        try:
            payload = response.json()
            results = payload["results"]
            if not isinstance(results, list) or len(results) != len(queries):
                raise ValueError
            return [
                [self._normalize(vuln) for vuln in result.get("vulns", [])] for result in results
            ]
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "OSV returned an invalid batch response (error_type=%s)", type(exc).__name__
            )
            raise OsvError() from exc

    @staticmethod
    def _normalize(data: dict[str, Any]) -> OsvVulnerability:
        """Extract conservative display fields while preserving the complete source object."""
        osv_id = data.get("id")
        if not isinstance(osv_id, str) or not osv_id:
            raise ValueError
        # OSV commonly supplies CVSS vectors rather than a categorical level. PatchPulse
        # only accepts an explicit recognized label; it never invents LOW for missing data.
        severity = None
        for container in (data.get("database_specific", {}), data.get("ecosystem_specific", {})):
            candidate = container.get("severity") if isinstance(container, dict) else None
            if isinstance(candidate, str) and candidate.upper() in {
                "LOW",
                "MODERATE",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            }:
                severity = candidate.upper()
                break
        advisory = next(
            (
                r.get("url")
                for r in data.get("references", [])
                if isinstance(r, dict) and isinstance(r.get("url"), str)
            ),
            None,
        )
        # The first explicit fixed event is useful for the MVP. Full affected-range
        # interpretation remains a future hardening concern.
        fixed = None
        for affected in data.get("affected", []):
            for version_range in affected.get("ranges", []) if isinstance(affected, dict) else []:
                for event in (
                    version_range.get("events", []) if isinstance(version_range, dict) else []
                ):
                    if isinstance(event, dict) and isinstance(event.get("fixed"), str):
                        fixed = event["fixed"]
                        break
                if fixed:
                    break
            if fixed:
                break
        return OsvVulnerability(
            osv_id, data.get("summary"), data.get("details"), severity, advisory, fixed, data
        )
