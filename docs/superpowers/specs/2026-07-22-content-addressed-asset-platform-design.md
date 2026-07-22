# Content-Addressed Classroom Asset Platform Design

## Goal

Give the Custom GPT verified image ingestion and transformation capabilities
whose results remain usable after a tool job ends and after a classroom is
published. Assets must be discoverable through `studio_tools_v1`, addressable
through immutable learner URLs, and rejected at publication time when their
identity or bytes cannot be verified.

## Decisions

- Store normalized assets by SHA-256 under `CLASSROOM_DATA_ROOT/assets`.
- Use `a-<64 lowercase hex characters>` as the immutable `asset_id` and
  `sha256:<64 lowercase hex characters>` as `content_hash`.
- Accept explicit base64 uploads and artifacts from successful Studio tool
  jobs. Do not fetch arbitrary remote URLs.
- Initially accept still PNG, JPEG, and WebP images. Reject animation, SVG,
  mismatched MIME declarations, decompression bombs, excessive dimensions,
  excessive pixels, unsafe filenames, truncated images, and blank alt text.
- Normalize orientation and re-encode pixels without EXIF, comments, ICC, or
  other submitted metadata before hashing and storing them.
- Expose immutable bytes at `/api/classroom/v1/assets/{asset_id}` with an ETag,
  the verified media type, and a one-year immutable cache policy.
- Keep every produced image as both a persistent asset and a normal job
  artifact so the GPT can inspect or download it through the existing protocol.

## Components

### Asset repository

`AssetRepository` owns immutable bytes and a strict JSON metadata record. It
validates identifiers and paths, writes atomically, detects duplicates by full
digest, checks stored bytes on read, and never overwrites content with a
different digest. Metadata records include media type, extension, dimensions,
byte size, content hash, safe display filename, and creation time.

### `asset.ingest@1.0.0`

The author supplies exactly one source:

1. `content_base64` plus declared media type and filename; or
2. a successful `source_job_id` and `source_artifact_name` from the same Studio
   platform.

The adapter performs strict base64 decoding or verified artifact lookup, MIME
signature inspection, Pillow verification, bounded decode, EXIF orientation,
pixel normalization, metadata removal, deterministic output encoding, and a
second decode of the produced file. It stores the normalized image and returns
an `AssetReference`-compatible result plus a machine-readable validation
report. Reingesting the same normalized pixels returns the same ID and reports
`duplicate=true`.

### `asset.transform@1.0.0`

The author supplies an existing asset ID, target dimensions, `contain` or
`cover`, output format, quality, optional background color, and an explicit
upscaling policy. The adapter preserves aspect ratio, uses high-quality Lanczos
resampling, correctly composites alpha for JPEG, rejects impossible geometry,
revalidates the output, stores it as a new immutable asset, and reports the
source-to-output relation.

### Classroom integration

The package validator receives an asset resolver beside the existing teaching
model resolver. Every declared package asset must have a unique ID, canonical
learner URI, verified content hash, matching media type, and a corresponding
repository record. Every image content block must include `asset_id`, canonical
`uri`, meaningful `alt`, and a matching package asset declaration. Unregistered
or externally hosted image blocks are publication errors.

The learner runtime returns the package asset declarations needed by a module.
The existing renderer keeps using the canonical URI and receives no filesystem
path or credential.

## Limits

- Encoded upload: at most 12 MiB of base64 text and 8 MiB decoded bytes.
- Source dimensions: 16 to 6000 pixels per side and at most 20 million pixels.
- Transform output: 32 to 4096 pixels per side and at most 16 million pixels.
- Still images only; `n_frames` must equal one.
- Filenames are display metadata only and must reduce to a safe basename.
- No host paths, URL imports, SVG scripts, embedded files, or arbitrary image
  decoder options are accepted from the GPT.

## Failure handling

Argument and image failures terminate the tool job with a concise repair hint.
Repository corruption is never silently repaired: reads fail when size or hash
differs from metadata. Duplicate content is successful and idempotent. A
missing source job, unfinished source job, absent artifact, unsupported media
type, or source artifact hash mismatch is a hard failure.

## Verification

- Repository tests cover atomic storage, duplicate detection, path rejection,
  and corruption detection.
- Adapter tests cover upload and prior-job sources, MIME spoofing, invalid
  base64, oversized images, animation rejection, EXIF stripping, dimensions,
  transforms, alpha compositing, and no-upscale behavior.
- API tests cover discovery, scope enforcement, submit/poll/download, learner
  ETag/cache behavior, unknown IDs, and publication rejection for undeclared or
  tampered assets.
- Evidence generation runs both tools through the public Studio job protocol,
  downloads every artifact, opens the learner URL in real Chromium, and checks
  natural dimensions, nonblank pixels, console errors, failed requests, and
  absence of secrets or temporary paths.

## Deferred extensions

Video/audio ingestion, OCR, document extraction, remote imports, and generated
image providers require separate verified adapters. They will reuse the same
repository and publication contract rather than weakening this image boundary.
