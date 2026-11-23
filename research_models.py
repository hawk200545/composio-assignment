import json
import os
import re
import textwrap
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

ACCESS = (
    "free", "free_trial", "paid_plan", "admin_approval",
    "vendor_approval", "partnership", "contact_sales", "unavailable",
)
GATES = set(ACCESS) - {"free", "free_trial", "unavailable"}
OPTIONS = {
    "description": (),
    "auth": ("oauth2", "api_key", "basic", "token", "other", "none_required"),
    "developer_access": ACCESS,
    "production_access": tuple(value for value in ACCESS if value != "free_trial"),
    "api_interfaces": ("rest", "graphql", "grpc", "local_cli", "other", "no_public_interface"),
    "api_breadth": ("broad", "limited", "none"),
    "mcp": ("official", "community", "explicitly_unavailable"),
}
FIELDS = tuple(OPTIONS)
SINGLE_VALUE_FIELDS = {"description", "api_breadth"}
EXCLUSIVE_VALUES = {
    "auth": "none_required",
    "developer_access": "unavailable",
    "production_access": "unavailable",
    "api_interfaces": "no_public_interface",
    "mcp": "explicitly_unavailable",
}


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class App(Record):
    id: PositiveInt
    name: str
    category: str
    hint: str
    sources: list[str]
    toolkit_slug: str | None = Field(default=None, pattern=r"^[a-z0-9_-]+$")

    def allows(self, url: str) -> bool:
        candidate = split_https(url)
        if candidate is None:
            return False
        for rule in self.sources:
            prefix = split_https(rule)
            if prefix is None or candidate.hostname != prefix.hostname:
                continue
            path = prefix.path.rstrip("/")
            if candidate.path == path or candidate.path.startswith(path + "/") or not path:
                return True
        return False


class Source(Record):
    id: str
    url: str
    retrieved_at: str
    text: str


class Citation(Record):
    source_id: str
    quote: str


class Claim(Record):
    values: list[str]
    evidence: list[Citation]
    conflict: bool


class Profile(Record):
    description: Claim
    auth: Claim
    developer_access: Claim
    production_access: Claim
    api_interfaces: Claim
    api_breadth: Claim
    mcp: Claim


ReviewStatus = Literal["supported", "unsupported", "conflict", "contradicted"]


class Review(Record):
    description: ReviewStatus
    auth: ReviewStatus
    developer_access: ReviewStatus
    production_access: ReviewStatus
    api_interfaces: ReviewStatus
    api_breadth: ReviewStatus
    mcp: ReviewStatus


def unknown() -> Claim:
    return Claim(values=[], evidence=[], conflict=False)


def split_https(url: str):
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme == "https" and parsed.hostname and parsed.port is None
            and not parsed.username and not parsed.password
            and parsed.netloc.lower() == parsed.hostname
            and not re.search(r"[\s\\%]", parsed.netloc)
            and not re.search(r"(?:^|/)\.{1,2}(?:/|$)|%2[ef]|%5c|\\", parsed.path, re.I)
        ):
            return parsed
    except ValueError:
        pass
    return None


def normalize(text: str) -> str:
    text = " ".join(text.split())
    # HTML extraction can put a break between an inline link and its punctuation.
    return re.sub(r"\s+([.,;:!?])(?=\s|$)", r"\1", text)


def repair_citations(claim: Claim, sources_by_id: dict[str, str]) -> Claim:
    evidence = []
    for citation in claim.evidence:
        text = sources_by_id.get(citation.source_id, "")
        quote = normalize(citation.quote)
        if quote not in text:
            fragments = [normalize(part) for part in re.split(r"\.{3}|…", citation.quote)]
        elif 320 < len(quote) <= 1200:
            fragments = textwrap.wrap(quote, width=250, break_long_words=False, break_on_hyphens=False)
        else:
            fragments = []
        if len(fragments) > 1 and all(12 <= len(part) <= 320 and part in text for part in fragments):
            evidence.extend(Citation(source_id=citation.source_id, quote=fragment) for fragment in fragments)
        else:
            evidence.append(citation)
    return claim.model_copy(update={"evidence": evidence})


def evidence_issues(profile: Profile, sources: list[Source]) -> dict[str, str]:
    source_text = {source.id: normalize(source.text) for source in sources}
    issues = {}
    for field in FIELDS:
        claim = getattr(profile, field)
        values = claim.values
        if claim.conflict:
            issues[field] = "sources conflict"
        elif not values:
            issues[field] = "no supported answer"
        elif field == "production_access" and "free_trial" in values:
            issues[field] = "trial access belongs in developer access"
        elif field in {"developer_access", "production_access"} and len(
            {"free", "free_trial", "paid_plan"}.intersection(values)
        ) > 1:
            issues[field] = "choose one cost tier for the least-gated documented route"
        elif (
            any(not value.strip() or value != value.strip() for value in values)
            or len(values) != len(set(values))
            or (OPTIONS[field] and any(value not in OPTIONS[field] for value in values))
            or (field in SINGLE_VALUE_FIELDS and len(values) != 1)
            or (len(values) > 1 and EXCLUSIVE_VALUES.get(field) in values)
        ):
            issues[field] = "invalid values"
        elif not claim.evidence:
            issues[field] = "missing citation"
        elif any(
            not 12 <= len(normalize(citation.quote)) <= 320
            or normalize(citation.quote) not in source_text.get(citation.source_id, "")
            for citation in claim.evidence
        ):
            issues[field] = "citation quote missing from fetched evidence"
    return issues


def verdict(profile: Profile) -> tuple[str, str]:
    interfaces = set(profile.api_interfaces.values)
    breadth = profile.api_breadth.values
    production = set(profile.production_access.values)
    auth = profile.auth.values
    if interfaces == {"local_cli"}:
        return "Limited", "Evidence supports a local command-line integration"
    if interfaces == {"no_public_interface"} or breadth == ["none"]:
        return "Limited", "Evidence indicates no usable public interface"
    if not interfaces or not breadth:
        return "Unresolved", "API interface or breadth is unverified"
    if production & GATES:
        return "Gated", ", ".join(sorted(gate.replace("_", " ") for gate in production & GATES))
    if production == {"unavailable"}:
        return "Limited", "Production credentials are unavailable"
    if breadth == ["limited"]:
        return "Limited", "Documented API covers a narrow set of actions"
    if "free" in production and auth:
        return "Ready", ""
    if production == {"free_trial"}:
        return "Unresolved", "Only trial access to production is documented"
    return "Unresolved", "Production credential path or authentication is unverified"


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def write_json(path: Path, payload: object) -> None:
    atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
