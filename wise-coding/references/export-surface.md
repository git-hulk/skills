# Minimal export surface

Everything visible outside its package or module is a contract: callers will depend on it, and
removing or changing it later needs coordination, deprecation, or a major version. Visible
things also cost every reader who has to decide whether they matter. So the default is private,
and each exception needs a caller you can point to.

## The rules

1. **Private by default.** A new type, function, method, constant, or field is unexported until
   code in another package, module, or client needs it — *in this change*. When that caller
   appears, export it then. "Might be useful" and "for tests" are not callers.
2. **Parameters are the narrowest thing that works.** Pass `userID int64`, not `*User`; pass
   `until time.Time`, not `req *UpdateFeedRequest`. A boolean parameter that selects between two
   behaviors is two methods or an enum. An options struct with one field is a parameter.
3. **Return the narrowest thing the caller uses.** Not the storage row when the API needs three
   fields; not `map[string]any`; not `(value, found bool, err error)` when the repo already has
   a not-found error.
4. **Interface methods are the most expensive export.** Every implementer, including fakes in
   tests, must change. Add a method only when a caller needs it through the interface — a
   concrete type can grow a method without touching the interface.
5. **No speculative knobs.** No option, flag, config key, or field that this change never sets to
   a non-default value.
6. **Follow the repo's exposure convention.** If the repo returns interfaces from constructors,
   do that; if it exposes concrete structs, do that. Minimal means "no more than the sibling",
   not "less than the sibling in a style the repo does not use".

## The helper test

Before keeping a new helper function, all three must hold:

- It is called from **two or more places**, or it names a **domain concept** already in the
  glossary (`isMuted(feed)` is a concept; `getFeedIDFromRequest(r)` is plumbing).
- Its body does **more than delegate**. A function whose body is one call to another function
  with the arguments reordered is noise.
- Removing it would make a call site **harder to read**, not just longer. Three lines inline
  are usually clearer than a jump to a definition.

Otherwise inline it. This applies with extra force to `utils`, `helpers`, and `common`
packages: adding to them is the path of least resistance and the most regretted.

## Audit procedure (step 6)

Read the diff hunk by hunk.

```text
For each added exported symbol:   grep for callers outside its package → none? make it private.
For each added parameter/field:   find the caller that passes a non-default value → none? remove.
For each added function < ~8 lines: count call sites → one? inline.
For each added interface method:  which caller invokes it via the interface? → none? move to the concrete type.
For each added error/constant:    is it a concept the glossary has? → no? reuse an existing one or justify.
```

A quick mechanical pass, in Go: `git diff | grep -E '^\+(func|type|var|const) [A-Z]|^\+func \([^)]*\) [A-Z]'`
lists the new exports; for each, `grep -rn '<Symbol>' --include='*.go' | grep -v '<its package>'`
shows whether anyone else uses it.

## Visibility mechanics by language

| Language | Private | Package / crate-visible | Public |
| --- | --- | --- | --- |
| Go | lowercase identifier | `internal/` directory blocks imports from outside the module tree | uppercase identifier |
| TypeScript / JS | no `export`; `#field` or `private` in classes | not exported from the package's `index.ts` / `exports` map | exported from the entry point |
| Python | `_name` prefix; omit from `__all__` | module-level in a private module `_impl.py` | listed in `__all__`, re-exported from `__init__.py` |
| Rust | default (module-private) | `pub(crate)`, `pub(super)` | `pub` reachable from the crate root |
| Java / Kotlin | `private` | package-private (no modifier) / `internal` | `public` |
| C# | `private` | `internal` | `public` |
| SQL | — | — | every column and table is public to every query; add the fewest |
| HTTP / RPC | — | — | every field is public forever; omit optional fields until requested |

In languages where the package boundary is the unit (Go, Rust), prefer keeping new code in the
package that already owns the sibling so that nothing has to be exported for the pieces to see
each other.
