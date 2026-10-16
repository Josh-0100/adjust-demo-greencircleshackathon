# Bolton Connect — integration contract

Bolton Connect runs **fully standalone** (`bolton_api.app:app`) and needs nothing
below to demonstrate end to end. This document describes the *optional* steps a
host CivicForge application would take to mount the module — and, per the project
brief, **none of them are applied automatically**. They are written here as
reviewable proposals so the parallel *Adjust* work and any shared entry points
are never touched without approval.

## What this module owns (and will not change)

| Concern | Owned by Bolton Connect |
|---|---|
| API routes | everything under `/api/bolton-connect` |
| Environment variables | everything prefixed `BOLTON_` |
| Database tables | `sessions`, `consent_events`, `cases`, `case_notes` (its own SQLite file) |
| Frontend assets | served from this module's `frontend/` directory |
| Data & prompts | this module's `data/` and `prompts/` directories |

It does **not** import, read, modify, or depend on the Adjust module, and it does
**not** register models with any host ORM or run any host migrations.

## Machine-readable manifest

`backend/bolton_api/plugin.py` exposes `MODULE_MANIFEST` and `describe()`:

```python
MODULE_MANIFEST = {
    "id": "bolton-connect",
    "name": "Bolton Connect",
    "api_prefix": "/api/bolton-connect",
    "env_prefix": "BOLTON_",
    "standalone_app": "bolton_api.app:app",
    "data_files": ["data/support_directory.json", "data/demo_residents.json"],
    "owns_tables": ["sessions", "consent_events", "cases", "case_notes"],
    "touches_shared_files": False,
    "depends_on_adjust_module": False,
}
```

## Mounting into a host app (one line, no shared-file edit)

The only supported bridge is a passive adapter. A host app chooses to call it:

```python
# in the host application's own composition root — NOT applied by this module
from bolton_api.plugin import mount_into

mount_into(host_app)   # adds the /api/bolton-connect router
```

`mount_into` only calls `app.include_router(...)`. It pulls in nothing from the
host and nothing from Adjust.

## Proposed shared changes (NOT applied)

If the host wants Bolton Connect registered in its module registry and surfaced
in its navigation, these are the changes a maintainer would make by hand. They
are listed for review only.

1. **Module registry** — add an entry pointing at the manifest/adapter, e.g.:

   ```python
   # host registry — proposal only
   from bolton_api.plugin import MODULE_MANIFEST, mount_into
   REGISTRY["bolton-connect"] = {"manifest": MODULE_MANIFEST, "mount": mount_into}
   ```

2. **Frontend navigation** — add a link to the resident portal
   (`/` when standalone, or the host's chosen mount path) and the adviser view
   (`/adviser.html`). No shared component needs to be rewritten; the views are
   self-contained static assets.

3. **Configuration** — provide the `BOLTON_` variables the deployment needs (all
   optional; defaults run offline). See the configuration table in `README.md`.

4. **Static asset serving** — when embedded, decide how the host serves this
   module's `frontend/` directory (the standalone app already mounts it at `/`).

## Deliberately out of scope

- No changes to shared application entry points are included in this module.
- No shared database migrations are added; the module manages its own store.
- No Adjust-module files are read or modified, and no dependency on Adjust is
  introduced.

Because every item above is manual and reviewable, integrating Bolton Connect
cannot collide with work happening in parallel elsewhere in the repository.
