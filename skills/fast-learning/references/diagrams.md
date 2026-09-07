# Mermaid conventions

One idea per diagram, at most ~12 nodes; split rather than cram. Every node label is a glossary
concept or a real symbol from the code, never a paraphrase. Put the citation for each diagram in a
line under it, not inside the labels (Mermaid chokes on `:` and `/` in labels — quote them:
`A["server/route.go"]`).

## Colors for workflows and architecture

Use explicit colors in architecture and workflow diagrams, including sequence and state diagrams.
Keep the same role or phase the same color throughout a report. Use this default palette, adapting
roles to the repository; include a short legend for the colors actually used:

| Role or phase | Fill | Border / text |
| --- | --- | --- |
| Entry points / request handling | `#DBEAFE` | `#1E40AF` |
| Core processing | `#DCFCE7` | `#166534` |
| Storage / persistence | `#F3E8FF` | `#6B21A8` |
| External dependencies / waiting | `#FEF3C7` | `#92400E` |
| Failure / recovery, when present | `#FEE2E2` | `#991B1B` |

For flowcharts and state diagrams, use `classDef` plus `class` assignments. For data flows, assign
a distinct color to each component using the sequence-diagram guidance below; component identity
takes precedence over this role palette. Do not use flowchart `classDef` syntax in sequence diagrams.
Keep fills light and text dark; preserve labels, shapes, and branch annotations so meaning does
not depend on color alone.

## Concept relationship map — `flowchart`

```mermaid
flowchart LR
    Namespace -->|"contains N"| Cluster
    Cluster -->|"contains N"| Shard
    Shard -->|"has 1 master"| Node
    Shard -->|"has N replicas"| Node
    Shard -->|"owns slot ranges"| Slot
    Controller -->|"probes"| Node
    Controller -->|"persists in"| Store
```

Edges carry the relationship *and* cardinality. Direction is owner → owned or producer → consumer.

## Architecture — `flowchart` with subgraphs

```mermaid
flowchart TB
    Client([CLI / Web UI])
    subgraph Server["controller-server process"]
        API["HTTP API (gin)"] --> Ctl[Controller]
        Ctl --> Store[Store]
    end
    Store --> Etcd[(etcd / consul / zk)]
    Ctl -->|"RESP probe"| KV[(kvrocks nodes)]
    Client --> API
    classDef entry fill:#DBEAFE,stroke:#1E40AF,color:#1E40AF
    classDef core fill:#DCFCE7,stroke:#166534,color:#166534
    classDef storage fill:#F3E8FF,stroke:#6B21A8,color:#6B21A8
    classDef external fill:#FEF3C7,stroke:#92400E,color:#92400E
    class Client,API entry
    class Ctl core
    class Store,Etcd storage
    class KV external
```

One subgraph per process. Externals are cylinders `[( )]`; entry points are stadiums `([ ])`.
In-process arrows are call direction; cross-process arrows say the protocol.

## Data flow — `sequenceDiagram`

Give every component a distinct color, even when components share a role. Keep each component's
color consistent across all data flows. Wrap each participant in its own colored `box rgb(...)`
to color its vertical lane; use the component name as the box label. Color identifies components,
not execution phases. See [Mermaid's box syntax](https://mermaid.js.org/syntax/sequenceDiagram.html#grouping-box).

```mermaid
sequenceDiagram
    box rgb(219, 234, 254) Client
        participant C as Client
    end
    box rgb(220, 252, 231) API
        participant A as api.CreateCluster
    end
    box rgb(243, 232, 255) Store
        participant S as store.CreateCluster
    end
    box rgb(254, 243, 199) etcd
        participant E as etcd
    end
    C->>A: POST /namespaces/{ns}/clusters
    A->>A: validate (cluster.go:74)
    A->>S: CreateCluster(ns, cluster)
    S->>E: Txn put /kvrocks/ns/cluster
    E-->>S: revision
    S-->>A: ok
    A-->>C: 201 {cluster}
```

Participants are components from the architecture diagram; arrow labels name the function. Use
`alt` / `loop` for retries and error branches only when they matter to the flow's guarantee.

## Schema — `erDiagram`

```mermaid
erDiagram
    USERS ||--o{ FEEDS : owns
    CATEGORIES ||--o{ FEEDS : groups
    FEEDS ||--o{ ENTRIES : has
    ENTRIES ||--o{ ENCLOSURES : has
    USERS {
        bigint id PK
        text username UK
    }
    FEEDS {
        bigint id PK
        bigint user_id FK
        bigint category_id FK
        text feed_url
    }
```

Show keys and the columns that appear in the flows; omit the rest. For KV / coordination stores
use a table of key prefixes instead:

| Key pattern | Value | Written by | Read by | Consistency |
| --- | --- | --- | --- | --- |
| `/kvrocks/<ns>/<cluster>` | Cluster JSON | `store.CreateCluster` | `controller.loadCluster` | etcd Txn, watched |

## Library interfaces — `classDiagram`

```mermaid
classDiagram
    class Raft {
        +Apply(cmd, timeout) ApplyFuture
        +Leader() ServerAddress
        +Shutdown() Future
    }
    class FSM { <<interface>> +Apply(*Log) +Snapshot() +Restore(io.ReadCloser) }
    class LogStore { <<interface>> +GetLog() +StoreLogs() +DeleteRange() }
    class Transport { <<interface>> +AppendEntries() +RequestVote() }
    Raft --> FSM : caller implements
    Raft --> LogStore : caller supplies
    Raft --> Transport : caller supplies
    NetworkTransport ..|> Transport
    InmemStore ..|> LogStore
```

Mark caller-implemented interfaces explicitly; that split is the first thing a library user needs.

## Internal state — `stateDiagram-v2`

```mermaid
stateDiagram-v2
    [*] --> Follower
    Follower --> Candidate : election timeout
    Candidate --> Leader : majority votes
    Candidate --> Follower : newer election epoch seen
    Leader --> Follower : newer election epoch seen
    Leader --> Shutdown
    classDef waiting fill:#FEF3C7,stroke:#92400E,color:#92400E
    classDef active fill:#DCFCE7,stroke:#166534,color:#166534
    classDef stopped fill:#F1F5F9,stroke:#475569,color:#475569
    class Follower,Candidate waiting
    class Leader active
    class Shutdown stopped
```

Use for state machines that the API's guarantees depend on.
