"""CLI for Photo Reliquary.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from pathlib import Path

import typer

from photo_reliquary.analysis.models import AnalysisRun
from photo_reliquary.config import PhotoReliquaryConfig
from photo_reliquary.logging_utils import init_logging
from photo_reliquary.plugins.registry import PluginRegistry
from photo_reliquary.scanner import PhotoScanner
from photo_reliquary.storage.sqlite_store import SQLitePhotoStore
from photo_reliquary.tags.manager import TagManager
from photo_reliquary.utils.hashing import checksum_tail as checksum_tail_value
from photo_reliquary.utils.paths import default_database_path

app = typer.Typer(help='Preserve the identity of your photos, even when their filenames lie.')
tag_app = typer.Typer(help='Manual tag commands.')
plugins_app = typer.Typer(help='Plugin inspection commands.')
app.add_typer(tag_app, name='tag')
app.add_typer(plugins_app, name='plugins')


def _build_services(database: Path | None = None) -> tuple[SQLitePhotoStore, PhotoScanner, TagManager, PluginRegistry]:
    db_path = database or default_database_path()
    config = PhotoReliquaryConfig(database_path=db_path)
    store = SQLitePhotoStore(config.database_path)
    scanner = PhotoScanner(store=store, config=config)
    tags = TagManager(store)
    registry = PluginRegistry()
    return store, scanner, tags, registry


@app.callback()
def main_callback() -> None:
    """Initialize logging for CLI operations."""

    init_logging()


@app.command()
def scan(path: Path, database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """Scan a file or directory and reconcile stored identity data."""

    store, scanner, _, _ = _build_services(database)
    try:
        summary = scanner.scan(path)
        typer.echo(
            f'Scanned {len(summary.scanned_paths)} file(s): '
            f'{len(summary.imported_photo_ids)} imported, '
            f'{len(summary.reconciled_photo_ids)} reconciled, '
            f'{len(summary.missing_photo_ids)} missing.'
        )
    finally:
        store.close()


@tag_app.command('add')
def tag_add(photo: str, tag: str, database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """Add a manual tag to a photo."""

    store, _, tags, _ = _build_services(database)
    try:
        tags.add_tag(photo, tag)
        typer.echo(f'Added tag {tag} to {photo}.')
    finally:
        store.close()


@tag_app.command('remove')
def tag_remove(photo: str, tag: str, database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """Remove a manual tag from a photo."""

    store, _, tags, _ = _build_services(database)
    try:
        tags.remove_tag(photo, tag)
        typer.echo(f'Removed tag {tag} from {photo}.')
    finally:
        store.close()


@tag_app.command('list')
def tag_list(photo: str, database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """List manual tags for a photo."""

    store, _, tags, _ = _build_services(database)
    try:
        for value in tags.list_tags(photo):
            typer.echo(value)
    finally:
        store.close()


@app.command()
def find(tag: str = typer.Option(..., '--tag', help='Manual tag to search for.'), database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """Find photos by manual tag."""

    store, _, tags, _ = _build_services(database)
    try:
        for photo in tags.find_photos_by_tag(tag):
            typer.echo(f'{photo.photo_id}\t{photo.current_path}')
    finally:
        store.close()


@app.command('checksum-tail')
def checksum_tail(photo: str, database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """Show the checksum tail for a photo."""

    store, _, _, _ = _build_services(database)
    try:
        record = store.resolve_photo(photo)
        typer.echo(checksum_tail_value(record.checksum))
    finally:
        store.close()


@app.command()
def missing(database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """List photos currently marked missing."""

    store, _, _, _ = _build_services(database)
    try:
        for photo in store.list_missing_photos():
            typer.echo(f'{photo.photo_id}\t{photo.current_path}\tmissing_since={photo.missing_since}')
    finally:
        store.close()


@app.command()
def duplicates(database: Path | None = typer.Option(None, '--database', help='SQLite database path.')) -> None:
    """List duplicate-related scan issues."""

    store, _, _, _ = _build_services(database)
    try:
        issues = store.list_scan_issues()
        for issue in issues:
            typer.echo(f'{issue.issue_type.value}\t{issue.photo_id}\t{issue.path}\t{issue.details}')
    finally:
        store.close()


@app.command()
def analyze(
    path: Path,
    plugin: str = typer.Option(..., '--plugin', help='Analyzer plugin name.'),
    database: Path | None = typer.Option(None, '--database', help='SQLite database path.'),
) -> None:
    """Run a registered analyzer plugin on scanned photos."""

    store, scanner, _, registry = _build_services(database)
    try:
        summary = scanner.scan(path)
        analyzer = registry.get(plugin)
        run = AnalysisRun(
            plugin_name=analyzer.name,
            plugin_version=analyzer.version,
            model_name='example-nudenet-model' if analyzer.name == 'nudenet-example' else None,
            model_version='0.1' if analyzer.name == 'nudenet-example' else None,
            target_path=str(path),
            started_at=store.utc_now(),
            completed_at=store.utc_now(),
        )
        analyzed = 0
        for photo in store.list_photos_by_ids(summary.touched_photo_ids):
            if analyzer.supports(photo.current_path):
                result = analyzer.analyze(photo)
                store.store_analysis_result(run, result)
                analyzed += 1
        typer.echo(f'Completed analysis with {plugin} for {analyzed} photo(s).')
    finally:
        store.close()


@plugins_app.command('list')
def plugins_list() -> None:
    """List available analyzer plugins."""

    registry = PluginRegistry()
    for plugin in registry.list_plugins():
        typer.echo(f'{plugin.name}\t{plugin.version}\t{" ".join(plugin.supported_file_types)}')


def main() -> None:
    """Console-script entry point."""

    app()


if __name__ == '__main__':
    main()
