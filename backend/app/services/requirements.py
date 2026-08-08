import re
from dataclasses import dataclass

NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
EXACT = re.compile(rf"^({NAME})\s*==\s*([^\s;]+)$")
NAME_ONLY = re.compile(rf"^({NAME})(.*)$")


@dataclass(frozen=True)
class ParsedRequirement:
    original: str
    package_name: str | None
    version: str | None
    is_supported: bool
    unsupported_reason: str | None


def normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements(content: bytes, max_dependencies: int = 2_000) -> list[ParsedRequirement]:
    text = content.decode("utf-8", errors="replace")
    parsed: list[ParsedRequirement] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"\s+#.*$", "", line).strip()
        exact = EXACT.fullmatch(line)
        if exact:
            parsed.append(
                ParsedRequirement(
                    raw.strip(), normalize_package_name(exact[1]), exact[2], True, None
                )
            )
        else:
            named = NAME_ONLY.fullmatch(line)
            name = normalize_package_name(named[1]) if named else None
            reason = "unsupported_requirement" if named else "malformed_requirement"
            parsed.append(ParsedRequirement(raw.strip(), name, None, False, reason))
        if len(parsed) > max_dependencies:
            raise ValueError("requirements.txt contains too many dependencies")
    return parsed
