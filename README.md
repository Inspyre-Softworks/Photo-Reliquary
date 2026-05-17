# Photo Reliquary

Preserve the identity of your photos, even when their filenames lie.

Taylor B. | Inspyre-Softworks

Photo Reliquary is a rename-resilient photo identity and tagging system for normal image files. It keeps tags, metadata, annotations, and history attached to the correct photo even after filenames and folder layouts change while the app is offline.

## Why this exists

Filename and path tracking are fragile. A photo can be renamed, copied, moved, or reorganized outside the app at any time. A watchdog-only design is not enough because the watcher can be offline, miss events, or observe incomplete file operations.

Photo Reliquary treats rescanning, metadata identity, database reconciliation, and checksum comparison as the source of truth.

## How stable photo identity works

Each imported photo receives a stable `photo_id` that is independent of its filename and path. During scanning, Photo Reliquary stores and reconciles:

- `photo_id`
- `current_path`
- `checksum`
- `checksum_algorithm`
- `checksum_tail`
- `size_bytes`
- `mtime_ns`
- `first_seen_at`
- `last_seen_at`
- `missing_since`
- `identity_storage_mode`

The checksum tail is only a human-friendly shorthand. It is never treated as unique.

## Storage model

Photo Reliquary uses SQLite for rich local data such as:

- tracked photo records
- manual tags
- scan issues and duplicate flags
- analysis runs
- machine annotations

When embedded metadata is unsupported or unsafe, Photo Reliquary falls back to JSON sidecar files such as:

```text
photo.jpg.reliquary.json
```

Sidecars store at minimum:

- `photo_id`
- `checksum`
- `checksum_algorithm`
- `checksum_tail`
- `created_at`
- `updated_at`

## Metadata strategy

The initial embedded metadata handler is intentionally conservative. Its API is ready for future XMP and EXIF support, but current writes safely fall back to sidecars instead of risking destructive metadata edits.

## Plugins and analyzers

Photo Reliquary includes a first-class plugin registry for analyzer extensions. Plugins return structured `AnalysisResult` objects containing namespaced annotations, confidence scores, optional values, and optional regions. The built-in `nudenet-example` plugin demonstrates how a future NudeNet-style extension can fit into the system without requiring NudeNet to be installed.

Example namespaces include:

- `nudenet:example_detection`
- `vision:dominant_color`
- `ocr:text`
- `reliquary:duplicate_candidate`

## CLI examples

```bash
photo-reliquary scan ./photos
photo-reliquary tag add pr_xxxxx family
photo-reliquary tag remove pr_xxxxx family
photo-reliquary tag list pr_xxxxx
photo-reliquary find --tag family
photo-reliquary checksum-tail pr_xxxxx
photo-reliquary missing
photo-reliquary duplicates
photo-reliquary analyze ./photos --plugin nudenet-example
photo-reliquary plugins list
```

## Roadmap

Future work can extend this foundation with:

- real XMP and EXIF writing
- NudeNet integration packages such as `photo_reliquary_nudenet`
- perceptual hashing
- duplicate detection refinements
- image similarity search
- CSV, JSON, and XMP export
- optional file watcher support
- GUI or TUI front ends
