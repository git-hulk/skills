# Orthogonality analysis

**Definition.** A set of operations (endpoints, RPCs, commands, or a library's interfaces) is
orthogonal when each one does one independent thing, any combination of them is meaningful, and
changing one does not force a change in another. The concept comes from *The Pragmatic Programmer*
and the Unix tool philosophy; the practical test is: *can a user learn each operation in
isolation and still predict what a combination will do?*

Analysis, not a change request: the output says where the design is and is not orthogonal, with
evidence, and what a more orthogonal shape would look like. Whether to change anything is the
maintainers' call; say so.

## The six checks

Apply each to the API map (service) or interface map (library). For every finding cite
`file:line` — the two handlers that overlap, the field that is ignored unless another is set.

| # | Check | Question to answer | What a failure looks like |
| --- | --- | --- | --- |
| 1 | **Non-overlap** | Is there exactly one way to reach each outcome? | Two endpoints differing only by a flag; a "batch" variant whose semantics diverge from the single one; an RPC that is a strict superset of another |
| 2 | **Independence** | Can A be understood and called without knowing B's state? | Hidden ordering (`Init` before `X`); a parameter meaningful only when another is set; behaviour that changes with global config |
| 3 | **Composability** | Do the primitives combine to build the compound operations, or does each compound re-implement them? | `MigrateSlot` and `MoveShard` with separate code paths; an option struct where flags interact in undocumented ways |
| 4 | **Consistency / symmetry** | Same resource → same verb set, naming, pagination, error shape? | `create` without `delete`; `list` without `get`; one endpoint returns `404`, its sibling `200` with empty body |
| 5 | **Leakage** | Does the surface expose storage or transport details a caller should not depend on? | Row IDs from the database in URLs; etcd revision numbers in responses; a transport-specific error type in a domain interface |
| 6 | **Blast radius** | If A's semantics change, how many other operations' code, docs, or tests change? | Count from the code: shared handlers, shared validation, shared response builders |

Library-specific additions:

- **Minimal interface.** How many methods must a caller implement to plug in a store, transport,
  or codec? More than ~5 usually means the interface mixes concerns (e.g. `LogStore` + `StableStore`
  split versus one fat `Storage`).
- **Option explosion.** Count the constructor options; list the pairs that interact. Options that
  only matter when another is set are a failed check 2.
- **Lifecycle coupling.** Which methods are valid in which state? An interface that panics or
  errors when called "too early" is a hidden ordering constraint.
- **Error surface.** Typed / sentinel errors the caller can branch on, versus strings.

## Scoring table

Score each API group (resource) or interface family, not each endpoint:

| Group | Non-overlap | Independence | Composability | Consistency | Leakage | Blast radius | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| e.g. `clusters` | ✅ | ⚠️ | ✅ | ❌ | ✅ | small | `server/api/cluster.go:88` … |

✅ holds · ⚠️ partial · ❌ fails. Then:

1. **Verdict** in two or three sentences: is the surface orthogonal as a whole, and where is the
   design's centre of gravity (which resource or interface everything else composes from).
2. **Non-orthogonal spots**, ranked by how likely a newcomer is to be bitten: what, where,
   why it probably happened (history, convenience, backward compatibility — check `git log`),
   and what the orthogonal shape would be.
3. **Where orthogonality was deliberately traded away** and what it bought (performance,
   atomicity, ergonomics). A batch endpoint that exists for atomicity is not a defect; say so.
