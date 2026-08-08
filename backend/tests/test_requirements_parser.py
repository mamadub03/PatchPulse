import pytest

from app.services.requirements import normalize_package_name, parse_requirements


def test_exact_pins_comments_whitespace_and_normalization() -> None:
    parsed = parse_requirements(b"\n# comment\n Django == 4.2.2  # safe\nMy_Package==1.0\n")
    assert [(item.package_name, item.version, item.is_supported) for item in parsed] == [
        ("django", "4.2.2", True),
        ("my-package", "1.0", True),
    ]
    assert normalize_package_name("Friendly_Bard...Test") == "friendly-bard-test"


@pytest.mark.parametrize(
    "line",
    [
        "Django>=4.2",
        "requests~=2.31",
        "Flask",
        "package!=1.0",
        "-r other.txt",
        "git+https://example.test/a.git",
        "name[extra]==1; python_version>'3'",
    ],
)
def test_unsupported_forms_are_preserved(line: str) -> None:
    item = parse_requirements(line.encode())[0]
    assert item.original == line
    assert item.is_supported is False
    assert item.version is None


def test_malformed_and_duplicates_do_not_crash() -> None:
    parsed = parse_requirements(b"???\nrequests==1\nrequests==1\n")
    assert parsed[0].unsupported_reason == "malformed_requirement"
    assert len(parsed) == 3
