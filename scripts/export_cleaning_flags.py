#!/usr/bin/env python3
"""Export portable cleaning warnings and eligibility reasons, without any prose.

The source SQLite database is read-only. The gzip sidecar is published atomically;
original text-only exports, metadata, database, and cleaning rules are untouched.
"""
import argparse
from collections import Counter
from contextlib import closing
import gzip
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import zlib


def export(database, output):
    database, output = database.expanduser().resolve(), output.expanduser().resolve()
    if database == output:
        raise ValueError('Output must not overwrite the source database')
    if not database.is_file():
        raise ValueError('Source database does not exist')
    output.parent.mkdir(parents=True, exist_ok=True)
    totals, warnings_count, reasons_count, statuses = Counter(), Counter(), Counter(), Counter()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', prefix=output.name + '.', suffix='.tmp',
                                         dir=output.parent, delete=False) as raw_output:
            temporary = Path(raw_output.name)
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw_output, compresslevel=3, mtime=0) as stream:
                with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
                    for record_id, content_hash, quality_status, blob in db.execute(
                            'SELECT id,hash,quality_status,payload FROM records ORDER BY rid'):
                        record = json.loads(zlib.decompress(blob))
                        cleaning = record['extra']['cleaning']
                        warnings = cleaning.get('warnings', [])
                        reasons = cleaning.get('reasons', [])
                        assert isinstance(warnings, list) and all(isinstance(value, str) for value in warnings)
                        assert isinstance(reasons, list) and all(isinstance(value, str) for value in reasons)
                        assert cleaning['status'] == quality_status
                        assert record['content_hash'] == content_hash and record['id'] == record_id
                        totals['records_scanned'] += 1
                        if not warnings and not reasons:
                            continue
                        entry = {'id': record_id, 'content_hash': content_hash,
                                 'warnings': warnings, 'quality_status': quality_status, 'reasons': reasons}
                        stream.write(json.dumps(entry, ensure_ascii=False, separators=(',', ':')).encode() + b'\n')
                        totals['flagged_records'] += 1
                        if 'nonempty_source_became_empty' in warnings:
                            totals['nonempty_became_empty_records'] += 1
                        warnings_count.update(warnings)
                        reasons_count.update(reasons)
                        statuses[quality_status] += 1
            raw_output.flush()
            os.fsync(raw_output.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    with output.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    result = {**totals, 'bytes': output.stat().st_size, 'sha256': digest,
              'quality_status_counts': dict(statuses), 'warning_counts': dict(warnings_count),
              'reason_counts': dict(reasons_count)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    export(args.database, args.output)
