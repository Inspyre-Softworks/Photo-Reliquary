"""SQLite storage implementation.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Iterable, Sequence

from photo_reliquary.analysis.models import AnalysisResult, AnalysisRun
from photo_reliquary.exceptions import StorageError
from photo_reliquary.logging_utils import ReliquaryLoggable
from photo_reliquary.models import IdentityStorageMode, PhotoRecord, ScanIssue, ScanIssueType
from photo_reliquary.utils.paths import ensure_parent_directory, normalize_path


class SQLitePhotoStore(ReliquaryLoggable):
    """Encapsulated SQLite storage for Photo Reliquary.

    Methods:
        upsert_photo: Create or update a tracked photo record.
        add_tag: Attach a manual tag to a photo.
        store_analysis_result: Persist structured machine annotations.
    """

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.database_path = normalize_path(database_path)
        ensure_parent_directory(self.database_path)
        try:
            self._connection = sqlite3.connect(self.database_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute('PRAGMA foreign_keys = ON')
        except sqlite3.Error as error:
            raise StorageError(f'Unable to open SQLite database at {self.database_path}: {error}') from error
        self.initialize()

    @staticmethod
    def utc_now() -> str:
        """Return a UTC ISO timestamp."""

        return datetime.now(tz=UTC).isoformat()

    def initialize(self) -> None:
        """Create the initial schema if needed."""

        schema_path = files('photo_reliquary.storage').joinpath('schema.sql')
        try:
            self._connection.executescript(schema_path.read_text(encoding='utf-8'))
            self._connection.commit()
        except sqlite3.Error as error:
            raise StorageError(f'Unable to initialize SQLite schema: {error}') from error
        self.log_device.info(f'Initialized SQLite store at {self.database_path}.')

    def close(self) -> None:
        """Close the SQLite connection."""

        self._connection.close()

    def _row_to_photo(self, row: sqlite3.Row | None) -> PhotoRecord | None:
        if row is None:
            return None
        return PhotoRecord(
            photo_id=row['photo_id'],
            current_path=Path(row['current_path']),
            checksum=row['checksum'],
            checksum_algorithm=row['checksum_algorithm'],
            checksum_tail=row['checksum_tail'],
            size_bytes=row['size_bytes'],
            mtime_ns=row['mtime_ns'],
            first_seen_at=row['first_seen_at'],
            last_seen_at=row['last_seen_at'],
            missing_since=row['missing_since'],
            identity_storage_mode=IdentityStorageMode(row['identity_storage_mode']),
        )

    def _execute(self, sql: str, parameters: Sequence[object] = ()) -> sqlite3.Cursor:
        try:
            cursor = self._connection.execute(sql, parameters)
            self._connection.commit()
            return cursor
        except sqlite3.Error as error:
            raise StorageError(f'SQLite operation failed: {error}') from error

    def get_photo_by_id(self, photo_id: str) -> PhotoRecord | None:
        """Return a photo record by photo ID."""

        row = self._execute('SELECT * FROM photos WHERE photo_id = ?', (photo_id,)).fetchone()
        return self._row_to_photo(row)

    def get_photo_by_path(self, path: Path | str) -> PhotoRecord | None:
        """Return a photo record by current path."""

        row = self._execute(
            '''
            SELECT *
            FROM photos
            WHERE current_path = ?
            ORDER BY CASE WHEN missing_since IS NULL THEN 0 ELSE 1 END, last_seen_at DESC
            LIMIT 1
            ''',
            (str(normalize_path(path)),),
        ).fetchone()
        return self._row_to_photo(row)

    def get_photo_by_checksum(self, checksum: str) -> PhotoRecord | None:
        """Return the first photo record matching a checksum."""

        row = self._execute('SELECT * FROM photos WHERE checksum = ? ORDER BY first_seen_at ASC LIMIT 1', (checksum,)).fetchone()
        return self._row_to_photo(row)

    def upsert_photo(self, photo: PhotoRecord) -> PhotoRecord:
        """Insert or update a photo record."""

        self._execute(
            '''
            INSERT INTO photos (
                photo_id, current_path, checksum, checksum_algorithm, checksum_tail,
                size_bytes, mtime_ns, first_seen_at, last_seen_at, missing_since,
                identity_storage_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(photo_id) DO UPDATE SET
                current_path = excluded.current_path,
                checksum = excluded.checksum,
                checksum_algorithm = excluded.checksum_algorithm,
                checksum_tail = excluded.checksum_tail,
                size_bytes = excluded.size_bytes,
                mtime_ns = excluded.mtime_ns,
                last_seen_at = excluded.last_seen_at,
                missing_since = excluded.missing_since,
                identity_storage_mode = excluded.identity_storage_mode
            ''',
            (
                photo.photo_id,
                str(normalize_path(photo.current_path)),
                photo.checksum,
                photo.checksum_algorithm,
                photo.checksum_tail,
                photo.size_bytes,
                photo.mtime_ns,
                photo.first_seen_at,
                photo.last_seen_at,
                photo.missing_since,
                photo.identity_storage_mode.value,
            ),
        )
        self.log_device.debug(f'Upserted photo record {photo.photo_id} at {photo.current_path}.')
        refreshed = self.get_photo_by_id(photo.photo_id)
        if refreshed is None:
            raise StorageError(f'Unable to reload photo record {photo.photo_id} after upsert.')
        return refreshed

    def list_photos(self) -> list[PhotoRecord]:
        """Return all tracked photos."""

        rows = self._execute('SELECT * FROM photos ORDER BY current_path ASC').fetchall()
        return [self._row_to_photo(row) for row in rows if row is not None]

    def list_photos_by_ids(self, photo_ids: Iterable[str]) -> list[PhotoRecord]:
        """Return photos matching the provided IDs."""

        requested_ids = list(photo_ids)
        if not requested_ids:
            return []

        # Deduplicate IDs while preserving insertion order.
        unique_ids = list(dict.fromkeys(requested_ids))
        placeholders = ', '.join('?' for _ in unique_ids)
        rows = self._execute(
            f'''
            SELECT
                photo_id,
                current_path,
                checksum,
                checksum_algorithm,
                checksum_tail,
                size_bytes,
                mtime_ns,
                first_seen_at,
                last_seen_at,
                missing_since,
                identity_storage_mode
            FROM photos
            WHERE photo_id IN ({placeholders})
            ''',
            tuple(unique_ids),
        ).fetchall()
        photo_map = {
            row['photo_id']: photo
            for row in rows
            if (photo := self._row_to_photo(row)) is not None
        }
        return [photo_map[photo_id] for photo_id in requested_ids if photo_id in photo_map]

    def resolve_photo(self, reference: str) -> PhotoRecord:
        """Resolve a photo by photo ID or path string."""

        photo = self.get_photo_by_id(reference)
        if photo is not None:
            return photo
        by_path = self.get_photo_by_path(reference)
        if by_path is not None:
            return by_path
        raise StorageError(f'Unable to resolve photo reference: {reference}')

    def mark_missing_under_root(self, root: Path, seen_photo_ids: Iterable[str], missing_since: str | None = None) -> list[str]:
        """Mark unseen photos under *root* as missing."""

        normalized_root = normalize_path(root)
        seen = set(seen_photo_ids)
        missing_since = missing_since or self.utc_now()
        rows = self._execute('SELECT photo_id, current_path FROM photos').fetchall()
        missing_photo_ids: list[str] = []
        for row in rows:
            photo_id = row['photo_id']
            if photo_id in seen:
                continue
            current_path = normalize_path(row['current_path'])
            if current_path != normalized_root and not current_path.is_relative_to(normalized_root):
                continue
            self._execute(
                'UPDATE photos SET missing_since = ? WHERE photo_id = ?',
                (missing_since, photo_id),
            )
            missing_photo_ids.append(photo_id)
            self.log_device.warning(f'Marked missing photo {photo_id} at {current_path}.')
        return missing_photo_ids

    def list_missing_photos(self) -> list[PhotoRecord]:
        """Return photos currently marked missing."""

        rows = self._execute('SELECT * FROM photos WHERE missing_since IS NOT NULL ORDER BY missing_since ASC').fetchall()
        return [self._row_to_photo(row) for row in rows if row is not None]

    def add_tag(self, photo_id: str, tag: str) -> None:
        """Add a manual tag to a photo."""

        created_at = self.utc_now()
        self._execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag,))
        tag_row = self._execute('SELECT id FROM tags WHERE name = ?', (tag,)).fetchone()
        if tag_row is None:
            raise StorageError(f'Unable to load tag row for {tag}.')
        self._execute(
            'INSERT OR IGNORE INTO photo_tags (photo_id, tag_id, created_at) VALUES (?, ?, ?)',
            (photo_id, tag_row['id'], created_at),
        )
        self.log_device.info(f'Added tag {tag} to photo {photo_id}.')

    def remove_tag(self, photo_id: str, tag: str) -> None:
        """Remove a manual tag from a photo."""

        self._execute(
            '''
            DELETE FROM photo_tags
            WHERE photo_id = ? AND tag_id IN (SELECT id FROM tags WHERE name = ?)
            ''',
            (photo_id, tag),
        )
        self.log_device.info(f'Removed tag {tag} from photo {photo_id}.')

    def list_tags(self, photo_id: str) -> list[str]:
        """List manual tags for a photo."""

        rows = self._execute(
            '''
            SELECT tags.name
            FROM tags
            INNER JOIN photo_tags ON photo_tags.tag_id = tags.id
            WHERE photo_tags.photo_id = ?
            ORDER BY tags.name ASC
            ''',
            (photo_id,),
        ).fetchall()
        return [row['name'] for row in rows]

    def find_photos_by_tag(self, tag: str) -> list[PhotoRecord]:
        """Return photo records with a given tag."""

        rows = self._execute(
            '''
            SELECT photos.*
            FROM photos
            INNER JOIN photo_tags ON photo_tags.photo_id = photos.photo_id
            INNER JOIN tags ON tags.id = photo_tags.tag_id
            WHERE tags.name = ?
            ORDER BY photos.current_path ASC
            ''',
            (tag,),
        ).fetchall()
        return [self._row_to_photo(row) for row in rows if row is not None]

    def create_analysis_run(self, analysis_run: AnalysisRun) -> AnalysisRun:
        """Persist an analysis run and return it with a run ID."""

        cursor = self._execute(
            '''
            INSERT INTO analysis_runs (
                plugin_name, plugin_version, model_name, model_version, target_path,
                started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                analysis_run.plugin_name,
                analysis_run.plugin_version,
                analysis_run.model_name,
                analysis_run.model_version,
                analysis_run.target_path,
                analysis_run.started_at,
                analysis_run.completed_at,
            ),
        )
        analysis_run.run_id = int(cursor.lastrowid)
        return analysis_run

    def store_analysis_result(self, analysis_run: AnalysisRun, result: AnalysisResult) -> None:
        """Store structured annotations from a plugin result."""

        if analysis_run.run_id is None:
            analysis_run = self.create_analysis_run(analysis_run)
        for annotation in result.annotations:
            region_json = None
            if annotation.region is not None:
                region_json = json.dumps(asdict(annotation.region))
            self._execute(
                '''
                INSERT INTO annotations (
                    run_id, photo_id, namespace, label, confidence, value_text,
                    region_json, plugin_name, plugin_version, model_name,
                    model_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    analysis_run.run_id,
                    result.photo_id,
                    annotation.namespace,
                    annotation.label,
                    annotation.confidence,
                    annotation.value,
                    region_json,
                    annotation.plugin_name or result.plugin_name,
                    annotation.plugin_version or result.plugin_version,
                    annotation.model_name or result.model_name,
                    annotation.model_version or result.model_version,
                    annotation.created_at or self.utc_now(),
                ),
            )
        self.log_device.info(f'Stored {len(result.annotations)} annotations for {result.photo_id}.')

    def list_annotations(self, photo_id: str) -> list[sqlite3.Row]:
        """Return stored annotation rows for *photo_id*."""

        return self._execute('SELECT * FROM annotations WHERE photo_id = ? ORDER BY id ASC', (photo_id,)).fetchall()

    def clear_scan_issues(self, issue_types: Iterable[ScanIssueType] | None = None) -> None:
        """Clear structured scan issues, optionally filtered by type."""

        if issue_types is None:
            self._execute('DELETE FROM scan_issues')
            return
        for issue_type in issue_types:
            self._execute('DELETE FROM scan_issues WHERE issue_type = ?', (issue_type.value,))

    def add_scan_issue(self, issue: ScanIssue) -> None:
        """Persist a structured scan issue."""

        self._execute(
            '''
            INSERT INTO scan_issues (
                issue_type, photo_id, related_photo_id, checksum, path, details_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                issue.issue_type.value,
                issue.photo_id,
                issue.related_photo_id,
                issue.checksum,
                str(issue.path) if issue.path is not None else None,
                json.dumps(issue.details, sort_keys=True),
                issue.created_at or self.utc_now(),
            ),
        )

    def list_scan_issues(self, issue_types: Iterable[ScanIssueType] | None = None) -> list[ScanIssue]:
        """Return structured scan issues."""

        rows = self._execute('SELECT * FROM scan_issues ORDER BY created_at ASC').fetchall()
        allowed_issue_types = None
        if issue_types is not None:
            allowed_issue_types = {issue_type.value for issue_type in issue_types}
        return [
            ScanIssue(
                issue_type=ScanIssueType(row['issue_type']),
                photo_id=row['photo_id'],
                related_photo_id=row['related_photo_id'],
                checksum=row['checksum'],
                path=Path(row['path']) if row['path'] else None,
                details=json.loads(row['details_json']),
                created_at=row['created_at'],
            )
            for row in rows
            if allowed_issue_types is None or row['issue_type'] in allowed_issue_types
        ]

    def refresh_duplicate_checksum_issues(self) -> list[ScanIssue]:
        """Refresh duplicate-checksum issues from the current photo table."""

        self.clear_scan_issues(issue_types=[ScanIssueType.DUPLICATE_CHECKSUM])
        rows = self._execute(
            '''
            SELECT checksum, COUNT(*) AS duplicate_count
            FROM photos
            GROUP BY checksum
            HAVING COUNT(*) > 1
            ORDER BY checksum ASC
            '''
        ).fetchall()
        issues: list[ScanIssue] = []
        for row in rows:
            checksum = row['checksum']
            photos = self._execute('SELECT photo_id, current_path FROM photos WHERE checksum = ? ORDER BY current_path ASC', (checksum,)).fetchall()
            for photo_row in photos:
                issue = ScanIssue(
                    issue_type=ScanIssueType.DUPLICATE_CHECKSUM,
                    photo_id=photo_row['photo_id'],
                    checksum=checksum,
                    path=Path(photo_row['current_path']),
                    details={
                        'duplicate_count': row['duplicate_count'],
                        'paths': [candidate['current_path'] for candidate in photos],
                    },
                )
                self.add_scan_issue(issue)
                issues.append(issue)
        if issues:
            self.log_device.warning(f'Flagged {len(issues)} duplicate-checksum issue records.')
        return issues
