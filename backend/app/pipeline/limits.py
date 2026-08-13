"""Fase 9 security pass: shared upload size limit.

Before this, no route enforced any file-size ceiling -- `UploadFile.read()`
loads the whole file into memory regardless, so an arbitrarily large upload
(OFX or CSV) could exhaust worker memory. Session-scoped, so the blast
radius is smaller than a shared resource, but there's no reason to leave
it unbounded.
"""

from __future__ import annotations

MAX_UPLOAD_FILE_BYTES = 10 * 1024 * 1024  # 10 MB per file
