"""YAML parser that validates test files and returns typed ``Test`` objects."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from .models import Test


def parse_test(
    path: str | Path,
    url_map: Optional[dict[str, str]] = None,
) -> Test:
    """Read, validate, and return a ``Test`` from a YAML file.

    Parameters
    ----------
    path:
        Path to the ``.yaml`` / ``.yml`` test file.
    url_map:
        Optional mapping of target names → URLs for resolving simple-name
        targets.  When ``None``, only inline targets (full objects with a
        ``url`` field) are accepted.

    Returns
    -------
    Test
        A fully-validated test object.

    Raises
    ------
    FileNotFoundError
        If the YAML file does not exist.
    yaml.YAMLError
        If the file is not valid YAML.
    pydantic.ValidationError
        If the test structure does not match the schema.
    ValueError
        If a target name cannot be resolved to a URL.
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Test file not found: {path}")

    raw: dict
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a YAML mapping (dict) at top level, got {type(raw).__name__}")

    # Normalise "test_id" → "test-id" so callers can use either key.
    if "test_id" in raw and "test-id" not in raw:
        raw["test-id"] = raw.pop("test_id")

    if "test-id" not in raw:
        raise ValueError("Missing required field 'test-id' (or 'test_id') in test file")

    test = Test.model_validate(raw)

    # Resolve targets (will raise ValueError if names can't be resolved).
    if url_map is None:
        url_map = {}
    test.targets.resolve(url_map)

    return test


def validate_test_yaml(
    path: str | Path,
    url_map: Optional[dict[str, str]] = None,
) -> str:
    """Validate a test YAML file and return a human-readable status message.

    Parameters
    ----------
    path:
        Path to the YAML test file.
    url_map:
        Optional URL mapping for target name resolution.

    Returns
    -------
    str
        ``"✓ <test-id>: <name> (valid, N steps)"`` on success, or an error
        description on failure.
    """
    try:
        test = parse_test(path, url_map=url_map)
        return (
            f"✓ {test.test_id}: {test.name} "
            f"(valid, {len(test.steps)} steps, "
            f"primary={test.targets.primary!r}, "
            f"{len(test.targets.references)} reference(s))"
        )
    except FileNotFoundError as exc:
        return f"✗ {exc}"
    except yaml.YAMLError as exc:
        return f"✗ YAML error in {path}: {exc}"
    except ValidationError as exc:
        errors = "; ".join(e["msg"] for e in exc.errors())
        return f"✗ Validation error in {path}: {errors}"
    except ValueError as exc:
        return f"✗ {exc}"
