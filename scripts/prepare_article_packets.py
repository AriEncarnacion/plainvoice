#!/usr/bin/env python3
"""Validate full-article claim extractions and prepare reproducible writer packets.

Python standard library only. No source article access, model calls or generation.
See ../prompts/article-content-extraction.md for the extraction schema.

Example:
  python3 prepare_article_packets.py --input-dir /path/content-extraction \
      --writer-dir /path/writer-packets --audit-dir /path/packet-audit --seed 20260912

Only writer-dir should be mounted/passed to the writer. Audit permissions do NOT
isolate an agent running as the same OS user: the caller must enforce that boundary.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

VERSION = "article-packets-v1"
REQUIRED_CLAIM = {
    "id", "subject", "predicate", "object", "qualifiers", "attribution",
    "modality", "polarity", "depends_on", "source_locator",
}
CONTEXT_KEYS = {"language", "audience", "genre", "as_of"}
SOURCE_KEYS = {
    "source_locator", "source_title", "original_title", "title", "author",
    "byline", "author_style", "style", "style_instruction", "style_instructions",
    "section", "section_id", "section_number", "section_heading", "heading",
    "chapter", "paragraph", "paragraph_id", "paragraph_number", "sentence_index",
    "word_count", "original_word_count", "target_word_count", "length",
    "order", "original_order", "source_order", "position", "source_index",
    "source_url", "source_text", "original_text", "rhetorical_device",
}
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}\Z")


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def text(value, location):
    require(isinstance(value, str) and bool(value.strip()), f"{location}: expected nonempty string")


def locator(value, location):
    require((isinstance(value, str) and bool(value.strip())) or
            (isinstance(value, dict) and bool(value)), f"{location}: expected source locator")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def bad_constant(value):
    raise ValidationError(f"non-finite JSON number: {value}")


def finite_float(value):
    result = float(value)
    require(math.isfinite(result), f"non-finite JSON number: {value}")
    return result


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       indent=2, allow_nan=False) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def key_name(key):
    return re.sub(r"[\s-]+", "_", key).lower()


def inspect_semantics(value, where, claim_ids, in_code=False):
    """Validate structured references; never rewrite prose, numbers or code."""
    if isinstance(value, dict):
        for key, item in value.items():
            require(isinstance(key, str), f"{where}: object keys must be strings")
            require(in_code or key_name(key) not in SOURCE_KEYS,
                    f"{where}.{key}: source/style metadata cannot be inside semantic fields")
            if key == "claim_id" and not in_code:
                require(isinstance(item, str) and item in claim_ids,
                        f"{where}.claim_id: unknown claim reference")
            elif key == "claim_ids" and not in_code:
                references(item, claim_ids, f"{where}.claim_ids")
            else:
                inspect_semantics(item, f"{where}.{key}", claim_ids,
                                  in_code or key == "code")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            inspect_semantics(item, f"{where}[{index}]", claim_ids, in_code)
    elif isinstance(value, float):
        require(math.isfinite(value), f"{where}: non-finite number")
    else:
        require(value is None or isinstance(value, (str, int, bool)),
                f"{where}: unsupported JSON type")


def references(value, ids, where):
    require(isinstance(value, list) and all(isinstance(x, str) for x in value),
            f"{where}: expected list of ID strings")
    require(len(set(value)) == len(value), f"{where}: duplicate references")
    require(set(value) <= ids, f"{where}: unknown IDs {sorted(set(value) - ids)}")


def validate_document(doc, path):
    require(isinstance(doc, dict), f"{path}: expected JSON object")
    for field in ("article_id", "language", "claims", "excluded", "coverage"):
        require(field in doc, f"{path}: missing {field}")
    article_id = doc["article_id"]
    require(isinstance(article_id, str) and SAFE_ID.fullmatch(article_id),
            f"{path}: unsafe/empty article_id")
    require(path.stem == article_id, f"{path}: filename stem must equal article_id")
    text(doc["language"], "language")
    require(isinstance(doc["claims"], list) and doc["claims"], "claims: expected nonempty list")
    ids = set()
    for index, claim in enumerate(doc["claims"]):
        where = f"claims[{index}]"
        require(isinstance(claim, dict), f"{where}: expected object")
        require(REQUIRED_CLAIM <= claim.keys(),
                f"{where}: missing fields {sorted(REQUIRED_CLAIM - claim.keys())}")
        require(not (claim.keys() - REQUIRED_CLAIM - SOURCE_KEYS),
                f"{where}: unknown fields {sorted(claim.keys() - REQUIRED_CLAIM - SOURCE_KEYS)}")
        text(claim["id"], f"{where}.id")
        require(claim["id"] not in ids, f"{where}: duplicate claim ID {claim['id']}")
        ids.add(claim["id"])
        for field in ("subject", "predicate", "object", "modality"):
            text(claim[field], f"{where}.{field}")
        require(isinstance(claim["qualifiers"], dict), f"{where}.qualifiers: expected object")
        require(claim["attribution"] is None or
                (isinstance(claim["attribution"], str) and bool(claim["attribution"].strip())),
                f"{where}.attribution: expected string or null")
        require(claim["polarity"] in ("positive", "negative"),
                f"{where}.polarity: use positive/negative and scope negation explicitly")
        locator(claim["source_locator"], f"{where}.source_locator")
    graph = {}
    for claim in doc["claims"]:
        references(claim["depends_on"], ids, f"{claim['id']}.depends_on")
        require(claim["id"] not in claim["depends_on"], f"{claim['id']}: self dependency")
        graph[claim["id"]] = claim["depends_on"]
        inspect_semantics(claim["qualifiers"], f"{claim['id']}.qualifiers", ids)
    # depends_on means interpretive prerequisites, not an arbitrary graph of causes.
    remaining = {key: set(value) for key, value in graph.items()}
    resolved = set()
    while remaining:
        ready = {key for key, value in remaining.items() if value <= resolved}
        require(ready, "depends_on contains a cycle; express actual feedback loops as claim content")
        resolved.update(ready)
        remaining = {key: value for key, value in remaining.items() if key not in ready}
    require(isinstance(doc["excluded"], list), "excluded: expected list")
    excluded_ids = set()
    for item in doc["excluded"]:
        require(isinstance(item, dict), "excluded item: expected object")
        for field in ("id", "reason"):
            text(item.get(field), f"excluded.{field}")
        locator(item.get("source_locator"), "excluded.source_locator")
        require(item["id"] not in excluded_ids | ids, "duplicate excluded/claim ID")
        excluded_ids.add(item["id"])
    coverage = doc["coverage"]
    require(isinstance(coverage, dict), "coverage: expected object")
    require(coverage.get("scope") == "full_article", "coverage.scope must be full_article")
    require(coverage.get("uncovered_units") == [], "coverage.uncovered_units must be an empty list")
    units = coverage.get("units")
    require(isinstance(units, list) and units, "coverage.units: expected nonempty list")
    covered_claims, covered_exclusions, seen_locators = set(), set(), set()
    for index, unit in enumerate(units):
        require(isinstance(unit, dict), f"coverage.units[{index}]: expected object")
        locator(unit.get("source_locator"), f"coverage.units[{index}].source_locator")
        serialized_locator = canonical(unit["source_locator"])
        require(serialized_locator not in seen_locators, "duplicate coverage source_locator")
        seen_locators.add(serialized_locator)
        references(unit.get("claim_ids"), ids, f"coverage.units[{index}].claim_ids")
        references(unit.get("excluded_ids"), excluded_ids, f"coverage.units[{index}].excluded_ids")
        require(unit["claim_ids"] or unit["excluded_ids"], "coverage unit has no disposition")
        covered_claims.update(unit["claim_ids"])
        covered_exclusions.update(unit["excluded_ids"])
    require(covered_claims == ids, f"claims missing from coverage: {sorted(ids - covered_claims)}")
    require(covered_exclusions == excluded_ids, "excluded items missing from coverage")
    context = doc.get("context", {})
    require(isinstance(context, dict), "context: expected object")
    for key in CONTEXT_KEYS & context.keys():
        text(context[key], f"context.{key}")
    if "language" in context:
        require(context["language"] == doc["language"], "context.language conflicts with language")
    return ids


def remap_refs(value, mapping, in_code=False):
    if isinstance(value, list):
        return [remap_refs(item, mapping, in_code) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == "code" or in_code:
                result[key] = copy.deepcopy(item)
            elif key == "claim_id":
                result[key] = mapping[item]
            elif key == "claim_ids":
                result[key] = [mapping[x] for x in item]
            else:
                result[key] = remap_refs(item, mapping)
        return result
    return value


def prepare(doc, source_bytes, source_path, seed):
    article_id = doc["article_id"]
    def pseudorandom(domain, value):
        return hmac.new(str(seed).encode("ascii"),
                        canonical([VERSION, domain, article_id, value]),
                        hashlib.sha256).hexdigest()
    packet_id = "p_" + pseudorandom("packet-id", "")[:20]
    mapping = {claim["id"]: "c_" + pseudorandom("claim-id", claim["id"])[:20]
               for claim in doc["claims"]}
    require(len(set(mapping.values())) == len(mapping), "claim ID hash collision")
    original_order = [claim["id"] for claim in doc["claims"]]
    shuffled = sorted(doc["claims"], key=lambda c: pseudorandom("storage-order", c["id"]))
    # Tiny packets can randomly retain their original order; still change storage order.
    if len(shuffled) > 1 and [c["id"] for c in shuffled] == original_order:
        shuffled = shuffled[1:] + shuffled[:1]
    claims = []
    for claim in shuffled:
        projected = {field: copy.deepcopy(claim[field])
                     for field in REQUIRED_CLAIM - {"source_locator"}}
        projected["id"] = mapping[claim["id"]]
        projected["depends_on"] = [mapping[x] for x in claim["depends_on"]]
        projected["qualifiers"] = remap_refs(claim["qualifiers"], mapping)
        for field in ("subject", "object", "attribution"):
            if projected[field] == "source_author":
                projected[field] = "narrator"
        claims.append(projected)
    packet = {"schema_version": VERSION, "packet_id": packet_id,
              "language": doc["language"], "claims": claims}
    context = {key: value for key, value in doc.get("context", {}).items()
               if key in CONTEXT_KEYS and key != "language"}
    if context:
        packet["context"] = context
    packet_bytes = canonical(packet)
    audit = {
        "schema_version": VERSION, "operation": "prepare_writer_packet",
        "article_id": article_id, "packet_id": packet_id, "seed": seed,
        "permutation_algorithm": "domain-separated HMAC-SHA256 sort; rotate if identity",
        "source_extraction_path": str(source_path),
        "source_extraction_sha256": digest(source_bytes),
        "packet_sha256": digest(packet_bytes),
        "claim_id_map": mapping,
        "original_claim_order": original_order,
        "shuffled_original_claim_order": [claim["id"] for claim in shuffled],
        "source_locators": {claim["id"]: claim["source_locator"] for claim in doc["claims"]},
        "withheld_top_level_fields": sorted(set(doc) - {"language", "claims", "context"}),
        "withheld_context_fields": sorted(set(doc.get("context", {})) - CONTEXT_KEYS),
        "withheld_claim_fields": {claim["id"]: sorted(set(claim) -
                                  (REQUIRED_CLAIM - {"source_locator"})) for claim in doc["claims"]},
        "extraction_coverage": doc["coverage"], "excluded": doc["excluded"],
        "checks": {
            "claim_count": len(claims), "dependency_edge_count": sum(len(c["depends_on"]) for c in claims),
            "source_unit_count": len(doc["coverage"]["units"]),
            "excluded_unit_record_count": len(doc["excluded"]),
            "all_input_claims_transferred": len(claims) == len(doc["claims"]),
            "storage_order_changed": len(claims) > 1,
            "semantic_text_rewritten": False,
            "source_author_role_normalized_to_narrator": True,
            "generation_performed": False,
            "coverage_validation": "extraction self-report consistency only; original article not read",
        },
        "writer_isolation": "Caller must expose only the packet. Same-user filesystem permissions do not enforce agent isolation.",
    }
    return packet_id, packet_bytes, audit


def disjoint(left, right):
    return left != right and left not in right.parents and right not in left.parents


def atomic_write(path, data, private):
    fd, temporary = tempfile.mkstemp(prefix=".packet-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600 if private else 0o644)
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--writer-dir", type=Path, required=True)
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--check-only", action="store_true", help="validate/plan only; write nothing")
    parser.add_argument("--overwrite", action="store_true", help="replace differing existing outputs; identical files are always reusable")
    args = parser.parse_args(argv)
    try:
        require(0 <= args.seed < 2**64, "seed must be an unsigned 64-bit integer")
        input_dir, writer_dir, audit_dir = [p.resolve() for p in (args.input_dir, args.writer_dir, args.audit_dir)]
        require(input_dir.is_dir(), "input-dir is not a directory")
        require(disjoint(writer_dir, audit_dir), "audit-dir and writer-dir must be disjoint")
        require(disjoint(input_dir, writer_dir) and disjoint(input_dir, audit_dir),
                "input-dir must be disjoint from both output directories")
        inputs = sorted(input_dir.glob("*.json"))
        require(inputs, "no extraction JSON files found")
        outputs, records, seen_packets = [], [], set()
        for path in inputs:
            require(path.is_file() and not path.is_symlink(), f"{path}: expected ordinary file, not symlink")
            require(path.stat().st_size <= 32 * 1024 * 1024, f"{path}: extraction exceeds 32 MiB")
            raw = path.read_bytes()
            doc = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object,
                             parse_constant=bad_constant, parse_float=finite_float)
            validate_document(doc, path)
            packet_id, packet_bytes, audit = prepare(doc, raw, path, args.seed)
            require(packet_id not in seen_packets, "packet ID collision")
            seen_packets.add(packet_id)
            packet_path = writer_dir / f"{packet_id}.json"
            audit_path = audit_dir / f"{packet_id}.audit.json"
            outputs.extend([(packet_path, packet_bytes, False), (audit_path, canonical(audit), True)])
            records.append({"article_id": doc["article_id"], "packet_id": packet_id,
                            "packet_path": str(packet_path), "audit_path": str(audit_path),
                            "input_sha256": audit["source_extraction_sha256"],
                            "packet_sha256": audit["packet_sha256"], **audit["checks"]})
        report = {"schema_version": VERSION, "operation": "prepare_writer_packets",
                  "seed": args.seed, "script_sha256": digest(Path(__file__).read_bytes()),
                  "article_count": len(records), "claim_count": sum(r["claim_count"] for r in records),
                  "generation_performed": False, "packets": records,
                  "writer_input_scope": "Only opaque packet JSONs. This report and audit files are coordinator-only."}
        outputs.append((audit_dir / "packet-report.json", canonical(report), True))
        # Validate all input and all destinations before publishing any packet.
        for path, payload, _ in outputs:
            require(not path.is_symlink(), f"refusing symlink destination: {path}")
            require(not path.exists() or (path.is_file() and
                    (path.read_bytes() == payload or args.overwrite)),
                    f"output exists and differs: {path}; choose new directories or --overwrite")
        if not args.check_only:
            writer_dir.mkdir(parents=True, exist_ok=True)
            audit_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(audit_dir, 0o700)
            for path, payload, private in outputs:
                if path.exists() and path.read_bytes() == payload:
                    if private:
                        os.chmod(path, 0o600)
                    continue
                atomic_write(path, payload, private)
        print(json.dumps({"status": "validated_only" if args.check_only else "packets_prepared",
                          "article_count": len(records), "claim_count": report["claim_count"],
                          "generation_performed": False, "writer_dir": str(writer_dir),
                          "coordinator_report": str(audit_dir / "packet-report.json")}, ensure_ascii=False))
        return 0
    except (ValidationError, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(json.dumps({"status": "failed", "error": str(error), "generation_performed": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
