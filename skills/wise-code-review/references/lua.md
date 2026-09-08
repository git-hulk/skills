# Lua Review Standards

Check changed Lua code against the [Roblox Lua Style Guide](https://roblox.github.io/lua-style-guide/).
Use the checklist to identify applicable rules, then read their linked exceptions before reporting.

**Checklist**

- [Structure](https://roblox.github.io/lua-style-guide/#file-structure): order imports, constants, implementation, exported object, and return; put Roblox services before imports where applicable.
- [Imports](https://roblox.github.io/lua-style-guide/#requires): keep requires at the top, alphabetized within structural groups; consume libraries through their public APIs.
- [Naming](https://roblox.github.io/lua-style-guide/#naming): use `camelCase` locals/functions, `PascalCase` classes/enums, and `LOUD_SNAKE_CASE` local constants; match filenames to exports.
- [Whitespace](https://roblox.github.io/lua-style-guide/#general-whitespace): indent with tabs; keep code under 100 columns and comments within 80, counting tabs as four columns. Avoid vertical alignment.
- [Punctuation](https://roblox.github.io/lua-style-guide/#general-punctuation): omit semicolons. Keep each statement on its own line.
- [Functions](https://roblox.github.io/lua-style-guide/#functions): use call parentheses and named function declarations; keep non-member functions local, respecting late-initialization exceptions.
- [Tables](https://roblox.github.io/lua-style-guide/#tables): avoid mixed list/dictionary tables; use trailing commas in multiline literals.
- [Failures](https://roblox.github.io/lua-style-guide/#error-handling): represent expected failures explicitly; reserve thrown errors for misuse checks and protect calls to throwing dependencies with `pcall` where recovery is intended.

Do not automatically introduce Promise libraries, metatable frameworks, or change an existing
error-return convention to match an example. Scope corrections to the patch; avoid repeating
formatter output as individual review findings.

## Establish the Runtime and Host

Identify the exact Lua version, LuaJIT build, or Luau runtime, host application, libraries, module loader,
and test runtime from project configuration and CI. Embedded Lua, OpenResty, game engines, and
standalone Lua can expose different APIs and lifecycle rules. Do not infer the runtime from the
`.lua` extension or the machine's default `lua` binary.

Use the matching Lua reference manual as the semantic authority. LuaJIT has a Lua 5.1 compatibility
baseline with documented extensions, not blanket Lua 5.4 compatibility. Check repository overrides
and use Luau documentation for Luau-specific behavior rather than treating Lua's
manual as authority for every Luau extension.

## Review Questions

| Area | Check when affected | Evidence needed before reporting |
| --- | --- | --- |
| Truth and defaults | `nil` versus `false`, `x or default`, and/or conditional idioms | A supported false value that is replaced or routed incorrectly |
| Tables | Sparse arrays, `#`, `ipairs`, `pairs` ordering, deletion while traversing | The actual key shape and skipped element, unstable result, or invalid count |
| Scope | Accidental globals, shared module tables, captured upvalues | Another call/request/coroutine that observes unintended shared state |
| Calls | `:` versus `.`, implicit `self`, multiple returns, parentheses, varargs | The callee signature and values actually passed or discarded |
| Errors | `pcall`/`xpcall` status, `nil, err` conventions, cleanup, propagation | A failing operation that is reported as success or loses required cleanup |
| Numbers and strings | Numeric representation, large IDs, coercion, byte versus character indexing, patterns | A supported input outside assumed precision, encoding, or pattern constraints |
| Coroutines and host APIs | Yield legality, resume status, request lifetimes, blocking host calls | The host-specific execution context and a failing or stalled path |
| Metatables and resources | `__index`/`__newindex`, raw access, weak references, finalizers | A relevant metamethod or resource lifetime that changes behavior |
| C API / FFI | Stack balance, indices, registry references, ownership, errors across native frames | The native/VM lifetime and exact stack or boundary violation |

Only `nil` and `false` are false in Lua; zero and the empty string are true. An `or` default is a
bug only when preserving false is part of the contract. The length operator is not a general
element count for sparse tables; `ipairs` stops at the first absent integer entry. Do not assume
`pairs` supplies stable ordering. See the matching manual's expressions and library sections.

Trace all results through wrappers: assigning a call to one variable, parenthesizing it, or moving
it away from the final expression position can truncate multiple results. When nil arguments must
be preserved, check both the explicit count and the unpack bounds, using APIs available in the
target runtime. Do not recommend replacing `unpack` with `table.unpack` on plain Lua 5.1.

## Version and Embedding Boundaries

- Roblox's [if-expression advice](https://roblox.github.io/lua-style-guide/#if-then-else-expressions)
  applies to Luau, not plain Lua/LuaJIT. Do not propose Luau type annotations, `+=`, or if-expressions
  for unsupported runtimes. Use ordinary `if` statements when a portable conditional is needed.
- Roblox service access, module paths using `script`, and scheduling advice apply only to matching
  hosts. Do not introduce `game:GetService`, `delay`, or a Roblox execution model into standalone
  Lua, OpenResty, or another embedding. Confirm the host's current API before suggesting a change.
- Verify support before using integer/bitwise syntax, `//`, `_ENV`, `table.pack`, `table.unpack`,
  or Lua 5.4 `<close>` variables. Do not assume a LuaJIT extension exists in standard Lua.
- Numeric precision depends on the runtime's number configuration and native conversion. Do not
  assume every Lua number is an integer or that every Lua build uses the same representation.
- For C++ embeddings, inspect how Lua is built and how its errors unwind before claiming C++
  destructors will run across a Lua error. Confirm protected-call and cleanup boundaries.
- Garbage collection is not a prompt external-resource release guarantee. Check the host's
  explicit cleanup contract and version-supported closing mechanism on success and error paths.

## Focused Verification

Use the repository's test runner under the actual target runtime, such as its existing Busted or
host integration suite. A standalone Lua test cannot establish host-specific coroutine behavior.
Use the configured Luacheck or formatter's check-only mode when present, preserving configured
host globals rather than treating them all as accidental globals.

For a small hypothesis, run an isolated snippet with the explicit Lua/LuaJIT binary. Record the
version and command; do not claim compatibility from a different runtime's successful execution.
Syntax checks cannot detect table-shape, multi-return, or host-lifecycle failures.

## Primary Sources

- [Roblox Lua Style Guide](https://roblox.github.io/lua-style-guide/): primary coding standard,
  with the runtime and host boundaries above.
- Lua reference manuals: [5.1](https://www.lua.org/manual/5.1/manual.html),
  [5.2](https://www.lua.org/manual/5.2/manual.html),
  [5.3](https://www.lua.org/manual/5.3/manual.html),
  [5.4](https://www.lua.org/manual/5.4/manual.html). For another version, use its matching manual.
- [LuaJIT extensions and compatibility](https://luajit.org/extensions.html).
- [LuaJIT FFI semantics](https://luajit.org/ext_ffi_semantics.html).
