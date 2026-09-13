#!/usr/bin/env python3
"""Append normalized AI-enrichment pairs without rewriting existing viewer records.

The only automatically discovered inputs are ROOT/ai-enrichment/*/pairs.jsonl.
No remote services are used. Importing this module has no I/O side effects.

export(root, emit) supplies the same hash-free rows to a complete viewer rebuild.
ingest(root, database, catalog_path=None) appends to an existing viewer database.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import zlib


ARTICLE_COLLECTION = "ai-enrichment-articles"
UNIT_COLLECTION = "ai-enrichment-units"
COLLECTION_TITLES = {
    ARTICLE_COLLECTION: "AI enrichment · full articles",
    UNIT_COLLECTION: "AI enrichment · short units",
}
DEFAULT_DESCRIPTION = (
    "AI-generated comparison candidates from local enrichment runs. "
    "Not independently human-validated gold; provenance and generation details remain in each record."
)
RECORD_COLUMNS = {
    "rid", "id", "collection", "language", "pair_type", "family", "title",
    "hash", "search_text", "payload",
}


class IngestError(ValueError):
    """Invalid source data, incompatible database, or immutable-ID conflict."""


class CatalogPublishError(RuntimeError):
    """The database committed, but its recoverable catalog-file publication failed."""


def canonical_json(value: object) -> bytes:
    """Match build_data_viewer.py: preserve key order; do not sort keys."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def prepare_row(value: dict, location: str = "record") -> tuple[dict, str]:
    """Validate a normalized row, discard any supplied hash, and compute its hash.

    Dict comprehension preserves the original order of every remaining input key.
    No defaults, normalization, or metadata fields are added to the hashed object.
    The returned object is a fresh deep copy, so emit callbacks cannot alter input.
    """
    if not isinstance(value, dict):
        raise IngestError(f"{location}: expected a JSON object")
    row = copy.deepcopy({key: item for key, item in value.items() if key != "content_hash"})
    for key in ("id", "collection", "title", "pair_type", "language"):
        if not isinstance(row.get(key), str):
            raise IngestError(f"{location}: {key} must be a string")
    for key in ("id", "collection", "pair_type", "language"):
        if not row[key]:
            raise IngestError(f"{location}: {key} must not be empty")
    if not isinstance(row.get("left"), dict) or not isinstance(row["left"].get("text"), str):
        raise IngestError(f"{location}: left.text must be a string")
    right = row.get("right")
    if right is not None and (not isinstance(right, dict) or not isinstance(right.get("text"), str)):
        raise IngestError(f"{location}: right must be null or contain a string text")
    alternatives = row.get("alternatives", [])
    if not isinstance(alternatives, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("text"), str)
        for item in alternatives
    ):
        raise IngestError(f"{location}: alternatives must be a list of objects with string text")
    if "family" in row and not isinstance(row["family"], str):
        raise IngestError(f"{location}: family must be a string")
    if "collection_title" in row and not isinstance(row["collection_title"], str):
        raise IngestError(f"{location}: collection_title must be a string")
    try:
        digest = hashlib.sha256(canonical_json(row)).hexdigest()
    except (TypeError, ValueError) as exc:
        raise IngestError(f"{location}: row is not valid canonical JSON: {exc}") from exc
    return row, digest


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise IngestError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def input_paths(root: Path) -> list[Path]:
    """Only read the designated pairs files; do not walk experiments or other data."""
    return sorted(Path(root).expanduser().glob("ai-enrichment/*/pairs.jsonl"))


def iter_rows(root: Path):
    """Yield validated rows without content_hash, in stable file/line order.

    Identical repeated IDs across runs are emitted once. A changed repeated ID is
    an error, including changes that preserve a caller-supplied content_hash.
    """
    seen = {}
    for path in input_paths(root):
        with path.open(encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                location = f"{path}:{lineno}"
                try:
                    value = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
                except (json.JSONDecodeError, IngestError) as exc:
                    raise IngestError(f"{location}: {exc}") from exc
                row, digest = prepare_row(value, location)
                prior = seen.get(row["id"])
                if prior is not None:
                    if prior != digest:
                        raise IngestError(f"{location}: changed input for repeated ID {row['id']!r}")
                    continue
                seen[row["id"]] = digest
                yield row


def export(root: Path, emit) -> list[dict]:
    """Emit all unique enrichment rows and return builder-compatible metadata.

    Pass build_data_viewer.build's existing emit callback directly. Its hashing
    and compression remain unchanged because all emitted rows lack content_hash.
    An empty/missing enrichment directory returns [] and emits nothing.
    """
    summaries = {}
    for row in iter_rows(root):
        ident = row["collection"]
        title = row.get("collection_title") or COLLECTION_TITLES.get(ident, ident)
        family = row.get("family", "")
        if ident not in summaries:
            summaries[ident] = {
                "id": ident, "collection": ident, "title": title, "family": family,
                "count": 0, "languages": collections.Counter(),
                "pair_types": collections.Counter(),
                "description": DEFAULT_DESCRIPTION, "source_url": None,
                "license": None, "data_local_only": True,
            }
        summary = summaries[ident]
        if summary["title"] != title or summary["family"] != family:
            raise IngestError(f"inconsistent title or family for collection {ident!r}")
        # Summarize before emit: the existing builder appends content_hash in-place.
        summary["count"] += 1
        summary["languages"][row["language"]] += 1
        summary["pair_types"][row["pair_type"]] += 1
        emit(row)
    result = list(summaries.values())
    for summary in result:
        summary["languages"] = dict(summary["languages"])
        summary["pair_types"] = dict(summary["pair_types"])
    return result


def default_collection(collections: list[dict], fallback: str) -> str:
    """Prefer the new article collection; preserve the old default when absent."""
    return ARTICLE_COLLECTION if any(
        (item.get("id") or item.get("collection")) == ARTICLE_COLLECTION and
        item.get("count", item.get("record_count", 0)) > 0
        for item in collections
    ) else fallback


def search_text(row: dict) -> str:
    """Exactly the builder's indexed text, including every alternative."""
    return "\n".join(
        [row["title"], row["left"]["text"], (row.get("right") or {}).get("text", "")]
        + [item.get("text", "") for item in row.get("alternatives", [])]
    ).lower()


def _insert_row(db: sqlite3.Connection, value: dict) -> bool:
    row, digest = prepare_row(value)
    previous = db.execute("SELECT hash FROM records WHERE id=?", (row["id"],)).fetchone()
    if previous is not None:
        if previous[0] != digest:
            raise IngestError(
                f"immutable ID conflict for {row['id']!r}: existing hash {previous[0]}, incoming {digest}"
            )
        return False
    row["content_hash"] = digest
    text = search_text(row)
    cursor = db.execute(
        "INSERT INTO records(id,collection,language,pair_type,family,title,hash,search_text,payload) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (row["id"], row["collection"], row["language"], row["pair_type"], row.get("family", ""),
         row["title"], digest, text, zlib.compress(canonical_json(row), 1)),
    )
    # The existing external-content FTS table has no synchronization triggers.
    # INSERT INTO records alone would leave new records invisible to MATCH.
    db.execute("INSERT INTO search(rowid,search_text) VALUES (?,?)", (cursor.lastrowid, text))
    return True


def _check_schema(db: sqlite3.Connection) -> dict:
    columns = {row[1] for row in db.execute("PRAGMA table_info(records)")}
    if not RECORD_COLUMNS.issubset(columns):
        raise IngestError("database does not have the expected viewer records schema")
    fts = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='search'").fetchone()
    if not fts or "fts5" not in (fts[0] or "").lower():
        raise IngestError("database does not have the expected FTS5 search table")
    # Explicit indexing is only correct for this builder's trigger-free schema.
    triggers = db.execute(
        "SELECT name,sql FROM sqlite_master WHERE type='trigger' AND tbl_name='records'"
    ).fetchall()
    if any("search" in (sql or "").lower() for _, sql in triggers):
        raise IngestError("records has an FTS synchronization trigger; explicit insertion would duplicate indexing")
    catalog_row = db.execute("SELECT value FROM metadata WHERE key='catalog'").fetchone()
    if catalog_row is None:
        raise IngestError("database catalog metadata is missing")
    try:
        catalog = json.loads(catalog_row[0])
    except (TypeError, ValueError) as exc:
        raise IngestError("database catalog is not valid JSON") from exc
    if not isinstance(catalog, dict) or not isinstance(catalog.get("collections"), list):
        raise IngestError("database catalog has an incompatible structure")
    return catalog


def _catalog_from_database(db: sqlite3.Connection, catalog: dict, incoming: list[dict]) -> dict:
    """Preserve existing metadata while deriving all counts from committed rows."""
    counts = collections.Counter()
    languages = collections.Counter()
    pair_types = collections.Counter()
    by_collection = collections.defaultdict(collections.Counter)
    for ident, language, kind, count in db.execute(
        "SELECT collection,language,pair_type,COUNT(*) FROM records GROUP BY collection,language,pair_type"
    ):
        counts[ident] += count
        languages[language] += count
        pair_types[kind] += count
        by_collection[ident][kind] += count
    existing = {}
    for item in catalog["collections"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise IngestError("catalog collection is missing its string ID")
        if item["id"] in existing:
            raise IngestError(f"duplicate collection metadata: {item['id']!r}")
        existing[item["id"]] = copy.deepcopy(item)
    # Preserve descriptions, titles, rights and other fields on old collections.
    for item in incoming:
        if item["id"] not in existing:
            existing[item["id"]] = {
                key: copy.deepcopy(value) for key, value in item.items()
                if key not in ("collection", "languages")
            }
    unknown = set(counts) - set(existing)
    if unknown:
        raise IngestError(f"database collections missing catalog metadata: {sorted(unknown)!r}")
    for ident, item in existing.items():
        item["count"] = counts[ident]
        item["pair_types"] = dict(by_collection[ident])
    result = copy.deepcopy(catalog)
    result.update({
        "total_records": sum(counts.values()), "collections": list(existing.values()),
        "languages": dict(languages), "pair_types": dict(pair_types),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    result["default_collection"] = default_collection(result["collections"], catalog.get("default_collection", ""))
    return result


def _atomic_json(path: Path, value: dict) -> None:
    """Publish in the target directory with fsync + atomic replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="." + path.name + ".", suffix=".tmp", delete=False) as handle:
            temp = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        temp = None
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


@contextlib.contextmanager
def _writer_lock(database: Path):
    # Covers the DB commit AND catalog publication, so concurrent copies of this
    # importer cannot publish an older catalog after a newer import finishes.
    lock_path = database.with_name(database.name + ".enrichment.lock")
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def ingest(root: Path, database: Path, catalog_path: Path | None = None) -> dict:
    """Append all new pairs atomically; existing IDs are immutable.

    Rows, explicit FTS entries, and authoritative metadata commit together in WAL.
    The JSON catalog is a derived file, published atomically after commit and a
    TRUNCATE checkpoint attempt. Busy readers may defer checkpoint completion.
    If file publication fails after commit, retrying this function republishes it
    without duplicating records. No existing row, hash, payload or review is edited.
    """
    root = Path(root).expanduser().resolve()
    database = Path(database).expanduser().resolve()
    if not database.is_file():
        raise IngestError(f"existing viewer database required: {database}")
    catalog_path = (Path(catalog_path).expanduser().resolve() if catalog_path is not None
                    else database.parent / "catalog.json")
    if catalog_path == database:
        raise IngestError("catalog path must differ from the database path")
    with _writer_lock(database):
        db = sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=30, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=30000")
            mode = db.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            if mode.lower() != "wal":
                raise IngestError(f"could not enable WAL journal mode: {mode}")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            catalog = _check_schema(db)
            inserted = 0
            skipped = 0

            def emit(row):
                nonlocal inserted, skipped
                if _insert_row(db, row):
                    inserted += 1
                else:
                    skipped += 1

            incoming = export(root, emit)
            catalog = _catalog_from_database(db, catalog, incoming)
            db.execute("UPDATE metadata SET value=? WHERE key='catalog'",
                       (json.dumps(catalog, ensure_ascii=False),))
            db.execute("COMMIT")
            checkpoint = db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            try:
                _atomic_json(catalog_path, catalog)
            except Exception as exc:
                raise CatalogPublishError(
                    "database import committed, but catalog-file publication failed; "
                    "rerun the same ingest to repair the catalog without duplicating rows"
                ) from exc
            return {
                "inserted": inserted, "skipped_existing": skipped,
                "total_records": catalog["total_records"], "collections": len(catalog["collections"]),
                "default_collection": catalog["default_collection"],
                "input_files": [str(path) for path in input_paths(root)],
                "database": str(database), "catalog": str(catalog_path),
                "checkpoint": {"busy": checkpoint[0], "log_frames": checkpoint[1],
                               "checkpointed_frames": checkpoint[2]},
            }
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        finally:
            db.close()


def _fixture_row(ident: str, collection: str, text: str, language: str = "en") -> dict:
    return {
        "id": ident, "collection": collection,
        "collection_title": COLLECTION_TITLES.get(collection, "Existing collection"),
        "family": "ai-enrichment" if collection in COLLECTION_TITLES else "existing",
        "language": language, "pair_type": "same-task", "title": "Fixture " + ident,
        "left": {"label": "Human", "text": text, "role": "reference"},
        "right": {"label": "AI", "text": "Generated antelope comparison", "role": "candidate"},
        "alternatives": [{"text": "Reference pangolin alternative"}],
        "provenance": {"local_only": True, "notes": "Offline fixture, not project data."},
    }


def self_test() -> dict:
    """Meaningful offline fixtures; only disposable files below /private/tmp."""
    test_names = []
    with tempfile.TemporaryDirectory(prefix="plainvoice-ingest-test-", dir="/private/tmp") as tempdir:
        root = Path(tempdir)
        database = root / "viewer.sqlite"
        catalog_path = root / "catalog.json"
        old_row = _fixture_row("existing-1", "existing", "Preserved original text 中文")
        old_row, old_hash = prepare_row(old_row)
        old_payload = copy.deepcopy(old_row)
        old_payload["content_hash"] = old_hash
        old_search = search_text(old_row)
        old_catalog = {
            "schema_version": "plainvoice-viewer-1", "total_records": 1,
            "collections": [{"id": "existing", "title": "Existing collection", "family": "existing",
                             "count": 1, "description": "Preserve this exact description.",
                             "license": {"status": "fixture"}, "pair_types": {"same-task": 1}}],
            "languages": {"en": 1}, "pair_types": {"same-task": 1},
            "default_collection": "existing", "mode": "local", "extra_metadata": {"keep": True},
        }
        with sqlite3.connect(database) as db:
            db.executescript("""
                CREATE TABLE records(rid INTEGER PRIMARY KEY,id TEXT NOT NULL UNIQUE,collection TEXT,
                    language TEXT,pair_type TEXT,family TEXT,title TEXT,hash TEXT,search_text TEXT,payload BLOB);
                CREATE INDEX collection_records ON records(collection,rid);
                CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
                CREATE TABLE reviews(id TEXT,content_hash TEXT,decision TEXT);
                CREATE VIRTUAL TABLE search USING fts5(search_text,content='records',content_rowid='rid',tokenize='unicode61');
            """)
            db.execute("INSERT INTO records(id,collection,language,pair_type,family,title,hash,search_text,payload) VALUES (?,?,?,?,?,?,?,?,?)",
                       (old_row["id"], old_row["collection"], old_row["language"], old_row["pair_type"],
                        old_row["family"], old_row["title"], old_hash, old_search, zlib.compress(canonical_json(old_payload), 1)))
            db.execute("INSERT INTO search(search) VALUES('rebuild')")
            db.execute("INSERT INTO metadata VALUES('catalog',?)", (json.dumps(old_catalog),))
            db.execute("INSERT INTO reviews VALUES(?,?,?)", (old_row["id"], old_hash, "keep"))
            before = db.execute("SELECT * FROM records").fetchall()
            before_reviews = db.execute("SELECT * FROM reviews").fetchall()
        _atomic_json(catalog_path, old_catalog)
        inputs = root / "ai-enrichment" / "2026-09-12-gemini25" / "pairs.jsonl"
        inputs.parent.mkdir(parents=True)
        article = _fixture_row("article-1", ARTICLE_COLLECTION, "Quokka retry semantics 中文", "zh")
        unit = _fixture_row("unit-1", UNIT_COLLECTION, "Wombat unit comparison")
        # A supplied stale hash must not affect canonical identity or survive emit.
        article["content_hash"] = "supplied-hash-is-not-authoritative"

        def write_inputs(rows):
            inputs.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")

        write_inputs([old_payload, article, unit, copy.deepcopy(article)])
        first = ingest(root, database, catalog_path)
        assert (first["inserted"], first["skipped_existing"], first["total_records"]) == (2, 1, 3), first
        second = ingest(root, database, catalog_path)
        assert (second["inserted"], second["skipped_existing"], second["total_records"]) == (0, 3, 3), second
        assert second["checkpoint"]["busy"] == 0
        test_names.append("repeat_ingest_and_duplicate_input_are_idempotent")
        with sqlite3.connect(database) as db:
            assert db.execute("SELECT * FROM records WHERE id='existing-1'").fetchall() == before
            assert db.execute("SELECT * FROM reviews").fetchall() == before_reviews
            assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            for query, expected in [("quokka", {"article-1"}), ("wombat", {"unit-1"}),
                                    ("antelope", {"existing-1", "article-1", "unit-1"}),
                                    ("pangolin", {"existing-1", "article-1", "unit-1"})]:
                got = {row[0] for row in db.execute(
                    "SELECT r.id FROM records r JOIN search s ON r.rid=s.rowid WHERE search MATCH ?", (query,))}
                assert got == expected, (query, got)
            stored = db.execute("SELECT hash,payload FROM records WHERE id='article-1'").fetchone()
            clean, expected_hash = prepare_row(article)
            assert expected_hash == hashlib.sha256(json.dumps(clean, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
            assert stored[0] == expected_hash
            assert json.loads(zlib.decompress(stored[1])) == {**clean, "content_hash": expected_hash}
            catalog = json.loads(db.execute("SELECT value FROM metadata WHERE key='catalog'").fetchone()[0])
            snapshot_records = db.execute("SELECT * FROM records ORDER BY rid").fetchall()
            snapshot_metadata = db.execute("SELECT * FROM metadata ORDER BY key").fetchall()
        test_names += ["existing_rows_hashes_payloads_and_reviews_unchanged", "explicit_fts_title_comparison_and_alternatives_search",
                       "unicode_compact_key_order_hash_matches_builder"]
        assert catalog == json.loads(catalog_path.read_text())
        assert catalog["default_collection"] == ARTICLE_COLLECTION
        assert catalog["extra_metadata"] == {"keep": True}
        assert catalog["languages"] == {"en": 2, "zh": 1}
        assert catalog["pair_types"] == {"same-task": 3}
        assert {item["id"]: item["count"] for item in catalog["collections"]} == {"existing": 1, ARTICLE_COLLECTION: 1, UNIT_COLLECTION: 1}
        assert catalog["collections"][0]["description"] == old_catalog["collections"][0]["description"]
        test_names.append("catalog_counts_metadata_and_default_articles")
        emitted = []
        summaries = export(root, emitted.append)
        assert len(emitted) == 3 and all("content_hash" not in item for item in emitted)
        with sqlite3.connect(database) as db:
            for row in emitted:
                expected = hashlib.sha256(json.dumps(row, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
                assert db.execute("SELECT hash FROM records WHERE id=?", (row["id"],)).fetchone()[0] == expected
        assert sum(item["count"] for item in summaries) == 3
        test_names.append("full_rebuild_export_matches_incremental_hashes")
        # Insert a new row first, then encounter a changed old ID carrying the old
        # hash. The entire transaction, including its FTS insert, must roll back.
        conflict = copy.deepcopy(old_payload)
        conflict["left"]["text"] += " changed"
        write_inputs([_fixture_row("must-rollback", ARTICLE_COLLECTION, "Ocelot rollback sentinel"), conflict])
        try:
            ingest(root, database, catalog_path)
        except IngestError as exc:
            assert "immutable ID conflict" in str(exc)
        else:
            raise AssertionError("changed existing ID was accepted")
        with sqlite3.connect(database) as db:
            assert db.execute("SELECT * FROM records ORDER BY rid").fetchall() == snapshot_records
            assert db.execute("SELECT * FROM metadata ORDER BY key").fetchall() == snapshot_metadata
            assert db.execute("SELECT rowid FROM search WHERE search MATCH 'ocelot'").fetchall() == []
            assert db.execute("SELECT * FROM reviews").fetchall() == before_reviews
        assert json.loads(catalog_path.read_text()) == catalog
        test_names.append("changed_existing_id_with_same_supplied_hash_rolls_back_records_fts_metadata")
        changed_input = copy.deepcopy(article)
        changed_input["right"]["text"] += " changed"
        write_inputs([article, changed_input])
        try:
            export(root, lambda row: None)
        except IngestError as exc:
            assert "changed input for repeated ID" in str(exc)
        else:
            raise AssertionError("changed duplicate input ID was accepted")
        test_names.append("conflicting_duplicate_input_id_rejected")
        write_inputs([article, unit, _fixture_row("article-2", ARTICLE_COLLECTION, "Axolotl repair sentinel")])
        original_atomic_json = globals()["_atomic_json"]
        def fail_publication(path, value):
            raise OSError("injected catalog publication failure")
        globals()["_atomic_json"] = fail_publication
        try:
            try:
                ingest(root, database, catalog_path)
            except CatalogPublishError:
                pass
            else:
                raise AssertionError("publication failure was not reported")
        finally:
            globals()["_atomic_json"] = original_atomic_json
        assert json.loads(catalog_path.read_text())["total_records"] == 3
        repaired = ingest(root, database, catalog_path)
        assert repaired["inserted"] == 0 and repaired["total_records"] == 4
        assert json.loads(catalog_path.read_text())["total_records"] == 4
        with sqlite3.connect(database) as db:
            assert db.execute("SELECT * FROM reviews").fetchall() == before_reviews
            assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            db.execute("INSERT INTO search(search,rank) VALUES('integrity-check',1)")
        test_names.append("post_commit_catalog_failure_is_repaired_by_idempotent_rerun")
    return {"ok": True, "tests": test_names, "fixture_location": "/private/tmp (automatically removed)", "network_calls": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Desktop bundle root containing ai-enrichment/*/pairs.jsonl")
    parser.add_argument("--database", type=Path, help="Existing viewer SQLite database; never created implicitly")
    parser.add_argument("--catalog", type=Path, help="Local catalog JSON; defaults to database sibling catalog.json")
    parser.add_argument("--self-test", action="store_true", help="Run isolated offline /private/tmp fixtures only")
    args = parser.parse_args()
    if args.self_test:
        if args.root or args.database or args.catalog:
            parser.error("--self-test cannot be combined with production path arguments")
        result = self_test()
    else:
        if args.root is None or args.database is None:
            parser.error("--root and --database are required unless --self-test is used")
        result = ingest(args.root, args.database, args.catalog)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
