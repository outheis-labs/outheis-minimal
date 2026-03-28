# Systems Survey: Operating Systems and Applicable Concepts

This document surveys operating systems and architectural patterns relevant to multi-agent AI system design.

---

## DragonFlyBSD

**Origin**: Forked from FreeBSD 4.x in 2003 by Matthew Dillon  
**Focus**: SMP scalability through message passing

### Relevant Concepts

#### LWKT (Light Weight Kernel Threads)

Traditional Unix kernels use a Big Kernel Lock (BKL) or fine-grained locking. Both have problems: BKL doesn't scale; fine-grained locking is complex and deadlock-prone.

DragonFlyBSD's approach: **per-CPU scheduling with message passing**.

- Each CPU runs its own scheduler
- No global run queue lock
- Threads migrate between CPUs via explicit messages

#### IPI Message Queues

Inter-Processor Interrupts (IPIs) deliver messages between CPUs:

```
CPU 0                CPU 1                CPU 2
┌─────────┐          ┌─────────┐          ┌─────────┐
│ Queue 0 │          │ Queue 1 │          │ Queue 2 │
└────▲────┘          └────▲────┘          └────▲────┘
     │                    │                    │
     └────────────────────┴────────────────────┘
              Messages go directly to target
```

**Not a central queue**. Each CPU has its own. Producers write to the target's queue; consumers read only from their own.

#### Ownership Semantics

Data "belongs" to a CPU. Only the owner modifies it. Others send messages requesting changes.

This eliminates:
- Lock contention
- Cache line bouncing
- Deadlocks

### Applicability to Agent Systems

| DragonFlyBSD | Agent System |
|--------------|--------------|
| CPU | Agent |
| Per-CPU queue | Per-agent inbox |
| IPI message | Inter-agent message |
| Ownership | Domain responsibility |
| No shared locks | No shared mutable state |

---

## Erlang/OTP

**Origin**: Developed at Ericsson for telecom switches (1986)  
**Focus**: Fault tolerance, concurrency, hot code reloading

### Relevant Concepts

#### Actor Model

Processes (actors) are:
- Isolated (no shared memory)
- Identified by PID
- Communicate only via async messages

```
┌─────────┐    message    ┌─────────┐
│ Actor A │──────────────►│ Actor B │
└─────────┘               └─────────┘
     │                         │
     │    (no shared state)    │
     └─────────────────────────┘
```

#### Supervision Trees

Processes are organized hierarchically. Parents supervise children:

```
        ┌──────────────┐
        │  Supervisor  │
        └──────┬───────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌───────┐ ┌───────┐ ┌───────┐
│Worker │ │Worker │ │Worker │
└───────┘ └───────┘ └───────┘
```

Supervisor strategies:
- **one_for_one**: Restart only the failed child
- **one_for_all**: Restart all children if one fails
- **rest_for_one**: Restart failed child and those started after it

#### "Let It Crash"

Don't program defensively. Let processes fail. The supervisor restarts them in a known good state.

This is counterintuitive but powerful: failure handling is separated from business logic.

### Applicability to Agent Systems

| Erlang/OTP | Agent System |
|------------|--------------|
| Process | Agent |
| PID | Agent ID |
| Mailbox | Message queue |
| Supervisor | Dispatcher |
| Restart strategy | Agent recovery policy |
| Hot code reload | Agent update without downtime |

---

## seL4

**Origin**: Formally verified microkernel (NICTA/Data61)  
**Focus**: Security through minimal trusted computing base

### Relevant Concepts

#### Capabilities

A capability is an unforgeable token granting specific rights to a specific object.

```
┌─────────────────────────────────────┐
│ Capability                          │
│                                     │
│  Object: FileHandle_42              │
│  Rights: Read, Write                │
│  Holder: Process_7                  │
└─────────────────────────────────────┘
```

You can only access what you hold capabilities for. No ambient authority.

#### Minimal Kernel

seL4's kernel provides only:
- Threads
- Address spaces
- IPC
- Capability management

Everything else (filesystems, drivers, networking) runs in user space.

### Applicability to Agent Systems

| seL4 | Agent System |
|------|--------------|
| Capability | Permission token |
| Object | Resource (file, API, domain) |
| Rights | Read, write, execute, delegate |
| Minimal kernel | Minimal dispatcher |

Example: A pattern agent holds write capability for insights; others hold only read capability.

---

## OpenBSD

**Origin**: Forked from NetBSD in 1995 by Theo de Raadt  
**Focus**: Security, correctness, simplicity

### Relevant Concepts

OpenBSD has contributed many security innovations. For agent architectures, two are particularly applicable:

#### pledge(2)

A process declares upfront which system call classes it needs. After pledging, any other syscall terminates the process.

```c
pledge("stdio rpath", NULL);  // Only stdio and read-only file access
// From here: no network, no write, no exec—enforced by kernel
```

This is **self-imposed restriction**. The process gives up capabilities it doesn't need.

#### unveil(2)

A process declares which filesystem paths it can access. Everything else becomes invisible.

```c
unveil("/var/data", "r");   // Read-only access to /var/data
unveil("/tmp", "rwc");      // Read, write, create in /tmp
unveil(NULL, NULL);         // Lock it down—no more unveil calls allowed
```

After the final `unveil(NULL, NULL)`, the process cannot expand its view. The filesystem has effectively shrunk to the declared paths.

#### Privilege Separation

OpenBSD daemons split into two processes:

```
┌─────────────────┐
│ Parent (root)   │  ← Holds socket, keys, minimal code
└────────┬────────┘
         │ fork
         ▼
┌─────────────────┐
│ Child (nobody)  │  ← Parses input, does work, unprivileged
└─────────────────┘
```

The child handles untrusted input. If compromised, it has no privileges. The parent only performs minimal, audited operations on the child's behalf.

#### Historical Context: Jails and Containers

Process isolation has evolved through several stages: chroot (1979), FreeBSD jails (1999), Solaris zones, Linux containers, Docker. These provide **static isolation**—you build the container, then run in it.

pledge/unveil represent a different approach: **dynamic restriction**. A process starts with full capabilities and progressively gives them up as it initializes. This is often more practical for applications that need resources during startup but not during operation.

### Applicability to Agent Systems

| OpenBSD | Agent System |
|---------|--------------|
| pledge | Agent declares capabilities at startup |
| unveil | Agent sees only relevant paths |
| privsep | Dispatcher privileged, agents restricted |
| Secure by default | No implicit permissions |

Example: A data agent pledges `["vault:read", "vault:write"]` and unveils only `vault/`. It cannot access `human/`, cannot make network calls, cannot execute code.

---

## macOS / Darwin

**Origin**: Apple's XNU kernel, combining Mach microkernel with BSD  
**Focus**: Consumer usability with Unix underpinnings

### Relevant Concepts

#### Grand Central Dispatch (GCD)

A system-wide framework for concurrent execution. Instead of managing threads directly, work is submitted to dispatch queues:

```
┌─────────────────────────────────────────┐
│           Dispatch Queues               │
├─────────────────────────────────────────┤
│  Main Queue      │ Serial, UI thread    │
├──────────────────┼──────────────────────┤
│  Global Queues   │ Concurrent, by       │
│  (QoS levels)    │ priority:            │
│                  │  - User Interactive  │
│                  │  - User Initiated    │
│                  │  - Utility           │
│                  │  - Background        │
├──────────────────┼──────────────────────┤
│  Custom Queues   │ Serial or concurrent │
└──────────────────┴──────────────────────┘
```

The system manages thread pools. You just say "do this work" and "how important is it."

#### Quality of Service (QoS)

Work is tagged with its priority level. The system can:
- Throttle background work when the user is active
- Boost priority when results are needed immediately
- Balance energy usage on laptops/phones

### Applicability to Agent Systems

| GCD | Agent System |
|-----|--------------|
| Dispatch queue | Agent message queue |
| QoS levels | Agent priority |
| Main queue | User-facing relay agent |
| Background queue | Pattern recognition agent |
| Serial queue | Sequential operations (writes) |
| Concurrent queue | Parallel operations (reads) |

Example: A relay agent handling user input runs at high priority. A pattern agent analyzing history runs in background. The dispatcher manages queue priorities based on system load and user activity.

---

## Plan 9

**Origin**: Bell Labs (1980s–2000s), successor to Unix  
**Focus**: Distributed systems, uniform interfaces

### Relevant Concepts

#### Everything is a File

Not just files and devices—processes, network connections, windows, even other machines appear as files.

```
/proc/42/mem      # Process memory
/net/tcp/clone    # New TCP connection
/mnt/remote/      # Remote machine's filesystem
```

#### 9P Protocol

A simple protocol for accessing files over a network. Any resource that implements 9P can be mounted and accessed uniformly.

#### Per-Process Namespaces

Each process can have its own view of the filesystem. Mounting resources is local to the process.

### Applicability to Agent Systems

| Plan 9 | Agent System |
|--------|--------------|
| File | Resource |
| 9P | Resource access protocol |
| Mount | Attach knowledge base |
| Namespace | Agent's view of available resources |

Example: A vault is mounted into an agent's namespace. The agent interacts with it through a uniform file-like interface.

---

## Event Sourcing

**Origin**: Domain-Driven Design community  
**Focus**: State as derived from immutable events

### Relevant Concepts

#### Append-Only Log

State is not stored directly. Instead, events are appended to an immutable log:

```
┌─────────────────────────────────────────────┐
│ Event Log                                   │
│                                             │
│ 1. UserCreated {id: 1, name: "..."}         │
│ 2. UserEmailChanged {id: 1, email: "..."}   │
│ 3. UserDeleted {id: 1}                      │
└─────────────────────────────────────────────┘
```

Current state = fold over all events.

#### Benefits

- **Audit trail**: Complete history
- **Replay**: Reconstruct any past state
- **Debugging**: See exactly what happened
- **Temporal queries**: "What was the state at time T?"

### Applicability to Agent Systems

| Event Sourcing | Agent System |
|----------------|--------------|
| Event | Message |
| Event log | Message queue (append-only) |
| Projection | Current conversation state |
| Replay | Debug, retry, recover |

---

## Unikernels

**Origin**: Academic research (MirageOS, IncludeOS, Nanos)  
**Focus**: Single-purpose, minimal attack surface

### Relevant Concepts

#### Library Operating System

The application links directly against OS libraries. No separate kernel. The result is a single bootable image.

```
Traditional:
┌─────────────┐
│ Application │
├─────────────┤
│   Kernel    │
└─────────────┘

Unikernel:
┌─────────────────────┐
│ Application + LibOS │
└─────────────────────┘
```

#### Specialization

Each unikernel does one thing. No shell, no users, no unnecessary drivers.

### Applicability to Agent Systems

| Unikernel | Agent System |
|-----------|--------------|
| Single-purpose image | Single-purpose agent |
| No shell | No general capabilities |
| Minimal surface | Minimal prompt, focused role |

Example: An action agent is specialized—it executes tasks. It doesn't analyze patterns or compose messages.

---

## Comparison Matrix

| System | Primary Contribution | Key Mechanism |
|--------|---------------------|---------------|
| DragonFlyBSD | Scalable concurrency | Per-CPU queues, ownership |
| Erlang/OTP | Fault tolerance | Supervision, let it crash |
| seL4 | Formal security | Capabilities |
| OpenBSD | Practical security | pledge, unveil, privsep |
| macOS/GCD | Priority scheduling | QoS-tagged dispatch queues |
| Plan 9 | Uniform access | Everything is a file |
| Event Sourcing | Auditability | Append-only log |
| Unikernels | Minimalism | Single-purpose images |

---

## Synthesis for Agent Architectures

A well-designed multi-agent system can combine:

1. **DragonFlyBSD's message passing** for agent communication
2. **Erlang's supervision** for fault tolerance
3. **seL4's capabilities** for formal access control
4. **OpenBSD's pledge/unveil** for practical, self-imposed restrictions
5. **GCD's priority queues** for workload management
6. **Plan 9's uniform interface** for resource access
7. **Event sourcing's append-only log** for auditability
8. **Unikernel's specialization** for focused agent roles

These are not competing approaches—they address orthogonal concerns and compose naturally.

---

Next: [03-architecture.md](03-architecture.md) — The outheis architecture derived from these principles.
