# C++ Review Standards

## First-Version Standard

Use the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html) as the default
coding standard. This first-version checklist was checked against the upstream guide on
2026-09-08; it is a focused review baseline, not a complete copy or an upstream version number.
Read the relevant linked section when its exceptions or details matter.

Explicit user/repository rules and the target version's semantics take precedence. Preserve
documented deviations; do not impose Google's current compiler baseline on an older target.
Report standards violations separately in meaning from bugs, following `SKILL.md`.

## Establish the Build Contract

Inspect the affected target's C++ standard, compiler and standard-library versions, platform/ABI,
compile definitions, exception/RTTI settings, and CI builds. Prefer actual compile commands or
target configuration over assuming one global CMake setting applies everywhere. Distinguish C++
sources from C and generated headers. Follow repository ownership idioms and lint configuration.

Google's guide is a coding policy, not the ISO standard or a reason to rewrite legacy code.
For version-sensitive language claims, consult the matching standard/draft and implementation
documentation. Do not demand C++20 facilities from a C++17 target.

## Review Questions

| Area | Check when affected | Evidence needed before reporting |
| --- | --- | --- |
| Lifetime | Returning references/views, temporaries, lambda captures, async callbacks, coroutine frames | The owning object's destruction or invalidation before the borrow is used |
| Ownership | Raw/smart pointers, transfer, deleters, double-free, cycles, error-path cleanup | Concrete ownership transitions and the path that leaks or releases twice |
| Containers | Reallocation, erase, iterator/reference invalidation, bounds, borrowed spans | The actual container operation and a subsequent invalid access |
| Object semantics | Copy/move operations, invariants, self-assignment, slicing, virtual destruction | A supported operation or deletion path that breaks the object's contract |
| Undefined behavior | Uninitialized reads, signed overflow, invalid shifts, alignment, aliasing, lifetime | Reachable operand values or storage usage; not merely a risky-looking expression |
| Concurrency | Data races, lock order, callbacks under locks, condition predicates, atomics | A feasible interleaving and violated synchronization or progress guarantee |
| Exceptions | Partial construction/update, cleanup, `noexcept`, failure across API boundaries | A throw-capable operation and the resulting termination, leak, or broken invariant |
| Compatibility | Public layout, virtual tables, exported signatures, templates, serialization | A supported source/binary consumer or stored format affected by the change |

Check integer promotions, signed/unsigned conversions, and size arithmetic against actual bounds.
Do not label unsigned wrap undefined behavior; it may instead violate an allocation or indexing
contract. Moved-from standard-library objects are generally valid but unspecified unless a stronger
contract applies; identify the operation and required precondition before reporting misuse.

## Google Checklist

- [Headers](https://google.github.io/styleguide/cppguide.html#Header_Files): make headers self-contained with guards and direct includes; include the related header first.
- [Namespaces](https://google.github.io/styleguide/cppguide.html#Namespaces): avoid using-directives; keep implementation details out of public headers.
- [Conversions](https://google.github.io/styleguide/cppguide.html#Implicit_Conversions): mark single-argument conversion constructors and conversion operators `explicit`; preserve copy/move and initializer-list exceptions.
- [Ownership](https://google.github.io/styleguide/cppguide.html#Ownership_and_Smart_Pointers): prefer unique ownership; use shared ownership only when required. Make copy/move support explicit in the API.
- [Globals](https://google.github.io/styleguide/cppguide.html#Static_and_Global_Variables): avoid static-storage objects with nontrivial destruction; examine initialization dependencies.
- [Exceptions](https://google.github.io/styleguide/cppguide.html#Exceptions): do not introduce exceptions under the Google baseline; check documented platform exceptions and repository policy.
- [Naming](https://google.github.io/styleguide/cppguide.html#Naming): use `MixedCase` types/functions, `snake_case` variables, trailing underscores for class data members, and `kMixedCase` constants, observing documented exceptions.
- [Formatting](https://google.github.io/styleguide/cppguide.html#Formatting): use the guide's two-space indentation and 80-column baseline unless repository configuration overrides them.

An explicit repository exception policy overrides Google's default prohibition. Even then, retain
the exception-safety checks above. Do not infer that enabled compiler exception support alone is
a project policy. Avoid introducing Abseil or rewriting APIs solely to match guide examples.

Raw pointers are not inherently defects; determine whether they own or borrow. A `shared_ptr`
does not by itself synchronize accesses to the pointee. `volatile` is not a substitute for the
required inter-thread synchronization. Avoid stylistic smart-pointer replacement findings without
an ownership problem or an explicit repository rule.

## Focused Verification

Use an existing configured build or isolated build directory, preserving the user's build settings:

```sh
cmake --build <configured-build-dir> --target <affected-test-target>
ctest --test-dir <configured-build-dir> -R <relevant-test-regex> --output-on-failure
```

These are examples, not a requirement to introduce CMake. Prefer the project's build/test runner.
Use configured ASan/UBSan builds for memory/undefined-behavior hypotheses, or a separate configured
TSan build for races; do not combine incompatible sanitizers or overwrite shared build flags.
Use existing clang-tidy settings and compile commands when relevant. Compilation or a clean
sanitizer run does not prove all lifetime or concurrency paths safe.

## Primary Sources

- [ISO C++ standards information](https://isocpp.org/std/the-standard): published standards and drafts.
- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html): primary coding standard.
- [Clang AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html),
  [UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html), and
  [ThreadSanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html): tool configuration and scope.
