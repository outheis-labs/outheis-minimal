# Agents

## Overview

| Name | Role | Nickname | Priority | Run Mode |
|------|------|----------|----------|----------|
| relay | Communication interface | @ou | NORMAL | daemon |
| data | Knowledge management | @zeno | NORMAL | on-demand |
| agenda | Personal secretary | @cato | NORMAL | on-demand |
| action | Task execution | @hiro | NORMAL | on-demand |
| pattern | Reflection & learning | @rumi | LOW | scheduled |

## Base Agent

All agents inherit from `BaseAgent`:

```python
from outheis.agents.base import BaseAgent

class MyAgent(BaseAgent):
    name = "my_agent"
    
    def get_system_prompt(self) -> str:
        return "You are..."
    
    def handle(self, msg: Message) -> Optional[Message]:
        # Process message, return response
        pass
```

### Methods

```python
# Send response to transport (user-facing)
self.respond(
    to="transport",
    payload={"text": "Hello!"},
    conversation_id=msg.conversation_id,
    reply_to=msg.id,
)

# Request another agent
self.request(
    to="data",
    payload={"query": "search vault"},
    conversation_id=msg.conversation_id,
    intent="search",
)

# Get conversation context
context = self.get_conversation_context(msg.conversation_id, max_messages=10)

# Log session note for Pattern agent
self.log_session_note(
    problem="User corrected date format",
    solution="Use DD.MM.YYYY for German locale",
    session_id=msg.conversation_id,
)
```

## Relay Agent

**File:** `agents/relay.py`

The only agent that speaks directly to users. Routes unclear requests, composes responses.

```python
def handle(self, msg: Message) -> Optional[Message]:
    text = msg.payload.get("text", "")
    context = self.get_conversation_context(msg.conversation_id)
    
    response_text = self._call_llm(text, context)
    
    return self.respond(
        to="transport",
        payload={"text": response_text},
        conversation_id=msg.conversation_id,
        reply_to=msg.id,
    )
```

### LLM Call

```python
def _call_llm(self, text: str, context: list[Message]) -> str:
    import anthropic
    
    client = anthropic.Anthropic()
    
    messages = []
    for msg in context[-5:]:
        if msg.from_user:
            messages.append({"role": "user", "content": msg.payload.get("text", "")})
        elif msg.from_agent == "relay":
            messages.append({"role": "assistant", "content": msg.payload.get("text", "")})
    
    messages.append({"role": "user", "content": text})
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=self.get_system_prompt(),
        messages=messages,
    )
    
    return response.content[0].text
```

## Data Agent

**File:** `agents/data.py`

Knowledge management across vaults.

**Status:** Stub (MVP)

**Capabilities:**
- Read vault files (Markdown + YAML frontmatter)
- Search by title, tag, content
- Maintain search index

```python
from outheis.core.vault import read_file, find_by_tag, search_content

# Read file with frontmatter
vf = read_file(path)
print(vf.title)      # From frontmatter or filename
print(vf.tags)       # From frontmatter
print(vf.body)       # Content without frontmatter

# Search
results = find_by_tag(vault_path, "project")
results = search_content(vault_path, "deadline")
```

## Agenda Agent

**File:** `agents/agenda.py`

Personal secretary — filtering, prioritizing, learning preferences.

**Status:** Stub (MVP)

**Owns:**
- `Agenda/Daily.md`
- `Agenda/Inbox.md`
- `Agenda/Exchange.md`

## Action Agent

**File:** `agents/action.py`

Task execution and external integrations.

**Status:** Stub (MVP)

**Capabilities:**
- Network access
- Code execution
- External API calls
- Write to `human/imports/`

## Pattern Agent

**File:** `agents/pattern.py`

Reflection, insight extraction, learning.

**Status:** Stub (MVP)

**Scheduled:** Default 04:00 local time

**Manual trigger:**
```bash
outheis pattern
outheis pattern --dry-run
```

### Learning Loop

```
Session Notes           Pattern Agent              Insights
     │                       │                        │
     │   ┌───────────────────┤                        │
     │   │ 1. Review notes   │                        │
     │   │ 2. Find patterns  │                        │
     │   │ 3. Generalize     │                        │
     │   └───────────────────┤                        │
     │                       │────────────────────────▶│
     │                       │   Write insight         │
     │                       │                        │
```

**Generalization criteria:**
- Pattern appears ≥3 times
- Not specific to one instance
- Actionable for agents

### Session Notes

Written by any agent when user helps solve a problem:

```json
{
  "v": 1,
  "id": "note_1731672000",
  "session_id": "conv_123",
  "agent": "relay",
  "problem": "User corrected date format",
  "solution": "Use DD.MM.YYYY for German locale",
  "context": {"channel": "signal"},
  "created_at": "2025-11-15T10:00:00Z",
  "reviewed": false
}
```

### Insights

Generalized knowledge from session notes:

```json
{
  "v": 1,
  "id": "ins_1731672000",
  "type": "preference",
  "domain": "formatting",
  "insight": "User prefers German date format DD.MM.YYYY",
  "confidence": 0.8,
  "evidence_count": 3,
  "source_sessions": ["conv_123", "conv_456", "conv_789"],
  "created_at": "2025-11-15T04:00:00Z"
}
```
