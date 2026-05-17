from __future__ import annotations

import importlib
import sys
from pathlib import Path

import photo_reliquary.logging_utils as logging_utils
from photo_reliquary.analysis.models import AnalysisRun
from photo_reliquary.config import PhotoReliquaryConfig
from photo_reliquary.identity import generate_photo_id
from photo_reliquary.plugins.registry import PluginRegistry
from photo_reliquary.scanner import PhotoScanner
from photo_reliquary.storage.sqlite_store import SQLitePhotoStore
from photo_reliquary.tags.manager import TagManager
from photo_reliquary.utils.hashing import calculate_checksum, checksum_tail


def create_test_photo(path: Path, content: bytes = b'fake-image-bytes') -> Path:
    path.write_bytes(content)
    return path


def build_store(tmp_path: Path) -> SQLitePhotoStore:
    return SQLitePhotoStore(tmp_path / 'photo-reliquary.db')


def test_generate_photo_id() -> None:
    photo_id = generate_photo_id()
    assert photo_id.startswith('pr_')
    assert len(photo_id) > 10


def test_import_does_not_initialize_logging(monkeypatch) -> None:
    calls: list[str] = []

    def fake_start_logger() -> None:
        calls.append('called')

    monkeypatch.setattr(logging_utils, 'start_logger', fake_start_logger)
    sys.modules.pop('photo_reliquary', None)
    package = importlib.import_module('photo_reliquary')

    assert calls == []
    assert hasattr(package, 'init_logging')


def test_init_logging_is_explicit(monkeypatch) -> None:
    calls: list[str] = []

    def fake_start_logger() -> None:
        calls.append('called')

    monkeypatch.setattr(logging_utils, 'start_logger', fake_start_logger)

    logging_utils.init_logging()

    assert calls == ['called']


def test_checksum_and_tail(tmp_path: Path) -> None:
    photo_path = create_test_photo(tmp_path / 'sample.jpg', b'abc123')
    checksum = calculate_checksum(photo_path)
    assert len(checksum) == 64
    assert checksum_tail(checksum) == checksum[-5:]


def test_scan_adds_photo_to_database(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    scanner = PhotoScanner(store, PhotoReliquaryConfig(database_path=store.database_path))
    photo_path = create_test_photo(tmp_path / 'import.jpg')

    summary = scanner.scan(tmp_path)

    assert summary.imported_photo_ids
    stored = store.get_photo_by_path(photo_path)
    assert stored is not None
    assert stored.checksum_tail == stored.checksum[-5:]
    assert photo_path.with_name('import.jpg.reliquary.json').exists()
    store.close()


def test_tags_survive_path_change_reconciliation(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    scanner = PhotoScanner(store, PhotoReliquaryConfig(database_path=store.database_path))
    tags = TagManager(store)
    original = create_test_photo(tmp_path / 'original.jpg', b'rename-me')

    first_summary = scanner.scan(tmp_path)
    photo_id = first_summary.imported_photo_ids[0]
    tags.add_tag(photo_id, 'family')

    renamed = tmp_path / 'renamed.jpg'
    original.rename(renamed)

    second_summary = scanner.scan(tmp_path)

    assert photo_id in second_summary.reconciled_photo_ids
    assert store.resolve_photo(photo_id).current_path == renamed
    assert tags.list_tags(photo_id) == ['family']
    store.close()


def test_missing_photos_are_marked(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    scanner = PhotoScanner(store, PhotoReliquaryConfig(database_path=store.database_path))
    photo_path = create_test_photo(tmp_path / 'missing.jpg', b'missing')

    summary = scanner.scan(tmp_path)
    photo_id = summary.imported_photo_ids[0]
    photo_path.unlink()

    scanner.scan(tmp_path)

    missing_photo = store.get_photo_by_id(photo_id)
    assert missing_photo is not None
    assert missing_photo.missing_since is not None
    store.close()


def test_add_remove_and_list_tags(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    scanner = PhotoScanner(store, PhotoReliquaryConfig(database_path=store.database_path))
    tags = TagManager(store)
    create_test_photo(tmp_path / 'tagged.jpg', b'tag-me')
    photo_id = scanner.scan(tmp_path).imported_photo_ids[0]

    tags.add_tag(photo_id, 'travel')
    assert tags.list_tags(photo_id) == ['travel']
    assert [photo.photo_id for photo in tags.find_photos_by_tag('travel')] == [photo_id]

    tags.remove_tag(photo_id, 'travel')
    assert tags.list_tags(photo_id) == []
    store.close()


def test_store_machine_annotations(tmp_path: Path) -> None:
    store = build_store(tmp_path)
    scanner = PhotoScanner(store, PhotoReliquaryConfig(database_path=store.database_path))
    registry = PluginRegistry()
    create_test_photo(tmp_path / 'analysis.jpg', b'analyze-me')
    photo_id = scanner.scan(tmp_path).imported_photo_ids[0]
    photo = store.get_photo_by_id(photo_id)
    assert photo is not None

    plugin = registry.get('nudenet-example')
    result = plugin.analyze(photo)
    run = AnalysisRun(
        plugin_name=plugin.name,
        plugin_version=plugin.version,
        model_name=result.model_name,
        model_version=result.model_version,
        target_path=str(tmp_path),
        started_at=store.utc_now(),
        completed_at=store.utc_now(),
    )
    store.store_analysis_result(run, result)

    rows = store.list_annotations(photo_id)
    assert len(rows) >= 1
    assert rows[0]['namespace'] == 'nudenet'
    store.close()


def test_builtin_plugin_loads() -> None:
    registry = PluginRegistry()
    plugin = registry.get('nudenet-example')
    assert plugin.name == 'nudenet-example'
    assert '.jpg' in plugin.supported_file_types


def test_list_photos_by_ids_uses_single_batch_lookup(tmp_path: Path, monkeypatch) -> None:
    store = build_store(tmp_path)
    scanner = PhotoScanner(store, PhotoReliquaryConfig(database_path=store.database_path))
    create_test_photo(tmp_path / 'one.jpg', b'one')
    create_test_photo(tmp_path / 'two.jpg', b'two')
    summary = scanner.scan(tmp_path)
    photo_ids = summary.imported_photo_ids

    executed_sql: list[str] = []
    original_execute = store._execute

    def capture_execute(sql: str, parameters=()):
        executed_sql.append(sql)
        return original_execute(sql, parameters)

    monkeypatch.setattr(store, '_execute', capture_execute)

    photos = store.list_photos_by_ids([photo_ids[1], 'missing-id', photo_ids[0], photo_ids[1]])

    assert [photo.photo_id for photo in photos] == [photo_ids[1], photo_ids[0], photo_ids[1]]
    assert len(executed_sql) == 1
    assert 'WHERE photo_id IN' in executed_sql[0]
    store.close()
