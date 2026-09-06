#!/usr/bin/env python3
"""Print a first-pass inventory of a repository: size, languages, manifests,
entry points, API / storage / docs signals, and a guess at what kind of
project it is. Read-only; stdlib only.

usage: inventory.py [REPO_DIR] [--json]
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "third_party", "thirdparty", "dist",
    "build", "target", ".venv", "venv", "__pycache__", ".idea", ".vscode",
    "testdata", "fixtures", ".next", "coverage", "_build", "deps",
}
LANG_BY_EXT = {
    ".go": "Go", ".rs": "Rust", ".py": "Python", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
    ".java": "Java", ".kt": "Kotlin", ".scala": "Scala", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".c": "C", ".h": "C/C++ header", ".cc": "C++",
    ".cpp": "C++", ".hpp": "C++", ".swift": "Swift", ".m": "Objective-C",
    ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".hs": "Haskell",
    ".zig": "Zig", ".lua": "Lua", ".dart": "Dart", ".sql": "SQL",
    ".proto": "Protobuf", ".graphql": "GraphQL", ".sh": "Shell",
}
MANIFESTS = [
    "go.mod", "go.work", "Cargo.toml", "package.json", "pyproject.toml",
    "setup.py", "requirements.txt", "pom.xml", "build.gradle",
    "build.gradle.kts", "CMakeLists.txt", "Makefile", "Gemfile", "mix.exs",
    "composer.json", "Package.swift", "BUILD", "BUILD.bazel", "WORKSPACE",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Procfile",
    "Chart.yaml", "skaffold.yaml", "serverless.yml", "fly.toml", "app.yaml",
]
DOC_FILES = [
    "README.md", "README.rst", "README", "README.txt", "ARCHITECTURE.md",
    "DESIGN.md", "CONTRIBUTING.md", "DEVELOPMENT.md", "HACKING.md",
    "CHANGELOG.md", "docs", "doc", "adr", "rfcs", "design", "wiki",
]
ENTRY_PATTERNS = [
    re.compile(r"(^|/)main\.go$"), re.compile(r"(^|/)cmd/[^/]+/main\.go$"),
    re.compile(r"(^|/)src/main\.rs$"), re.compile(r"(^|/)src/bin/[^/]+\.rs$"),
    re.compile(r"(^|/)__main__\.py$"), re.compile(r"(^|/)manage\.py$"),
    re.compile(r"(^|/)app\.py$"), re.compile(r"(^|/)server\.(py|js|ts)$"),
    re.compile(r"(^|/)src/(index|main|server|app)\.(js|ts)$"),
    re.compile(r"^bin/[^/.]+$"),
]
LIB_ROOT_PATTERNS = [re.compile(r"(^|/)src/lib\.rs$"), re.compile(r"(^|/)__init__\.py$")]
API_FILE_PATTERNS = [
    re.compile(r"\.proto$"), re.compile(r"(openapi|swagger)[^/]*\.(ya?ml|json)$", re.I),
    re.compile(r"\.graphql$"), re.compile(r"(^|/)routes?\.[a-z]+$"),
    re.compile(r"(^|/)(router|handlers?|controllers?|api|rpc|grpc|endpoints?)(/|\.)"),
]
STORAGE_FILE_PATTERNS = [
    re.compile(r"(^|/)(migrations?|migrate|db/migrate|alembic|flyway|liquibase)/"),
    re.compile(r"\.sql$"), re.compile(r"(^|/)schema\.(prisma|graphql|rb|sql|hcl)$"),
    re.compile(r"(^|/)(models?|entities|entity|ent|repository|repositories|store|storage|dao|persistence)(/|\.)"),
    re.compile(r"(^|/)sqlc\.(ya?ml|json)$"),
]
ROUTE_REGEX = re.compile(
    r"(HandleFunc\(|\.Handle\(|\.(GET|POST|PUT|PATCH|DELETE)\(|@(app|router|bp)\.(route|get|post|put|delete)\(|"
    r"@(Get|Post|Put|Delete|Patch)Mapping|@RestController|Route::|router\.(get|post|put|delete|patch)\(|"
    r"^\s*rpc\s+\w+\s*\(|app\.(get|post|put|delete|patch)\(|#\[(get|post|put|delete|patch)\()",
    re.M,
)
SERVICE_DEP_HINTS = (
    "net/http", "gin-gonic", "labstack/echo", "gorilla/mux", "go-chi", "fiber", "grpc",
    "fastapi", "flask", "django", "express", "koa", "nestjs", "fastify", "actix", "axum",
    "rocket", "tonic", "spring-boot", "rails", "sinatra", "phoenix", "hapi",
)
DB_DEP_HINTS = (
    "gorm", "sqlx", "database/sql", "pgx", "lib/pq", "go-sql-driver", "ent/", "sqlc",
    "sqlalchemy", "psycopg", "asyncpg", "prisma", "typeorm", "sequelize", "knex", "mongoose",
    "diesel", "sea-orm", "redis", "mongo", "etcd", "consul", "zookeeper", "rocksdb", "badger",
    "bolt", "pebble", "sqlite", "clickhouse", "spanner", "bigquery", "dynamodb", "cassandra",
    "kafka", "nats", "rabbitmq", "amqp", "pulsar",
)
CLI_DEP_HINTS = ("spf13/cobra", "urfave/cli", "kingpin", "clap", "structopt", "argparse", "click", "typer", "commander", "yargs", "oclif", "thor", "picocli")


def run(cmd, cwd):
    try:
        return subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def walk(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            p = os.path.join(dirpath, f)
            files.append(os.path.relpath(p, root))
    return files


def count_lines(path):
    try:
        with open(path, "rb") as fh:
            return sum(1 for _ in fh)
    except Exception:
        return 0


def read_text(path, limit=400_000):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except Exception:
        return ""


def tree(root, depth=2):
    lines = []

    def rec(d, prefix, level):
        if level > depth:
            return
        try:
            entries = sorted(os.listdir(d))
        except Exception:
            return
        entries = [e for e in entries if e not in SKIP_DIRS and not e.startswith(".")]
        dirs = [e for e in entries if os.path.isdir(os.path.join(d, e))]
        files = [e for e in entries if not os.path.isdir(os.path.join(d, e))]
        for e in dirs:
            sub = os.path.join(d, e)
            n = sum(len(fs) for _, _, fs in os.walk(sub))
            lines.append(f"{prefix}{e}/  ({n} files)")
            rec(sub, prefix + "  ", level + 1)
        if level == 1:
            shown = files[:25]
            lines.append(f"{prefix}" + ", ".join(shown) + (" ..." if len(files) > 25 else ""))
    rec(root, "", 1)
    return lines


def readme_links(root):
    urls = []
    for name in ("README.md", "README.rst", "README", "README.txt", "docs/README.md"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            urls += re.findall(r"https?://[^\s)\]>\"']+", read_text(p))
    seen, docish, other = set(), [], []
    for u in urls:
        u = u.rstrip(".,;:")
        if u in seen:
            continue
        seen.add(u)
        if re.search(r"(docs?\.|/docs?(/|$)|readthedocs|pkg\.go\.dev|godoc|docs\.rs|wiki|apache\.org|\.io/|guide|manual|reference|tutorial)", u, re.I) \
                and not re.search(r"(shields\.io|badge|img\.|\.png|\.svg|travis|codecov|circleci|github\.com/.*/(actions|issues|pull))", u, re.I):
            docish.append(u)
        else:
            other.append(u)
    return docish, other


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    root = os.path.abspath(args[0] if args else ".")
    if not os.path.isdir(root):
        sys.exit(f"not a directory: {root}")

    files = walk(root)
    lang_files, lang_lines = Counter(), Counter()
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        lang = LANG_BY_EXT.get(ext)
        if lang:
            lang_files[lang] += 1
            lang_lines[lang] += count_lines(os.path.join(root, f))
    test_files = [f for f in files if re.search(r"(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|(^|/)tests?/|test_[^/]+\.py|_test\.py|_spec\.rb|/tests/)", f)]

    manifests = [m for m in MANIFESTS if os.path.exists(os.path.join(root, m))]
    manifest_text = "\n".join(read_text(os.path.join(root, m), 200_000) for m in manifests)
    nested_manifests = [f for f in files if os.path.basename(f) in ("go.mod", "Cargo.toml", "package.json", "pyproject.toml") and "/" in f][:30]

    entries = [f for f in files if any(p.search(f) for p in ENTRY_PATTERNS)][:40]
    lib_roots = [f for f in files if any(p.search(f) for p in LIB_ROOT_PATTERNS) and f.count("/") <= 1][:10]
    api_files = [f for f in files if any(p.search(f) for p in API_FILE_PATTERNS)]
    storage_files = [f for f in files if any(p.search(f) for p in STORAGE_FILE_PATTERNS)]

    route_hits = Counter()
    src_exts = tuple(LANG_BY_EXT.keys())
    for f in files:
        if f.endswith(src_exts) and f not in test_files:
            n = len(ROUTE_REGEX.findall(read_text(os.path.join(root, f), 300_000)))
            if n:
                route_hits[f] += n

    docs = [d for d in DOC_FILES if os.path.exists(os.path.join(root, d))]
    doc_urls, other_urls = readme_links(root)

    def dep_present(hint):
        return re.search(r"(^|[^A-Za-z0-9])" + re.escape(hint) + r"($|[^A-Za-z0-9])", manifest_text, re.M) is not None

    service_deps = sorted({h for h in SERVICE_DEP_HINTS if dep_present(h)})
    db_deps = sorted({h for h in DB_DEP_HINTS if dep_present(h)})
    cli_deps = sorted({h for h in CLI_DEP_HINTS if dep_present(h)})

    signals = defaultdict(list)
    if any(m.startswith("Dockerfile") or m.startswith("docker-compose") or m in ("Chart.yaml", "Procfile", "skaffold.yaml", "fly.toml", "app.yaml") for m in manifests):
        signals["service"].append("deployment files: " + ", ".join(m for m in manifests if m.startswith(("Dockerfile", "docker-compose", "Chart", "Procfile", "skaffold", "fly", "app.yaml"))))
    if service_deps:
        signals["service"].append("server framework deps: " + ", ".join(service_deps))
    if route_hits:
        signals["service"].append(f"route/rpc registrations in {len(route_hits)} files ({sum(route_hits.values())} hits)")
    if storage_files or db_deps:
        signals["service"].append("storage layer: " + ", ".join((db_deps + [f for f in storage_files if 'migrat' in f or f.endswith('.sql')][:3])[:6]))
    if cli_deps:
        signals["cli"].append("CLI framework deps: " + ", ".join(cli_deps))
    if [e for e in entries if "/cmd/" in e or e.startswith("cmd/")]:
        signals["cli" if cli_deps else "service"].append("cmd/ entry points: " + ", ".join(e for e in entries if "cmd/" in e)[:200])
    if not entries or lib_roots:
        signals["library"].append("no or few executable entry points; exported package root(s): " + (", ".join(lib_roots) or "(language default)"))
    if os.path.exists(os.path.join(root, "go.mod")) and not [e for e in entries if e.endswith("main.go")]:
        signals["library"].append("Go module without main.go")
    if "package.json" in manifests:
        try:
            pj = json.loads(read_text(os.path.join(root, "package.json")))
            if pj.get("bin"):
                signals["cli"].append("package.json bin: " + json.dumps(pj["bin"])[:120])
            if pj.get("main") or pj.get("exports") or pj.get("types"):
                signals["library"].append("package.json main/exports/types present")
            if not pj.get("private") and pj.get("name"):
                signals["library"].append("publishable npm package")
        except Exception:
            pass
    if "Cargo.toml" in manifests:
        ct = read_text(os.path.join(root, "Cargo.toml"))
        if "[lib]" in ct or os.path.exists(os.path.join(root, "src/lib.rs")):
            signals["library"].append("Cargo [lib] / src/lib.rs")
        if "[[bin]]" in ct or os.path.exists(os.path.join(root, "src/main.rs")):
            signals["cli"].append("Cargo [[bin]] / src/main.rs")
    if "pyproject.toml" in manifests or "setup.py" in manifests:
        py = read_text(os.path.join(root, "pyproject.toml")) + read_text(os.path.join(root, "setup.py"))
        if "[project.scripts]" in py or "console_scripts" in py:
            signals["cli"].append("python console_scripts")
        else:
            signals["library"].append("python package without console scripts")
    if len(nested_manifests) >= 3:
        signals["monorepo"].append(f"{len(nested_manifests)} nested manifests, e.g. " + ", ".join(nested_manifests[:4]))

    scored = {k: len(v) for k, v in signals.items() if k != "monorepo"}
    guess = max(scored, key=scored.get) if scored else "unknown"
    if scored and len([k for k, v in scored.items() if v == scored[guess]]) > 1:
        guess = "mixed (" + " / ".join(k for k, v in scored.items() if v == scored[guess]) + ")"

    report = {
        "root": root,
        "git": {"remote": run(["git", "remote", "get-url", "origin"], root), "head": run(["git", "log", "-1", "--format=%h %ad %s", "--date=short"], root), "commits": run(["git", "rev-list", "--count", "HEAD"], root)},
        "size": {"files": len(files), "test_files": len(test_files)},
        "languages": [{"lang": l, "files": lang_files[l], "lines": lang_lines[l]} for l, _ in lang_lines.most_common(8)],
        "manifests": manifests,
        "nested_manifests": nested_manifests,
        "entry_points": entries,
        "library_roots": lib_roots,
        "api_files": api_files[:40],
        "route_files": [f"{f} ({n})" for f, n in route_hits.most_common(25)],
        "storage_files": storage_files[:40],
        "deps": {"server": service_deps, "storage": db_deps, "cli": cli_deps},
        "docs": docs,
        "doc_urls": doc_urls[:20],
        "other_urls": other_urls[:10],
        "kind_signals": dict(signals),
        "kind_guess": guess,
        "tree": tree(root),
    }

    if as_json:
        print(json.dumps(report, indent=2))
        return

    g = report["git"]
    print(f"# Inventory: {os.path.basename(root)}")
    print(f"root: {root}\nremote: {g['remote'] or '-'}\nhead: {g['head'] or '-'}  ({g['commits'] or '?'} commits)")
    print(f"files: {report['size']['files']}  test files: {report['size']['test_files']}")
    print("\n## Languages (lines)")
    for l in report["languages"]:
        print(f"  {l['lang']:<14} {l['files']:>6} files {l['lines']:>9} lines")
    print("\n## Kind guess: " + guess)
    for k, v in signals.items():
        for s in v:
            print(f"  [{k}] {s}")
    print("\n## Manifests: " + (", ".join(manifests) or "-"))
    if nested_manifests:
        print("  nested: " + ", ".join(nested_manifests[:12]) + (" ..." if len(nested_manifests) > 12 else ""))
    print("\n## Entry points")
    for e in entries or ["- (none found)"]:
        print("  " + e)
    if lib_roots:
        print("  library roots: " + ", ".join(lib_roots))
    print("\n## API surface signals")
    for f in api_files[:25] or ["(no api-looking files)"]:
        print("  " + f)
    if route_hits:
        print("  route/rpc registrations: " + ", ".join(report["route_files"][:12]))
    print("\n## Storage signals")
    for f in storage_files[:25] or ["(no storage-looking files)"]:
        print("  " + f)
    if db_deps:
        print("  storage deps: " + ", ".join(db_deps))
    print("\n## Docs")
    print("  in repo: " + (", ".join(docs) or "-"))
    for u in doc_urls:
        print("  doc url: " + u)
    for u in other_urls[:5]:
        print("  other url: " + u)
    print("\n## Layout (depth 2)")
    for line in report["tree"]:
        print("  " + line)


if __name__ == "__main__":
    main()
