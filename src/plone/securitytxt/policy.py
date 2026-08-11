"""Authoritative Security Policy application module.

All management adapters delegate to this module.  The persistent record is kept
small and deliberately contains the exact bytes served by the public endpoint.
"""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit

from persistent.mapping import PersistentMapping


ANNOTATION_KEY = "plone.securitytxt.security-policy"
MANAGE_PERMISSION = "plone.securitytxt.ManageSecurityPolicy"
SERIALIZER_VERSION = 1
MAX_UNSIGNED_BYTES = 32 * 1024
MAX_SIGNED_BYTES = 64 * 1024
MAX_LINE_CHARACTERS = 2048
MAX_LINES = 1000
WARNING_WINDOW_SECONDS = 30 * 24 * 60 * 60

FIELD_ORDER = (
    ("contact", "Contact"),
    ("expires", "Expires"),
    ("encryption", "Encryption"),
    ("acknowledgments", "Acknowledgments"),
    ("preferred_languages", "Preferred-Languages"),
    ("canonical", "Canonical"),
    ("policy", "Policy"),
    ("hiring", "Hiring"),
)
URI_FIELDS = {
    "contact",
    "encryption",
    "acknowledgments",
    "canonical",
    "policy",
    "hiring",
}
FIRST_CLASS_NAMES = {label.casefold() for _, label in FIELD_ORDER}
FIELD_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")
LANGUAGE_RE = re.compile(
    r"^(?:"
    r"(?:[A-Z]{2,3}(?:-[A-Z]{3}){0,3}|[A-Z]{4}|[A-Z]{5,8})"
    r"(?:-[A-Z]{4})?(?:-(?:[A-Z]{2}|[0-9]{3}))?"
    r"(?:-(?:[A-Z0-9]{5,8}|[0-9][A-Z0-9]{3}))*"
    r"(?:-[0-9A-WY-Z](?:-[A-Z0-9]{2,8})+)*"
    r"(?:-X(?:-[A-Z0-9]{1,8})+)?"
    r"|X(?:-[A-Z0-9]{1,8})+"
    r"|I-(?:AMI|Bnn|Default|Enochian|Hak|Klingon|Lux|Mingo|Navajo|Pwn|Tao|Tay|Tsu)"
    r"|SGN-(?:BE-FR|BE-NL|CH-DE)"
    r"|ART-LOJBAN|CEL-GAULISH|NO-BOK|NO-NYN|ZH-(?:GUOYU|HAKKA|MIN|MIN-NAN|XIANG)"
    r")$",
    re.IGNORECASE,
)


class PolicyError(Exception):
    """Base class for stable management errors."""


class PolicyPermissionError(PolicyError):
    """The current principal cannot manage the Security Policy."""


class PolicyRevisionError(PolicyError):
    """The caller supplied a stale revision."""


class PolicyCommandError(PolicyError):
    """A command failed validation without changing persistent state."""

    def __init__(self, message: str, diagnostics: dict[str, Any] | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


@dataclass(frozen=True)
class PublicationResult:
    """Sanitized result consumed by the anonymous HTTP adapter."""

    status: str
    body: bytes = b""
    etag: str | None = None
    seconds_to_expiry: int = 0


def _default_values() -> dict[str, Any]:
    return {
        "contact": [],
        "expires": None,
        "encryption": [],
        "acknowledgments": [],
        "preferred_languages": [],
        "canonical": [],
        "policy": [],
        "hiring": [],
        "extensions": [],
        "publication_mode": "unsigned",
        "signing_profile": None,
    }


def new_record() -> PersistentMapping:
    """Create the one versioned site record installed for a Plone site."""
    return PersistentMapping({
        "format_version": 1,
        "revision": 1,
        "values": PersistentMapping(_default_values()),
        "publication_enabled": False,
        "artifact": b"",
        "artifact_binding": PersistentMapping(),
        "etag": None,
        "signing_status": PersistentMapping({"capability": "unavailable", "last_error": None}),
    })


def _diagnostic(code: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "field": field, "message": message}


def _has_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _absolute_uri(value: str) -> bool:
    if (
        not value
        or _has_control_characters(value)
        or any(character.isspace() for character in value)
        or re.search(r"%(?![0-9A-Fa-f]{2})", value)
        or any(character in '<>"{}|\\^`' for character in value)
    ):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    if not parsed.scheme or not SCHEME_RE.fullmatch(parsed.scheme):
        return False
    if parsed.scheme.casefold() in {"http", "https"}:
        try:
            _port = parsed.port
        except ValueError:
            return False
        return parsed.scheme.casefold() == "https" and bool(parsed.netloc)
    return bool(parsed.path)


def _parse_expiry(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _format_expiry(value: datetime) -> str:
    value = value.astimezone(timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def _normalize_list(value: Any) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        return None
    return [item if isinstance(item, str) else "" for item in value]


def validate_policy(  # noqa: C901 - one pass preserves ordered cross-field diagnostics
    candidate: dict[str, Any] | None,
    *,
    now: datetime,
) -> dict[str, Any]:
    """Normalize candidate values and return errors, blockers, and warnings."""
    raw = dict(candidate or {})
    values = _default_values()
    errors: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for field, _label in FIELD_ORDER:
        if field == "expires":
            continue
        normalized = _normalize_list(raw.get(field, []))
        if normalized is None:
            errors.append(_diagnostic(f"{field}.type", field, "Expected an ordered list."))
            normalized = []
        values[field] = normalized

    expiry_raw = raw.get("expires")
    expiry = _parse_expiry(expiry_raw)
    if expiry_raw not in (None, "") and expiry is None:
        errors.append(
            _diagnostic("expires.invalid", "expires", "Use an ISO 8601 instant with a timezone.")
        )
    values["expires"] = _format_expiry(expiry) if expiry else None

    for field in URI_FIELDS:
        for index, value in enumerate(values[field]):
            if not _absolute_uri(value):
                errors.append(
                    _diagnostic(
                        f"{field}.uri",
                        field,
                        f"Value {index + 1} must be an absolute URI; web URIs must use HTTPS.",
                    )
                )

    for value in values["canonical"]:
        try:
            parsed = urlsplit(value)
        except ValueError:
            continue
        if (
            parsed.scheme.casefold() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or not parsed.path.endswith("/.well-known/security.txt")
        ):
            errors.append(
                _diagnostic(
                    "canonical.invalid",
                    "canonical",
                    "Canonical URLs must be credential-free HTTPS well-known URLs "
                    "without query or fragment.",
                )
            )

    seen_languages: set[str] = set()
    for tag in values["preferred_languages"]:
        folded = tag.casefold()
        if not LANGUAGE_RE.fullmatch(tag):
            errors.append(
                _diagnostic(
                    "preferred_languages.invalid",
                    "preferred_languages",
                    f"{tag!r} is not a supported BCP 47 language tag.",
                )
            )
        elif folded in seen_languages:
            errors.append(
                _diagnostic(
                    "preferred_languages.duplicate",
                    "preferred_languages",
                    f"Duplicate language tag: {tag}.",
                )
            )
        seen_languages.add(folded)

    extensions = raw.get("extensions", []) or []
    if not isinstance(extensions, (list, tuple)):
        errors.append(
            _diagnostic("extensions.type", "extensions", "Expected ordered name/value rows.")
        )
        extensions = []
    normalized_extensions: list[dict[str, str]] = []
    seen_extensions: set[tuple[str, str]] = set()
    counts: dict[str, int] = {}
    for row in extensions:
        if not isinstance(row, dict):
            errors.append(
                _diagnostic(
                    "extension.type", "extensions", "Each extension must have a name and value."
                )
            )
            continue
        name = row.get("name", "")
        value = row.get("value", "")
        if not isinstance(name, str) or not FIELD_NAME_RE.fullmatch(name):
            errors.append(
                _diagnostic("extension.name", "extensions", "Extension field names are invalid.")
            )
            continue
        folded_name = name.casefold()
        if folded_name in FIRST_CLASS_NAMES:
            errors.append(
                _diagnostic("extension.collision", "extensions", f"{name} is a first-class field.")
            )
        if not isinstance(value, str) or not value or _has_control_characters(value):
            errors.append(
                _diagnostic(
                    "extension.value", "extensions", f"{name} needs a nonempty single-line value."
                )
            )
            value = value if isinstance(value, str) else ""
        key = (folded_name, value)
        if key in seen_extensions:
            errors.append(
                _diagnostic("extension.duplicate", "extensions", f"Duplicate {name} value.")
            )
        seen_extensions.add(key)
        counts[folded_name] = counts.get(folded_name, 0) + 1
        if folded_name == "csaf" and (
            not _absolute_uri(value) or urlsplit(value).scheme.casefold() != "https"
        ):
            errors.append(
                _diagnostic("extension.csaf-uri", "extensions", "CSAF must contain an HTTPS URI.")
            )
        elif folded_name == "bug-bounty" and value not in {"True", "False"}:
            errors.append(
                _diagnostic(
                    "extension.bug-bounty", "extensions", "Bug-Bounty must be True or False."
                )
            )
        elif folded_name not in {"csaf", "bug-bounty"}:
            warnings.append(
                _diagnostic(
                    "extension.unknown",
                    "extensions",
                    f"{name} is not in this release's IANA snapshot.",
                )
            )
        normalized_extensions.append({"name": name, "value": value})
    if counts.get("bug-bounty", 0) > 1:
        errors.append(
            _diagnostic("extension.singleton", "extensions", "Bug-Bounty may occur at most once.")
        )
    values["extensions"] = normalized_extensions

    mode = raw.get("publication_mode", "unsigned") or "unsigned"
    if mode not in {"unsigned", "signed"}:
        errors.append(
            _diagnostic(
                "publication_mode.invalid", "publication_mode", "Use unsigned or signed mode."
            )
        )
        mode = "unsigned"
    values["publication_mode"] = mode
    profile = raw.get("signing_profile") or None
    if profile is not None and (not isinstance(profile, str) or not profile.strip()):
        errors.append(
            _diagnostic(
                "signing_profile.invalid", "signing_profile", "Select a valid Signing Profile."
            )
        )
        profile = None
    values["signing_profile"] = profile

    if not values["contact"]:
        blockers.append(
            _diagnostic("contact.required", "contact", "At least one Contact is required.")
        )
    if expiry is None:
        blockers.append(_diagnostic("expires.required", "expires", "Expires is required."))
    elif expiry <= now:
        blockers.append(_diagnostic("expires.future", "expires", "Expires must be in the future."))
    else:
        seconds = (expiry - now).total_seconds()
        if seconds <= WARNING_WINDOW_SECONDS:
            warnings.append(
                _diagnostic("expires.soon", "expires", "The policy expires within 30 days.")
            )
        if seconds > 366 * 24 * 60 * 60:
            warnings.append(
                _diagnostic(
                    "expires.over-year", "expires", "The expiry is more than one year away."
                )
            )
    if not values["canonical"]:
        warnings.append(
            _diagnostic("canonical.recommended", "canonical", "Canonical is recommended.")
        )
    if not values["policy"]:
        warnings.append(_diagnostic("policy.recommended", "policy", "Policy is recommended."))
    if (
        any(value.casefold().startswith("mailto:") for value in values["contact"])
        and not values["encryption"]
    ):
        warnings.append(
            _diagnostic(
                "encryption.recommended",
                "encryption",
                "Encryption is recommended for email contacts.",
            )
        )
    if mode == "signed":
        if not values["canonical"]:
            blockers.append(
                _diagnostic(
                    "canonical.signing-required",
                    "canonical",
                    "Signed publication requires Canonical.",
                )
            )
        if not profile:
            blockers.append(
                _diagnostic(
                    "signing_profile.required",
                    "signing_profile",
                    "Signed publication requires a Signing Profile.",
                )
            )

    preview = b""
    if not errors:
        preview = render_security_txt(values)
        lines = preview.decode("utf-8").splitlines()
        if len(preview) > MAX_UNSIGNED_BYTES:
            blockers.append(
                _diagnostic(
                    "representation.size", "", "The unsigned representation exceeds 32 KiB."
                )
            )
        if len(lines) > MAX_LINES:
            blockers.append(
                _diagnostic("representation.lines", "", "The representation exceeds 1,000 lines.")
            )
        if any(len(line) > MAX_LINE_CHARACTERS for line in lines):
            blockers.append(
                _diagnostic(
                    "representation.line-length", "", "A generated line exceeds 2,048 characters."
                )
            )

    return {
        "values": values,
        "errors": errors,
        "blockers": blockers,
        "warnings": warnings,
        "preview": preview.decode("utf-8"),
    }


def render_security_txt(values: dict[str, Any]) -> bytes:
    """Render canonical RFC 9116 bytes; signing is intentionally elsewhere."""
    lines: list[str] = []
    for field, label in FIELD_ORDER:
        field_value = values.get(field)
        if not field_value:
            continue
        if field == "expires":
            lines.append(f"{label}: {field_value}")
        elif field == "preferred_languages":
            lines.append(f"{label}: {', '.join(field_value)}")
        else:
            lines.extend(f"{label}: {value}" for value in field_value)
    lines.extend(f"{row['name']}: {row['value']}" for row in values.get("extensions", []))
    if not lines:
        return b""
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def _normalized_https_url(value: str) -> tuple[str, str, int | None, str] | None:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        if (
            parsed.scheme.casefold() != "https"
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            return None
        hostname = hostname.encode("idna").decode("ascii").casefold()
        port = parsed.port
    except (UnicodeError, ValueError):
        return None
    if port == 443:
        port = None
    return ("https", hostname, port, parsed.path)


def canonical_url_matches(request_url: str, canonical_urls: list[str]) -> bool:
    """Apply the intentionally narrow Canonical normalization contract."""
    if not canonical_urls:
        return True
    request_key = _normalized_https_url(request_url)
    return request_key is not None and request_key in {
        key for value in canonical_urls if (key := _normalized_https_url(value))
    }


class SecurityPolicyApplication:
    """Deep interface shared by Classic UI, REST, warning, and HTTP adapters."""

    def __init__(
        self,
        site: Any | None = None,
        *,
        record: PersistentMapping | None = None,
        clock=None,
        signer=None,
        check_permission: bool = True,
    ):
        if record is None:
            if site is None:
                raise ValueError("site or record is required")
            from zope.annotation.interfaces import IAnnotations

            annotations = IAnnotations(site)
            record = annotations.get(ANNOTATION_KEY)
            if record is None:
                raise LookupError("Security Policy record is not installed")
        self.site = site
        self.record = record
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.signer = signer
        self.check_permission = check_permission

    def _authorize(self) -> None:
        if not self.check_permission:
            return
        from AccessControl import getSecurityManager

        if self.site is None or not getSecurityManager().checkPermission(
            MANAGE_PERMISSION, self.site
        ):
            raise PolicyPermissionError("Security Policy management is not permitted")

    def evaluate(self, candidate: dict[str, Any] | None, *, preview: bool = True) -> dict[str, Any]:
        self._authorize()
        result = validate_policy(candidate, now=self.clock())
        if not preview:
            result["preview"] = ""
        return result

    def inspect(self) -> dict[str, Any]:
        self._authorize()
        return self._inspect_authorized()

    def _inspect_authorized(self) -> dict[str, Any]:
        values = deepcopy(dict(self.record["values"]))
        now = self.clock()
        expiry = _parse_expiry(values.get("expires"))
        enabled = bool(self.record["publication_enabled"])
        lifecycle = "draft"
        endpoint_status = 404
        if enabled:
            if expiry is None or expiry <= now:
                lifecycle = "publication-blocked"
            elif not self._artifact_matches(values):
                lifecycle = "publication-blocked"
                endpoint_status = 503
            else:
                lifecycle = "published"
                endpoint_status = 200
        diagnostics = validate_policy(values, now=now)
        expiry_seconds = int((expiry - now).total_seconds()) if expiry else None
        warning = (
            enabled and expiry_seconds is not None and expiry_seconds <= WARNING_WINDOW_SECONDS
        )
        signing = deepcopy(dict(self.record["signing_status"]))
        binding = self.record.get("artifact_binding", {})
        signing.update(
            profile_id=values.get("signing_profile"),
            profile_revision=binding.get("profile_revision"),
            primary_fingerprint=binding.get("primary_fingerprint"),
            signing_fingerprint=binding.get("signing_fingerprint"),
        )
        return {
            "values": values,
            "revision": str(self.record["revision"]),
            "publication_enabled": enabled,
            "lifecycle": lifecycle,
            "endpoint_status": endpoint_status,
            "errors": diagnostics["errors"],
            "blockers": diagnostics["blockers"],
            "warnings": diagnostics["warnings"],
            "expiry_seconds": expiry_seconds,
            "show_expiry_warning": warning,
            "signing": signing,
            "actions": ["save", "validate", "preview", "publish", "disable", "test-signing"],
        }

    def execute(
        self,
        command: str,
        candidate: dict[str, Any] | None = None,
        *,
        expected_revision: str | None,
    ) -> dict[str, Any]:
        self._authorize()
        if expected_revision is None or str(expected_revision).strip('"') != str(
            self.record["revision"]
        ):
            raise PolicyRevisionError("The Security Policy revision is stale")

        if command == "test-signing":
            return self._execute_signing_test(candidate)

        if command == "disable":
            self.record["publication_enabled"] = False
            self.record["revision"] += 1
            return self._inspect_authorized()

        if command not in {"save", "publish"}:
            raise PolicyCommandError(f"Unknown command: {command}")

        if candidate is None:
            values = deepcopy(dict(self.record["values"]))
        else:
            evaluated = validate_policy(candidate, now=self.clock())
            if evaluated["errors"]:
                raise PolicyCommandError("The Security Policy contains invalid values", evaluated)
            values = evaluated["values"]

        evaluated = validate_policy(values, now=self.clock())
        self._ensure_signing_selection(values)
        enabling = command == "publish"
        remains_enabled = bool(self.record["publication_enabled"]) or enabling
        if remains_enabled and (evaluated["errors"] or evaluated["blockers"]):
            raise PolicyCommandError("The Security Policy cannot be published", evaluated)

        artifact = self.record["artifact"]
        binding = deepcopy(dict(self.record["artifact_binding"]))
        etag = self.record["etag"]
        if remains_enabled:
            unsigned = render_security_txt(values)
            artifact, binding = self._generate_artifact(values, unsigned)
            etag = f'"{sha256(artifact).hexdigest()}"'

        # Replace complete values/artifact only after every fallible operation.
        self.record["values"] = PersistentMapping(deepcopy(values))
        self.record["publication_enabled"] = remains_enabled
        self.record["artifact"] = artifact
        self.record["artifact_binding"] = PersistentMapping(binding)
        self.record["etag"] = etag
        self.record["revision"] += 1
        return self._inspect_authorized()

    def _ensure_signing_selection(self, values):
        if values["publication_mode"] != "signed":
            return
        from importlib.util import find_spec

        from plone.securitytxt.signing import signing_profile_metadata

        profile = signing_profile_metadata(values.get("signing_profile"))
        if (
            profile is None
            or not profile["enabled"]
            or (self.signer is None and find_spec("gnupg") is None)
        ):
            diagnostic = _diagnostic(
                "signing_profile.unavailable",
                "signing_profile",
                "Signed Publication Mode requires an available Signing Profile.",
            )
            raise PolicyCommandError(
                "The selected Signing Profile is unavailable",
                {"errors": [diagnostic], "blockers": [], "warnings": []},
            )

    def _execute_signing_test(self, candidate):
        signer = self._get_signer()
        if signer is None:
            raise PolicyCommandError("Signing support is unavailable")
        try:
            status = signer.test(candidate or dict(self.record["values"]))
        except Exception as exc:
            raise PolicyCommandError("Signing capability test failed") from exc
        self.record["signing_status"] = PersistentMapping(status)
        self.record["revision"] += 1
        return self._inspect_authorized()

    def _generate_artifact(
        self, values: dict[str, Any], unsigned: bytes
    ) -> tuple[bytes, dict[str, Any]]:
        content_hash = sha256(unsigned).hexdigest()
        mode = values["publication_mode"]
        binding: dict[str, Any] = {
            "unsigned_hash": content_hash,
            "mode": mode,
            "serializer_version": SERIALIZER_VERSION,
        }
        if mode == "unsigned":
            artifact = unsigned
        else:
            signer = self._get_signer()
            if signer is None:
                raise PolicyCommandError("Signing support is unavailable")
            try:
                artifact, signer_binding = signer.sign_and_verify(
                    unsigned,
                    values["signing_profile"],
                    expires=values["expires"],
                )
            except Exception as exc:
                raise PolicyCommandError("Signing failed") from exc
            binding.update(signer_binding)
            binding["profile_id"] = values["signing_profile"]
            if len(artifact) > MAX_SIGNED_BYTES:
                raise PolicyCommandError("The signed artifact exceeds 64 KiB")
        binding["artifact_hash"] = sha256(artifact).hexdigest()
        return artifact, binding

    def _get_signer(self):
        if self.signer is None:
            from plone.securitytxt.signing import configured_signer

            self.signer = configured_signer()
        return self.signer

    def _artifact_matches(self, values: dict[str, Any]) -> bool:
        artifact = self.record.get("artifact", b"")
        binding = self.record.get("artifact_binding", {})
        if not artifact or not binding:
            return False
        unsigned = render_security_txt(values)
        if binding.get("unsigned_hash") != sha256(unsigned).hexdigest():
            return False
        if binding.get("mode") != values.get("publication_mode"):
            return False
        if binding.get("serializer_version") != SERIALIZER_VERSION:
            return False
        if binding.get("artifact_hash") != sha256(artifact).hexdigest():
            return False
        if values.get("publication_mode") == "signed":
            profile_id = values.get("signing_profile")
            if binding.get("profile_id") != profile_id:
                return False
            from plone.securitytxt.signing import signing_profile_metadata

            profile = signing_profile_metadata(profile_id)
            return profile is None or (
                profile["enabled"]
                and binding.get("profile_revision") == profile["revision"]
                and binding.get("signing_fingerprint") == profile["signing_fingerprint"]
            )
        return artifact == unsigned

    def resolve_publication(self, request_url: str) -> PublicationResult:
        """Resolve locally retained public bytes without management permission."""
        values = dict(self.record["values"])
        if not self.record["publication_enabled"]:
            return PublicationResult("not-found")
        expiry = _parse_expiry(values.get("expires"))
        now = self.clock()
        if expiry is None or expiry <= now:
            return PublicationResult("not-found")
        if not canonical_url_matches(request_url, values.get("canonical", [])):
            return PublicationResult("not-found")
        if not self._artifact_matches(values):
            return PublicationResult("unavailable")
        return PublicationResult(
            "published",
            body=self.record["artifact"],
            etag=self.record["etag"],
            seconds_to_expiry=max(0, int((expiry - now).total_seconds())),
        )
