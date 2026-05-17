"""Directory scanning and reconciliation.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from photo_reliquary.config import PhotoReliquaryConfig
from photo_reliquary.identity import PhotoIdentityService
from photo_reliquary.logging_utils import ReliquaryLoggable
from photo_reliquary.metadata import EmbeddedMetadataHandler, MetadataCoordinator, SidecarMetadataHandler
from photo_reliquary.models import IdentityStorageMode, PhotoMetadata, PhotoRecord, ScanIssue, ScanIssueType, ScanSummary
from photo_reliquary.storage.sqlite_store import SQLitePhotoStore
from photo_reliquary.utils.hashing import calculate_checksum, checksum_tail
from photo_reliquary.utils.paths import iter_supported_files, normalize_path


class PhotoScanner(ReliquaryLoggable):
    """Scan image files and reconcile them against metadata and SQLite storage."""

    def __init__(self, store: SQLitePhotoStore, config: PhotoReliquaryConfig | None = None) -> None:
        super().__init__()
        self.store = store
        self.config = config or PhotoReliquaryConfig(database_path=store.database_path)
        self.identity_service = PhotoIdentityService()
        self.metadata = MetadataCoordinator(
            [
                EmbeddedMetadataHandler(),
                SidecarMetadataHandler(sidecar_suffix=self.config.sidecar_suffix),
            ],
            allow_database_only_fallback=self.config.allow_database_only_fallback,
        )

    def _build_metadata(self, photo_record: PhotoRecord) -> PhotoMetadata:
        return PhotoMetadata(
            photo_id=photo_record.photo_id,
            checksum=photo_record.checksum,
            checksum_algorithm=photo_record.checksum_algorithm,
            checksum_tail=photo_record.checksum_tail,
            created_at=photo_record.first_seen_at,
            updated_at=photo_record.last_seen_at,
            identity_storage_mode=photo_record.identity_storage_mode,
        )

    def _record_from_file(self, path: Path, photo_id: str, first_seen_at: str, last_seen_at: str, mode: IdentityStorageMode) -> PhotoRecord:
        stat_result = path.stat()
        checksum = calculate_checksum(path, self.config.checksum_algorithm)
        return PhotoRecord(
            photo_id=photo_id,
            current_path=normalize_path(path),
            checksum=checksum,
            checksum_algorithm=self.config.checksum_algorithm,
            checksum_tail=checksum_tail(checksum),
            size_bytes=stat_result.st_size,
            mtime_ns=stat_result.st_mtime_ns,
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
            missing_since=None,
            identity_storage_mode=mode,
        )

    def _reconcile_path(self, photo: PhotoRecord, path: Path, seen_at: str) -> PhotoRecord:
        updated = self._record_from_file(
            path=path,
            photo_id=photo.photo_id,
            first_seen_at=photo.first_seen_at,
            last_seen_at=seen_at,
            mode=photo.identity_storage_mode,
        )
        storage_mode = self.metadata.write_identity(path, self._build_metadata(updated))
        stored = self.store.upsert_photo(replace(updated, identity_storage_mode=storage_mode))
        self.log_device.info(f'Reconciled photo {stored.photo_id} to {stored.current_path}.')
        return stored

    def _import_new_photo(self, path: Path, seen_at: str) -> PhotoRecord:
        generated = self.identity_service.create_photo_identity()
        provisional = self._record_from_file(
            path=path,
            photo_id=generated.photo_id,
            first_seen_at=seen_at,
            last_seen_at=seen_at,
            mode=IdentityStorageMode.DATABASE,
        )
        storage_mode = self.metadata.write_identity(path, self._build_metadata(provisional))
        photo = replace(provisional, identity_storage_mode=storage_mode)
        stored = self.store.upsert_photo(photo)
        self.log_device.info(f'Imported photo {stored.photo_id} from {stored.current_path}.')
        return stored

    def scan(self, path: Path | str) -> ScanSummary:
        """Scan a file or directory for supported image files."""

        target = normalize_path(path)
        summary = ScanSummary()
        seen_photo_ids: list[str] = []
        self.store.clear_scan_issues(issue_types=[ScanIssueType.DUPLICATE_PHOTO_ID, ScanIssueType.DUPLICATE_CHECKSUM])
        self.log_device.info(f'Starting scan for {target}.')
        for file_path in iter_supported_files(target, self.config.supported_suffixes):
            summary.scanned_paths.append(file_path)
            seen_at = self.store.utc_now()
            metadata = self.metadata.read_identity(file_path)
            checksum = calculate_checksum(file_path, self.config.checksum_algorithm)
            existing_by_checksum = self.store.get_photo_by_checksum(checksum)
            if metadata is not None:
                existing_by_id = self.store.get_photo_by_id(metadata.photo_id)
                if existing_by_id is not None and existing_by_id.checksum != checksum:
                    issue = ScanIssue(
                        issue_type=ScanIssueType.DUPLICATE_PHOTO_ID,
                        photo_id=metadata.photo_id,
                        related_photo_id=existing_by_checksum.photo_id if existing_by_checksum else None,
                        checksum=checksum,
                        path=file_path,
                        details={
                            'message': 'A file declared an existing photo_id but its checksum did not match the stored record.',
                            'stored_checksum': existing_by_id.checksum,
                            'scanned_checksum': checksum,
                        },
                    )
                    self.store.add_scan_issue(issue)
                    summary.issues.append(issue)
                    self.log_device.warning(f'Duplicate photo ID conflict detected for {file_path}: {metadata.photo_id}.')
                elif existing_by_id is not None:
                    photo = self._reconcile_path(existing_by_id, file_path, seen_at)
                    summary.reconciled_photo_ids.append(photo.photo_id)
                    seen_photo_ids.append(photo.photo_id)
                    continue
                else:
                    stat_result = file_path.stat()
                    photo = PhotoRecord(
                        photo_id=metadata.photo_id,
                        current_path=normalize_path(file_path),
                        checksum=checksum,
                        checksum_algorithm=self.config.checksum_algorithm,
                        checksum_tail=checksum_tail(checksum),
                        size_bytes=stat_result.st_size,
                        mtime_ns=stat_result.st_mtime_ns,
                        first_seen_at=metadata.created_at,
                        last_seen_at=seen_at,
                        missing_since=None,
                        identity_storage_mode=metadata.identity_storage_mode,
                    )
                    stored = self.store.upsert_photo(photo)
                    summary.imported_photo_ids.append(stored.photo_id)
                    seen_photo_ids.append(stored.photo_id)
                    continue
            if existing_by_checksum is not None:
                photo = self._reconcile_path(existing_by_checksum, file_path, seen_at)
                summary.reconciled_photo_ids.append(photo.photo_id)
                seen_photo_ids.append(photo.photo_id)
                continue
            stored = self._import_new_photo(file_path, seen_at)
            summary.imported_photo_ids.append(stored.photo_id)
            seen_photo_ids.append(stored.photo_id)
        if target.is_dir():
            summary.missing_photo_ids = self.store.mark_missing_under_root(target, seen_photo_ids, missing_since=self.store.utc_now())
        summary.issues.extend(self.store.refresh_duplicate_checksum_issues())
        self.log_device.info(
            'Completed scan for '
            f'{target}: {len(summary.imported_photo_ids)} imported, '
            f'{len(summary.reconciled_photo_ids)} reconciled, '
            f'{len(summary.missing_photo_ids)} missing.'
        )
        return summary
