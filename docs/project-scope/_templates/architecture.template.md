# Architecture

> Generated and amended ONLY by `architect-agent` (initial run or via `/amend-architecture`).
> No other agent may write to this file. `task-writer` and all `/implement` sessions
> must conform to this document. Conflicts are blocked, not silently resolved
> — see `/amend-architecture`.

**Version:** 1
**Last amended:** (date) — see `decisions.md` entry: (id), or "initial" if version 1

---

## Layering

> e.g. API → Application/Services → Domain → Infrastructure. Be concrete about
> what lives in each layer and the dependency direction.

## Module / Project Boundaries

> e.g. solution structure for a C# backend, package structure for a Vue frontend.

## Data Model

### Core Entities
> Name, key fields, relationships. Not a full schema — enough for task-writer
> to scope entity-related tasks correctly.

### Multi-Tenancy Implementation
> Concrete mechanism matching `constraints.md` (e.g. "TenantId column on every
> aggregate root, enforced via EF Core global query filter, never via app-layer
> filtering alone").

## API Conventions
- **Style:** (REST / GraphQL / etc.)
- **Versioning:**
- **Auth flow:** (e.g. token issuance, refresh, claims structure)
- **Error response shape:**
- **Naming conventions:**

## Frontend Conventions
- **State management:**
- **Component structure:**
- **Styling approach:** (SCSS conventions, BEM/utility/etc.)

## Integration Points
| Service/System | Purpose | Notes |
|---|---|---|
| | | |

## Folder / Naming Conventions
> So every coding session produces structurally consistent code without
> re-deciding "where does this go."

```
(example tree)
```

## Non-Functional Decisions With Structural Impact
> e.g. "must support offline kiosk mode" — note here AND ensure layering above
> actually accounts for it.

## Explicitly Rejected Approaches
> Alternatives considered and why they were not chosen. Prevents future
> coding/QA sessions from "fixing" something back to a rejected pattern.
-
