# Mermaid conventions

One idea per diagram, at most ~12 nodes; split rather than cram. Every node label is a glossary
concept or a real symbol from the code, never a paraphrase. Put the citation for each diagram in a
line under it, not inside the labels (Mermaid chokes on `:` and `/` in labels — quote them:
`A["server/route.go"]`).

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
```

One subgraph per process. Externals are cylinders `[( )]`; entry points are stadiums `([ ])`.
In-process arrows are call direction; cross-process arrows say the protocol.

## Data flow — `sequenceDiagram`

```mermaid
sequenceDiagram
    participant C as Client
    participant A as api.CreateCluster
    participant S as store.CreateCluster
    participant E as etcd
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
```

Use for state machines that the API's guarantees depend on.
