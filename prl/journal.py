from __future__ import annotations
import json
import os
import threading
from pathlib import Path
from .util import canonical, digest, plain
from .errors import ValidationError


class Journal:
    """Append-only, hash-linked local evidence; one writer per episode directory.

    Hashes detect accidental mutation, not malicious replacement of the entire log.
    Native live sessions cannot be resumed from this journal alone.
    """
    def __init__(self, path: Path, *, resume=False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.seq, self.previous = 0, "0"*64
        if self.path.exists():
            if not resume:
                raise FileExistsError(f"Refusing to overwrite {path}")
            rows = self.verify(self.path)
            if rows:
                self.seq, self.previous = len(rows), rows[-1]['hash']
        self._f = self.path.open('a', encoding='utf-8')

    def append(self, kind: str, data: dict):
        with self.lock:
            body = {'seq': self.seq, 'previous': self.previous, 'kind': kind, 'data': plain(data)}
            row = {**body, 'hash': digest(body)}
            self._f.write(canonical(row)+'\n')
            self._f.flush()
            self.previous = row['hash']
            self.seq += 1
            return row['hash']

    def close(self):
        if not self._f.closed:
            self._f.flush()
            os.fsync(self._f.fileno())
            self._f.close()

    @staticmethod
    def verify(path: Path):
        rows, prev = [], '0'*64
        for i, line in enumerate(Path(path).read_text().splitlines()):
            try:
                row = json.loads(line)
                h = row.pop('hash')
                if row['seq'] != i or row['previous'] != prev or digest(row) != h:
                    raise ValueError('chain mismatch')
                row['hash'] = h
                rows.append(row)
                prev = h
            except (KeyError, ValueError, TypeError) as e:
                raise ValidationError(f"Invalid journal row {i}: {e}") from e
        return rows
