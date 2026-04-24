import mimetypes
from pathlib import Path

MIME_OVERRIDES = {
    ".apk":  "application/vnd.android.package-archive",
    ".ipa":  "application/octet-stream",
    ".zip":  "application/zip",
    ".tar":  "application/x-tar",
    ".gz":   "application/gzip",
    ".bz2":  "application/x-bzip2",
    ".xz":   "application/x-xz",
    ".7z":   "application/x-7z-compressed",
    ".rar":  "application/vnd.rar",
    ".pdf":  "application/pdf",
    ".mp4":  "video/mp4",
    ".mkv":  "video/x-matroska",
    ".avi":  "video/x-msvideo",
    ".mov":  "video/quicktime",
    ".mp3":  "audio/mpeg",
    ".wav":  "audio/wav",
    ".flac": "audio/flac",
    ".ogg":  "audio/ogg",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".svg":  "image/svg+xml",
    ".exe":  "application/octet-stream",
    ".dmg":  "application/octet-stream",
    ".deb":  "application/vnd.debian.binary-package",
    ".rpm":  "application/x-rpm",
}


def get_mimetype(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in MIME_OVERRIDES:
        return MIME_OVERRIDES[ext]
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"
