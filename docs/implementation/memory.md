---
title: Memory
---

# Memory

*What outheis remembers about you — and how.*

## Memory vs. Vault

outheis maintains two separate knowledge stores:

| | Memory | Vault |
|---|--------|-------|
| **Purpose** | Meta-knowledge about you | Your work content |
| **Contains** | Facts, preferences, context | Documents, notes, projects |
| **Updated by** | Pattern agent, explicit markers | You directly |
| **Format** | Structured JSON | Markdown files |

**Memory** answers: *Who is this person? How do they want me to work?*

**Vault** answers: *What information do they have?*

## Memory Types

### user

Personal facts that don't change often.

Examples:
- "User is 35 years old"
- "Children: Leo (8) and Emma (5)"
- "Lives in Munich"
- "Works as a software engineer"

**Decay:** Permanent (until corrected)

### feedback

How you want outheis to behave.

Examples:
- "Prefers short, direct answers"
- "Respond in German unless asked otherwise"
- "Don't explain technical concepts — user is an expert"

**Decay:** Permanent (until corrected)

### context

What you're currently focused on.

Examples:
- "Working on Project Alpha mobile app"
- "Preparing for conference talk next week"
- "Learning Japanese"

**Decay:** 14 days by default (fades when no longer relevant)

## How Memory is Created

### Explicit Marker

Prefix any message with `!` to store it immediately:

```
! I am 35 years old
→ Stored in user memory

! please always give short answers
→ Stored in feedback memory

! I'm currently working on Project Alpha
→ Stored in context memory (14 day decay)
```

Classification happens automatically based on content.

### Pattern Agent Extraction

The Pattern agent (rumi) runs nightly at 04:00 and:

1. Reviews recent conversations
2. Extracts memorable information
3. Avoids duplicates with existing memory
4. Assigns confidence scores
5. Cleans up expired entries

You can trigger this manually: `outheis pattern`

## Temporal Awareness

Not everything should be remembered forever.

**Stored as permanent fact:**
- "User has two children"
- "Prefers formal communication"

**NOT stored (temporary state):**
- "User seems frustrated today"
- "User is tired"
- "User is stressed about deadline"

The Pattern agent is instructed to distinguish stable traits from temporary moods. Emotional states from a bad day won't become part of your permanent profile.

## Viewing and Editing Memory

### CLI

```bash
# View all memory
outheis memory

# Add entry manually
outheis memory --add "user:My birthday is March 15"

# Clear a type
outheis memory --clear context
```

### Display Format

```
Memory
----------------------------------------

[user] (3 entries)
  1. User is 35 years old
  2. Children: Leo (8), Emma (5) [!]
  3. Lives in Munich [90%]

[feedback] (1 entries)
  1. Prefers short answers [!]

[context] (2 entries)
  1. Working on Project Alpha [↓12d]
  2. Preparing conference talk [↓5d]
```

Markers:
- `[!]` — Explicitly stored via `!` marker
- `[90%]` — Confidence below 100%
- `[↓12d]` — Expires in 12 days

## Storage

```
~/.outheis/human/memory/
├── user.json
├── feedback.json
└── context.json
```

Each file contains timestamped entries with metadata:

```json
{
  "type": "user",
  "updated_at": "2025-03-28T14:30:00",
  "entries": [
    {
      "content": "User is 35 years old",
      "created_at": "2025-03-28T14:30:00",
      "updated_at": "2025-03-28T14:30:00",
      "confidence": 1.0,
      "source_count": 1,
      "decay_days": null,
      "is_explicit": true
    }
  ]
}
```

## Integration with Agents

Memory is injected into agent system prompts automatically:

```
# Memory

## About the user
- User is 35 years old
- Children: Leo (8), Emma (5)

## Working preferences
- Prefers short answers

## Current context
- Working on Project Alpha
```

Agents use this naturally — they don't announce "I remember that..." but simply know.

## Correction

If outheis has wrong information:

1. **Explicit correction:** `! I'm 36, not 35`
2. **CLI edit:** `outheis memory --clear user` then re-add
3. **Direct file edit:** Modify JSON in `~/.outheis/human/memory/`

The Pattern agent respects explicit (`!`) entries and won't override them with lower-confidence extractions.

---

## Rules

Rules are the stable distillation of memory — behavioral principles that shape how outheis works with you.

### Two Layers

| | System Rules | User Rules |
|---|--------------|------------|
| **Source** | Developers | Emergent from interaction |
| **Purpose** | Boundaries, capabilities | Style, preferences |
| **Location** | `src/outheis/agents/rules/` | `~/.outheis/human/rules/` |
| **Mutability** | Changes with code updates | Grows over time |

**System rules** define what an agent *can* do — architectural constraints.

**User rules** define how an agent *should* do it — your working style.

### How User Rules Emerge

User rules aren't written by you directly. They emerge from memory through the Pattern agent:

```
Day 1: "Please give me shorter answers"
Day 3: "That's too long, can you be more concise?"
Day 7: "Keep it brief"
Day 12: "Shorter please"
Day 15: "Just the essentials"
        ↓
Pattern agent detects: 5 requests for brevity
        ↓
User Rule created: "User prefers concise responses"
```

The threshold is deliberately high (≥5 occurrences, spread over multiple days) to prevent temporary moods from becoming permanent rules.

### Memory vs. Rules

| | Memory | Rules |
|---|--------|-------|
| **Timescale** | Days to weeks | Months to years |
| **Volatility** | Can expire, frequently updated | Stable once established |
| **Content** | Facts, observations | Principles, patterns |
| **Example** | "User is 35 years old" | "User prefers brevity" |

Memory is *what we know*. Rules are *how we work*.

### Storage

```
~/.outheis/human/rules/
├── common.md      # Applies to all agents
├── relay.md       # Conversation style
├── data.md        # Search behavior
├── agenda.md      # Scheduling preferences
└── pattern.md     # Extraction behavior
```

### CLI

```bash
# View all rules
outheis rules

# View rules for specific agent
outheis rules relay

# View only user rules (emergent)
outheis rules --user

# View only system rules (architectural)
outheis rules --system
```

### Coherent Personality

Although outheis consists of five agents, you experience one assistant. Rules maintain this coherence:

- **Common rules** ensure consistent behavior across all agents
- **Agent-specific rules** allow appropriate specialization
- **User rules** adapt the entire system to your working style

Over time, outheis develops a stable personality — not programmed, but grown from working together.

