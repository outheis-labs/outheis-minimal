# Data Formats and Conventions

This document specifies the structure and format of data in outheis, enabling agents to make reliable assumptions about content.

---

## Core Principle: Data Locality

**User data exists only in two locations:**

| Location | Written by | Contains |
|----------|-----------|----------|
| `~/.outheis/human/` | outheis system, user via Web UI, manual edit | Configuration, insights, rules |
| `vault/` (external) | User | Knowledge, documents, assets |

No user data is stored anywhere else. Removing these directories erases all user traces.

---

## Directory Structure

### System Directory

```
~/.outheis/                      # System directory
├── agents/                      # Agent implementations
├── transport/                   # Transport daemon
├── dispatcher/                  # Dispatcher
├── web/                         # Web UI (localhost-only)
└── human/                       # ALL user-specific data
    ├── config.json              # User configuration
    ├── insights.jsonl           # Pattern agent output
    ├── rules/                   # Agenda agent rules
    │   └── priorities.md
    ├── messages.jsonl           # Message queue (append-only)
    ├── archive/                 # Cold storage for old conversations
    │   ├── messages-2025-01.jsonl
    │   └── ...
    ├── index.jsonl              # Search index (across all vaults)
    ├── tag-weights.jsonl        # Learned tag importance
    ├── cache/                   # Cached data
    │   └── agenda/              # Previous versions for diff
    │       ├── Daily.md.prev
    │       ├── Inbox.md.prev
    │       └── Exchange.md.prev
    ├── imports/                 # Imported external data
    │   ├── calendar/
    │   │   └── 2025-03-27.jsonl
    │   ├── email/
    │   │   └── inbox.jsonl
    │   ├── tasks/
    │   └── contacts/
    └── vault/                   # Minimal starter vault
```

### Vault (External, User-Managed)

Vaults can be anywhere on the filesystem. Multiple vaults are supported.

```
~/Documents/MyVault/             # Example: user's primary vault
├── Agenda/                      # Special directory (required in primary vault)
│   ├── Daily.md
│   ├── Inbox.md
│   └── Exchange.md
├── notes/
│   └── project-alpha.md
├── projects/
│   └── project-alpha/
│       ├── README.md
│       └── assets/
│           └── diagram.png
└── archive/
    └── 2024/

~/Documents/Obsidian/            # Example: second vault
├── ...
```

### Configuration

```json
{
  "vault": [
    "~/Documents/MyVault",
    "~/Documents/Obsidian"
  ]
}
```

First vault in list is the **primary vault** — contains `Agenda/`.

---

## Vault Structure

### Conventions

| Rule | Description |
|------|-------------|
| `Agenda/` | Required in primary vault, special handling |
| User directories | Arbitrary structure, arbitrary depth |
| Directory names | May serve as organizational hints |
| Markdown files | Primary knowledge format, self-describing via tags |
| Other files | Assets, attachments, linked or loose |

### Philosophy

Following the principle of *prospective information architecture*:

- **Self-description**: Files carry their meaning via tags, not via position
- **Position as hint**: Directory structure provides context, not identity
- **Multiple access paths**: Tags enable retrieval from any perspective
- **Structure at query time**: Hierarchies are computed, not stored

---

## File Types

### Primary: Markdown (.md)

The primary knowledge format. Human-readable, machine-parseable, self-describing.

### Common Assets

Files that commonly appear alongside or linked from Markdown:

| Category | Extensions | Handling |
|----------|------------|----------|
| Documents | `.docx`, `.xlsx`, `.pptx`, `.pdf` | Index metadata, extract text where possible |
| Archives | `.zip`, `.tgz`, `.tar.gz`, `.tar`, `.7z` | Index as container, list contents |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp` | Index metadata, OCR if configured |
| Code | `.py`, `.js`, `.ts`, `.sh`, `.json`, `.yaml` | Index as text |
| Repositories | `.git/` (directory) | Recognize as git repo, index metadata |
| Data | `.csv`, `.tsv`, `.jsonl` | Index as structured data |

### Relationship Patterns

Files relate to each other in several ways:

| Pattern | Description |
|---------|-------------|
| **Embedded** | Image/asset referenced in Markdown (`![](path)`) |
| **Linked** | Document referenced via path or wiki-link (`[[name]]`) |
| **Sibling** | Related files in same directory |
| **Loose** | Files without explicit links (discoverable via search) |

---

## Markdown Format

### Frontmatter

Optional YAML frontmatter for explicit metadata:

```markdown
---
title: Project Alpha Notes
created: 2025-01-15
modified: 2025-03-27
tags: [project/alpha, important]
---

# Project Alpha Notes

Content here...
```

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Display title |
| `created` | date | Creation date (ISO 8601) |
| `modified` | date | Last modification (ISO 8601) |
| `tags` | array | Semantic tags |

If frontmatter is absent, agents derive metadata from:
- Title: First `# heading` or filename
- Created/Modified: Filesystem timestamps
- Tags: Inline tags in content

### Inline Tags

Tags can appear anywhere in content:

```markdown
This is an #important note about #project/alpha.

Meeting scheduled for tomorrow #deadline #priority-high.
```

### Tag Formats

| Format | Example | Meaning |
|--------|---------|---------|
| Single | `#important` | Simple flag |
| Key-value | `#priority-high` | Attribute with value |
| Hierarchical | `#project/alpha` | Nested namespace |
| Deep nesting | `#company/acme/sales` | Multiple levels |

### Tag Normalization

Agents normalize tags for indexing:

```
#Important     → important
#Priority-High → priority-high
#Project/Alpha → project/alpha
```

Rules:
- Lowercase
- Preserve hyphens
- Preserve hierarchy separators (`/`)
- Strip leading `#`

### Links

Wiki-style links for internal references:

```markdown
See [[meeting-notes]] for details.
Related: [[projects/alpha/README]]
```

Standard Markdown links for external references:

```markdown
Based on [this paper](https://example.com/paper.pdf).
```

---

## Imported Data

External data (calendar, email, etc.) is imported by the Action agent into `~/.outheis/human/imports/`. This data is canonical—structured representations of external sources.

### Directory Structure

```
~/.outheis/human/imports/
├── calendar/
│   ├── 2025-03-27.jsonl
│   └── recurring.jsonl
├── email/
│   ├── inbox.jsonl
│   └── sent.jsonl
├── tasks/
│   └── tasks.jsonl
└── contacts/
    └── contacts.jsonl
```

### Calendar Events

```json
{
  "id": "evt_abc123",
  "source": "google_calendar",
  "title": "Team Meeting",
  "start": "2025-03-27T10:00:00Z",
  "end": "2025-03-27T11:00:00Z",
  "location": "Room 3B",
  "description": "Weekly sync",
  "attendees": ["alice@example.com", "bob@example.com"],
  "recurring": false,
  "imported_at": "2025-03-27T08:00:00Z"
}
```

### Email

```json
{
  "id": "msg_xyz789",
  "source": "gmail",
  "from": {"name": "Alice", "email": "alice@example.com"},
  "to": [{"name": "User", "email": "user@example.com"}],
  "cc": [],
  "subject": "Project Update",
  "body_text": "Plain text body...",
  "date": "2025-03-27T09:15:00Z",
  "thread_id": "thread_123",
  "labels": ["inbox", "important"],
  "attachments": [
    {"filename": "report.pdf", "mime_type": "application/pdf", "size": 102400}
  ],
  "imported_at": "2025-03-27T10:00:00Z"
}
```

### Tasks

```json
{
  "id": "task_456",
  "source": "todoist",
  "title": "Review proposal",
  "description": "Review and comment on Q2 proposal",
  "due": "2025-03-28T17:00:00Z",
  "priority": 2,
  "status": "pending",
  "project": "Work",
  "labels": ["review", "q2"],
  "imported_at": "2025-03-27T08:00:00Z"
}
```

### Contacts

```json
{
  "id": "contact_789",
  "source": "google_contacts",
  "name": "Alice Smith",
  "email": ["alice@example.com", "alice.smith@work.com"],
  "phone": ["+1-555-123-4567"],
  "organization": "Acme Corp",
  "notes": "Met at conference 2024",
  "imported_at": "2025-03-27T08:00:00Z"
}
```

---

## Index

The Data agent maintains a search index at `~/.outheis/human/index.jsonl`:

```json
{
  "vault": "~/Documents/MyVault",
  "path": "notes/project-alpha.md",
  "type": "markdown",
  "title": "Project Alpha Notes",
  "tags": ["project/alpha", "important"],
  "links_to": ["meeting-notes.md", "assets/diagram.png"],
  "linked_from": ["README.md"],
  "modified": "2025-03-27T10:00:00Z",
  "accessed_at": "2025-03-27T14:00:00Z",
  "access_count": 12,
  "checksum": "sha256:abc123...",
  "indexed_at": "2025-03-27T10:05:00Z"
}
```

The index spans all configured vaults. Each entry includes the `vault` field.

---

## Human Directory

### Structure

```
~/.outheis/human/
├── config.json                  # User configuration
├── insights.jsonl               # Pattern agent output
├── rules/                       # Agenda agent rules
│   └── priorities.md
└── vault/                       # Minimal starter vault
```

### Write Access

| Component | Can Write |
|-----------|-----------|
| outheis system | config.json, insights.jsonl |
| Pattern agent | insights.jsonl |
| User (Web UI) | config.json, rules/ |
| User (manual) | Any file |
| Other agents | **Never** (read-only) |

### config.json

User configuration:

```json
{
  "name": "Markus",
  "language": "en",
  "timezone": "Europe/Berlin",
  "vault": [
    "~/Documents/MyVault",
    "~/Documents/Obsidian"
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | User's display name |
| `language` | string | Preferred language (ISO 639-1) |
| `timezone` | string | IANA timezone |
| `vault` | array | Paths to vaults (first = primary) |

### insights.jsonl

Pattern agent writes observations:

```json
{
  "v": 1,
  "id": "ins_20251115_001",
  "type": "strategy",
  "domain": "communication",
  "insight": "When formatting for Signal, use emoji headers instead of markdown",
  "confidence": 0.8,
  "evidence_count": 5,
  "source_sessions": ["sess_001", "sess_003", "sess_007"],
  "created_at": "2025-11-15T04:12:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `strategy`, `preference`, `pattern`, `capability` |
| `domain` | string | Area of applicability |
| `confidence` | float | 0.0–1.0, increases with evidence |
| `evidence_count` | int | Number of supporting instances |
| `source_sessions` | array | Traceability to conversations |

### session_notes.jsonl

Temporary learning notes, reviewed by Pattern agent during scheduled runs:

```json
{
  "v": 1,
  "id": "note_20251115_001",
  "session_id": "sess_007",
  "agent": "relay",
  "problem": "User asked for table formatting in Signal",
  "solution": "Replace markdown tables with emoji-separated rows",
  "context": {
    "channel": "signal",
    "user_feedback": "positive"
  },
  "created_at": "2025-11-15T10:30:00Z",
  "reviewed": false
}
```

Session notes are:
- Written by any agent when user helps solve a problem
- Read by Pattern agent during nightly run
- Marked `reviewed: true` after processing
- Periodically cleaned (reviewed notes older than 30 days)

Pattern agent decides: generalize to insight, or leave as specific instance in archive.

### Agenda Rules

Markdown files in `human/rules/` define user preferences:

```markdown
# Priorities

## Work vs Personal
- Work appointments take priority over personal, except:
  - Family events always take priority
  - Health appointments always take priority

## Time Blocks
- Monday mornings: no meetings before 10:00
- Friday afternoons: no meetings after 15:00

## Notifications
- Deadline < 3 days: always remind
- Emails from boss: always show immediately
```

---

## Text Extraction

For non-Markdown files, agents extract text where possible:

| Type | Extraction Method |
|------|-------------------|
| PDF | `pdftotext`, `pymupdf`, or similar |
| DOCX/XLSX/PPTX | `python-docx`, `openpyxl`, `python-pptx` |
| Images | OCR (optional, configurable) |
| Archives | List contents, extract text from contained files |
| Code | Treat as plain text |

Extracted text is stored in the index, not as separate files.

---

## Binary Files

Binary files (images, PDFs, Office documents) are:

1. **Indexed** by metadata (size, type, modification date)
2. **Text-extracted** where possible
3. **Linked** via references in Markdown
4. **Not modified** by outheis (read-only from agent perspective)

---

## Git Repositories

If a directory contains `.git/`:

1. **Recognized** as a git repository
2. **Indexed** by metadata (remotes, branches, recent commits)
3. **Not modified** by outheis agents
4. **Action agent** may execute git commands if instructed

---

## Timestamps

All timestamps use ISO 8601 format in UTC:

```
2025-03-27T10:00:00Z
```

Agents convert to local timezone for display based on `human/config.json` timezone setting.

---

## File Naming

### Conventions

| Type | Convention | Example |
|------|------------|---------|
| Notes | lowercase, hyphens | `project-alpha-notes.md` |
| Imports | date or type prefix | `2025-03-27.jsonl` |
| System | descriptive | `index.jsonl` |

### Forbidden Characters

Filenames must not contain:
- `/` `\` `:` `*` `?` `"` `<` `>` `|`
- Leading/trailing spaces
- Leading `.` in user files (reserved for system)

---

## Encoding

All text files use UTF-8 encoding without BOM.

---

## Summary

| Data Type | Location | Format | Written By |
|-----------|----------|--------|------------|
| User notes | `vault/` | Markdown | User |
| User assets | `vault/` | Various | User |
| Search index | `~/.outheis/human/index.jsonl` | JSONL | Data agent |
| Tag weights | `~/.outheis/human/tag-weights.jsonl` | JSONL | Pattern agent |
| Imported data | `~/.outheis/human/imports/` | JSONL | Action agent |
| Message queue | `~/.outheis/human/messages.jsonl` | JSONL | All agents |
| Archive | `~/.outheis/human/archive/` | JSONL | Dispatcher |
| User config | `~/.outheis/human/config.json` | JSON | System, User |
| Insights | `~/.outheis/human/insights.jsonl` | JSONL | Pattern agent |
| Agenda rules | `~/.outheis/human/rules/` | Markdown | User |

---

## Schema Versioning

### The Problem

Data structures evolve. Messages, insights, and other formats will change over time. Without versioning:

- Old data becomes unreadable after upgrades
- Mixed versions in same file cause parsing errors
- No migration path for existing data

### Version Field

Every record in outheis-managed JSONL files carries a version:

```json
{"v": 1, "id": "msg_001", "from": {"agent": "zeno"}, ...}
{"v": 1, "id": "msg_002", "from": {"agent": "cato"}, ...}
{"v": 2, "id": "msg_003", "from": {"agent": "zeno"}, "priority": "high", ...}
```

| Field | Type | Meaning |
|-------|------|---------|
| `v` | integer | Schema version of this record |

Short field name (`v` not `version`) because JSONL should be compact.

### Version Authority

The schema version is defined in `core/schema.py`:

```python
# core/schema.py — single source of truth

MESSAGES_VERSION = 2
INSIGHTS_VERSION = 1
CONFIG_VERSION = 1

def write_message(msg):
    msg["v"] = MESSAGES_VERSION
    return json.dumps(msg)
```

All agents import this module. No agent writes JSON directly.

### Reading with Version Check

```python
def read_message(line):
    msg = json.loads(line)
    version = msg.get("v", 0)  # v0 = pre-versioning
    
    if version == MESSAGES_VERSION:
        return msg  # Hot path, no overhead
    
    if version > MESSAGES_VERSION:
        raise UnsupportedVersion(
            f"Message v{version} requires newer outheis"
        )
    
    # Only old messages go through migration
    return migrate_message(msg, from_version=version)
```

**Performance:** 99% of messages match current version → single integer comparison, no overhead.

### Migration Logic

Migration is stepwise (v0 → v1 → v2), located in `core/schema.py`:

```python
def migrate_message(msg, from_version):
    """Stepwise migration: v0 → v1 → v2 → ..."""
    
    if from_version < 1:
        # v0 → v1: "from" was string, now object
        if isinstance(msg.get("from"), str):
            msg["from"] = {"agent": msg["from"]}
        msg["v"] = 1
        from_version = 1
    
    if from_version < 2:
        # v1 → v2: New field "priority" with default
        msg.setdefault("priority", "normal")
        msg["v"] = 2
        from_version = 2
    
    return msg
```

| Principle | Reason |
|-----------|--------|
| Stepwise (v0→v1→v2) | Each step isolated, testable |
| Lossless | Old data remains fully readable |
| Read-time migration | Original file unchanged |
| Write always current | Never create old versions |

### Migration CLI

```bash
# Scan for outdated records
outheis migrate --scan

> Found 47 messages at v1 (current: v2)
> Found 12 insights at v0 (current: v1)
> 
> Run 'outheis migrate --apply' to convert

# Apply migration
outheis migrate --apply

> Migrating messages.jsonl: 47 entries v1 → v2
> Migrating archive/messages-2025-01.jsonl: 128 entries v1 → v2
> Migrating insights.jsonl: 12 entries v0 → v1
> Done. Backup in human/.migrate-backup/2025-11-15T10:00:00/

# Quiet mode for automation
outheis migrate --apply --quiet
```

### Automatic Migration

Optional: run migration in nightly batch with Pattern agent.

```json
{
  "system": {
    "auto_migrate": true,
    "migrate_schedule": "04:00"
  }
}
```

### Version History

| File | Current | Changes |
|------|---------|---------|
| messages.jsonl | v1 | Initial |
| insights.jsonl | v1 | Initial |
| config.json | v1 | Initial |
| tag-weights.jsonl | v1 | Initial |
| index.jsonl | v1 | Initial |

*Updated with each schema change.*

---

## Theoretical Background

The vault architecture implements principles of *prospective information architecture*:

- **Self-describing objects**: Files carry meaning via tags, not position
- **Multiple relationierung**: Tags and links enable multiple access paths
- **Structure at query time**: Hierarchies are computed, not stored
- **Plaintext as foundation**: Universal readability, long-term stability

See: [Temporalization of Order](https://github.com/outheis-labs/research-base/blob/main/temporalization-of-order/temporalization-of-order.md) for theoretical foundations.

---

## Edge Cases

### Symlinks

| Type | Handling |
|------|----------|
| Symlink within vault | Follow, index target |
| Symlink pointing outside vault | **Do not follow**, log as error |

Rationale: Symlinks outside vault could leak data or bypass access control.

### Hidden Files

Files and directories starting with `.` are ignored, except:

| Path | Handling |
|------|----------|
| `.git/` | Recognized as repository metadata |
| All other `.*` | Ignored (not indexed, not processed) |

This includes `.obsidian/`, `.DS_Store`, `.gitignore`, etc.

### Large Files

| Size | Handling |
|------|----------|
| < 50 MB | Full text extraction |
| 50 MB - 200 MB | Extract first/last pages, metadata only |
| > 200 MB | Metadata only, log warning |

Thresholds are configurable.

### Encoding Issues

If a file is not valid UTF-8:

1. Attempt detection (ISO-8859-1, Windows-1252, etc.)
2. If conversion succeeds: index converted text
3. If conversion fails: index metadata only, **notify user**

Notification path: Data agent → Dispatcher → Agenda agent (Personal Mode) or Relay (Domain Expert Mode) → User

---

## Domain Expert Mode: Admin Role

In Domain Expert Mode, the `human/` directory serves a different purpose:

| Aspect | Personal Mode | Domain Expert Mode |
|--------|---------------|-------------------|
| `human/` represents | Single user | System administrator |
| Agenda agent | Active (personal secretary) | Disabled |
| Pattern agent | Reflects on user behavior | Reflects on domain knowledge |
| Config access | User via Web UI | Admin via Web UI |
| Rules | User preferences | System policies |

The admin role in Domain Expert Mode:

- Configures agents, models, routing
- Defines domain-specific rules
- Monitors system health
- Does **not** receive personal filtering (no Agenda)

Multiple end-users interact via Transport, but only the admin configures `human/`.

---

## Agenda Directory

The primary vault contains a special `Agenda/` directory that serves as the structured interface between user and system.

### Structure

```
vault/Agenda/
├── Daily.md
├── Inbox.md
└── Exchange.md
```

Three files, no subdirectories.

### Purpose

| File | Direction | Purpose |
|------|-----------|---------|
| `Daily.md` | Bidirectional | Today: appointments, tasks, notes |
| `Inbox.md` | User → System | Quick input, unstructured thoughts |
| `Exchange.md` | System ↔ User | Questions, clarifications, learning |

### Daily.md

The current day. Agenda agent maintains structure, user adds content.

```markdown
# 2025-03-27

## Appointments
- 09:00 Standup
- 14:00 Workshop

## Focus
- [ ] Finish report #deadline
- [ ] Review proposal

## Notes

```

### Inbox.md

Quick capture. User writes, system processes.

```markdown
meeting with X next week, important

remember to call Y about the contract

#idea redesign the onboarding flow
```

Agenda agent reads, classifies, routes to appropriate agents.

### Exchange.md

Asynchronous dialogue. System asks, user answers when convenient. No pressure.

```markdown
# Open

## Scheduling conflict
> Friday 28.03 you have:
> - 10:00 Team meeting
> - 10:00 Dentist
>
> Which takes priority?

Your answer:


---

# Resolved

## Tag meaning
> You use #wip and #in-progress. Synonyms?

Your answer: Yes, merge to #wip

Learned: #in-progress → #wip
```

### Special Handling

The `Agenda/` directory receives special treatment:

| Aspect | Handling |
|--------|----------|
| Change detection | Checksum + diff (cached previous version) |
| Ownership | Agenda agent |
| Indexing | Higher priority, always current |
| Diff analysis | Comments, additions, deletions tracked |

This enables the Agenda agent to understand *what* changed, not just *that* something changed.

### Cache Location

```
~/.outheis/human/cache/agenda/
├── Daily.md.prev
├── Inbox.md.prev
└── Exchange.md.prev
```

Previous versions are cached in the system directory to compute diffs.

---

## Access Strategies

Without a database, fast access requires smart strategies on top of plaintext.

### Index as Primary Lookup

The index (`~/.outheis/human/index.jsonl`) serves as the first point of access. File content is only loaded when needed.

```
Query
  │
  ▼
Index (fast, in-memory)
  │
  ├── Filter by tags, type, date
  ├── Rank candidates
  │
  ▼
Top-N file access (lazy load)
```

### Ranking Heuristics

Candidates from index are ranked by multiple signals:

| Signal | Weight | Rationale |
|--------|--------|-----------|
| **Recency** | High | Recently modified = likely relevant |
| **Access frequency** | Medium | Often accessed = important |
| **Link density** | Medium | Many backlinks = central node |
| **Tag match** | High | Direct tag match = strong signal |
| **Tag weight** | Medium | Learned tag importance |

### Tag Learning

Pattern agent analyzes tag usage and learns weights:

```json
{
  "tag": "project/alpha",
  "weight": 0.85,
  "access_count": 47,
  "co_occurs_with": ["deadline", "important"],
  "last_accessed": "2025-03-27T10:00:00Z"
}
```

Stored in `~/.outheis/human/tag-weights.jsonl`.

Weights are updated based on:
- Access frequency (tag appears in accessed files)
- Co-occurrence with successful searches
- Implicit feedback (was result used?)

### Full-Text Search

For content not captured in index:

| Approach | Use Case |
|----------|----------|
| Grep + cache | Simple substring search |
| Inverted index | Frequent full-text queries |
| Embedding search | Semantic similarity (optional, local) |

Implementation choice depends on vault size and hardware.

### Index Updates

| Trigger | Action |
|---------|--------|
| Filewatch on vault | Detect changes |
| Checksum mismatch | Re-index file |
| Periodic sweep | Catch missed changes |

Filewatch uses `inotify` (Linux) or `kqueue` (macOS/BSD) — event-driven, no polling.

### Cold Storage Access

For archived conversations (`~/.outheis/human/archive/messages-*.jsonl`):

```
Query about old conversation
  │
  ▼
Data agent identifies relevant archive
  │
  ▼
Load archive file (slower)
  │
  ▼
Search within archive
  │
  ▼
Return results, unload archive
```

No permanent memory impact. Load on demand, release after use.
