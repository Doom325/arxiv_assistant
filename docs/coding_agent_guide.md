# Coding Agent Guide — The Rules

> **Version**: 1.0.0
> **Effective Date**: 2026-03-19
> **Authority**: This document is the single source of truth for all coding rules enforced by the coding agent. Every rule herein is binding. If a rule is not in this document, it is not enforced. If a rule is in this document, it is non-negotiable unless overridden via the documented override mechanism.
> **Companion Document**: [coding_agent_action_loop.md](coding_agent_action_loop.md) — the operational process the agent follows for every task.

---

## Table of Contents

1. [Agent Operating Contract](#1-agent-operating-contract)
2. [Core Action Loop (Summary)](#2-core-action-loop-summary)
3. [Security Rules — CRITICAL Tier](#3-security-rules--critical-tier)
4. [Architecture Rules — CRITICAL Tier](#4-architecture-rules--critical-tier)
5. [Type Safety Rules — MAJOR Tier](#5-type-safety-rules--major-tier)
6. [OOP Design Rules — MAJOR Tier](#6-oop-design-rules--major-tier)
7. [Functional Programming Rules — MAJOR Tier](#7-functional-programming-rules--major-tier)
8. [Performance Rules — MAJOR Tier](#8-performance-rules--major-tier)
9. [Async & Concurrency Rules — MAJOR Tier](#9-async--concurrency-rules--major-tier)
10. [Testing Rules — MAJOR Tier](#10-testing-rules--major-tier)
11. [Production Readiness Rules — MAJOR Tier](#11-production-readiness-rules--major-tier)
12. [API & Service Contract Rules — MAJOR Tier](#12-api--service-contract-rules--major-tier)
13. [Import Hygiene Rules — MINOR Tier](#13-import-hygiene-rules--minor-tier)
14. [Formatting & Documentation Rules — MINOR Tier](#14-formatting--documentation-rules--minor-tier)
15. [Self-Review Protocol](#15-self-review-protocol)
16. [Hard Limits Quick Reference Table](#16-hard-limits-quick-reference-table)

---

## 1. Agent Operating Contract

### 1.1 Identity

The coding agent is an autonomous software engineer. It receives a task, writes production-quality code that satisfies every rule in this document, verifies its own output, and reports what it did. It does not ship code that it has not self-reviewed.

### 1.2 Behavioral Rules

**`[CRITICAL] RULE: Never guess.`** If the agent lacks context — unclear requirements, missing type information, ambiguous architecture boundaries, unknown business rules — it MUST stop and ask. It MUST NOT invent behavior, assume intent, or fill gaps with defaults.

**`[CRITICAL] RULE: Be deterministic.`** Given the same task and the same codebase state, the agent MUST produce the same output. No randomness. No "it depends" without explicit, enumerated conditions.

**`[CRITICAL] RULE: Follow existing patterns.`** Before writing new code, the agent MUST read existing code in the same module/layer and match its conventions — naming, structure, error handling patterns, test organization. Consistency with the codebase takes priority over personal preference.

**`[MAJOR] RULE: Use agent-first language.`** Express all conditions as measurable, machine-checkable predicates. Replace subjective words ("clean," "nice," "simple," "elegant") with concrete thresholds ("function body ≤ 50 lines," "cyclomatic complexity ≤ 10," "zero external dependencies in this module").

**`[MAJOR] RULE: Every change has a reason.`** The agent MUST be able to articulate why each line of code exists. "Because I felt like it" is never valid. Valid reasons include: satisfying a requirement, fixing a bug, enforcing a rule from this document, maintaining consistency with an existing pattern.

**`[MAJOR] RULE: Minimize blast radius.`** Change only what the task requires. Do not refactor unrelated code. Do not add features that were not requested. Do not "improve" adjacent code unless the task explicitly asks for it.

### 1.3 Execution Model

The agent operates in a strict sequential loop. Every step must complete before the next begins. The full process is defined in the companion document ([coding_agent_action_loop.md](coding_agent_action_loop.md)). The summary is in Section 2 below.

### 1.4 Severity Tiers

| Severity | Scope | Consequence |
|----------|-------|-------------|
| **CRITICAL** | Security vulnerabilities, data corruption, architectural boundary violations | A single CRITICAL violation blocks the entire change. The agent MUST NOT submit code containing a CRITICAL violation under any circumstance. |
| **MAJOR** | Type safety gaps, SOLID violations, structural design flaws, missing tests, performance anti-patterns | These require rework. The agent MUST fix all MAJOR violations before submission. |
| **MINOR** | Style, naming, docstring formatting, import ordering | These are cheap to fix. The agent MUST fix them proactively. |
| **WARNING** | Best practice gaps with no immediate harm | The agent MUST fix these. A warning pattern repeated 3+ times in the same changeset escalates to MAJOR. |

### 1.5 Override Mechanism

If a rule MUST be violated due to external constraints (third-party API limitations, legacy compatibility, explicit user instruction):

1. Document the specific rule being overridden (reference the rule ID from this document).
2. Provide explicit justification.
3. Limit the scope of the override to the minimum necessary.
4. Add a code comment at the violation site: `# OVERRIDE: <rule> — <reason>`.
5. Report the override in the final summary.

---

## 2. Core Action Loop (Summary)

This is the abbreviated version. See [coding_agent_action_loop.md](coding_agent_action_loop.md) for the full process with entry/exit conditions and checklists.

| Step | Name | Purpose |
|------|------|---------|
| 0 | **Receive & Validate** | Parse the task. Confirm all context is present. If not, stop and ask. |
| 1 | **Explore & Understand** | Read existing code. Find patterns. Identify boundaries. |
| 2 | **Plan** | Design the approach. List files to change. Identify risks. |
| 3 | **Implement** | Write the code following every rule in this document. |
| 4 | **Self-Review** | Check every line against the rules. Automated checks first, then manual. |
| 5 | **Test** | Write and run tests. Verify coverage meets thresholds. |
| 6 | **Report** | Summarize changes, flag decisions, note trade-offs. |

---

## 3. Security Rules — CRITICAL Tier

Every rule in this section has zero tolerance. A single violation produces a CRITICAL finding and blocks submission.

### 3.1 Injection Prevention

**`[CRITICAL] SEC-01: Use parameterized queries exclusively.`** Never interpolate variables into SQL strings. Use ORM query builders (SQLAlchemy, Django ORM) or `$1`-style placeholders.

```python
# NON-COMPLIANT — SQL injection
query = f"SELECT * FROM papers WHERE id = '{paper_id}'"
cursor.execute(query)

# COMPLIANT — parameterized
cursor.execute("SELECT * FROM papers WHERE id = %s", (paper_id,))
# COMPLIANT — ORM
paper = session.query(Paper).filter(Paper.id == paper_id).first()
```

**`[CRITICAL] SEC-02: Never use shell=True with variable input.`** Use `subprocess.run()` with a list of arguments.

```python
# NON-COMPLIANT — shell injection
subprocess.run(f"convert {filename} output.pdf", shell=True)

# COMPLIANT
subprocess.run(["convert", filename, "output.pdf"], check=True)
```

**`[CRITICAL] SEC-03: Never use eval() or exec().`** Unless there is explicit, documented justification AND the input is provably trusted AND an OVERRIDE comment is present.

**`[CRITICAL] SEC-04: Never deserialize untrusted data with pickle.`** Use JSON, MessagePack, or Protobuf for data from external sources.

### 3.2 Configuration Safety

**`[CRITICAL] SEC-05: Always use yaml.safe_load().`** Never bare `yaml.load()`. Always `yaml.safe_load()` or `yaml.load(stream, Loader=yaml.SafeLoader)`.

```python
# NON-COMPLIANT
config = yaml.load(open("config.yml"))

# COMPLIANT
config = yaml.safe_load(open("config.yml"))
```

**`[CRITICAL] SEC-06: No hardcoded credentials.`** Secrets come from environment variables or a secrets manager. Never commit API keys, passwords, tokens, or connection strings in source code.

```python
# NON-COMPLIANT
API_KEY = "sk-abc123def456"

# COMPLIANT
API_KEY = os.environ["API_KEY"]
# or
API_KEY = settings.api_key  # loaded via Pydantic BaseSettings from env
```

**`[CRITICAL] SEC-07: No debug=True in production code.`** Debug mode MUST be gated behind an environment check. `DEBUG = os.getenv("DEBUG", "false").lower() == "true"`.

### 3.3 Input Validation

**`[CRITICAL] SEC-08: Prevent path traversal.`** Validate and sanitize all file paths. Use `pathlib.Path.resolve()` and confirm the resolved path starts with the expected root directory.

```python
# NON-COMPLIANT
file_path = base_dir / user_input
content = file_path.read_text()

# COMPLIANT
file_path = (base_dir / user_input).resolve()
if not str(file_path).startswith(str(base_dir.resolve())):
    raise ValueError("Path traversal detected")
content = file_path.read_text()
```

### 3.4 Dependency Safety

**`[MAJOR] SEC-09: Pin dependency versions.`** Use specific versions or bounded ranges (`>=1.2,<2.0`). No unbounded `>=` without an upper limit.

**`[WARNING] SEC-10: pip-audit or safety should be present as a CI/CD blocking gate for dependency vulnerability scanning.`**

---

## 4. Architecture Rules — CRITICAL Tier

Boundary violations are CRITICAL. Structural preferences within layers are MAJOR.

### 4.1 Clean Architecture — Dependency Direction

**`[CRITICAL] ARCH-01: Dependencies point inward only.`**

```
External (frameworks, DB drivers, HTTP clients)
    ↓ depends on
Interface Adapters (routers, repositories, gateways)
    ↓ depends on
Application Services (use cases, orchestration)
    ↓ depends on
Domain (entities, value objects, domain services, protocols)
```

No layer may import from a layer above it. The domain layer MUST NOT import from application, adapter, or external layers.

**`[CRITICAL] ARCH-02: Domain layer has zero framework imports.`** The domain layer MUST NOT import FastAPI, SQLAlchemy, Django, httpx, or any infrastructure framework. It contains only: pure Python, dataclasses, protocols, enums, and domain logic.

```python
# NON-COMPLIANT — domain entity importing infrastructure
from sqlalchemy import Column, String
from fastapi import HTTPException

class Paper:
    ...

# COMPLIANT — pure domain
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    title: str
    abstract: str
```

**`[CRITICAL] ARCH-03: Application services receive dependencies via injection.`** Use cases MUST NOT call constructors for DB sessions, HTTP clients, or external services directly. They receive them as parameters or through a dependency injection framework.

```python
# NON-COMPLIANT
class SearchPapers:
    def execute(self, query: str) -> list[Paper]:
        session = Session()  # direct instantiation
        return session.query(PaperModel).filter(...).all()

# COMPLIANT
class SearchPapers:
    def __init__(self, repo: PaperRepository) -> None:
        self._repo = repo

    def execute(self, query: str) -> list[Paper]:
        return self._repo.search(query)
```

### 4.2 Structural Patterns

**`[MAJOR] ARCH-04: Use the Repository Protocol pattern.`** Define a `Repository` protocol in the domain or application layer. Implement it in the infrastructure layer. Inject the implementation.

**`[MAJOR] ARCH-05: Use Unit of Work for multi-repo transactions.`** When a use case touches multiple repositories in a single transaction, use a Unit of Work pattern to manage the transaction boundary.

**`[MAJOR] ARCH-06: No concrete imports in business logic.`** Business logic modules MUST depend on abstractions (protocols), not concrete implementations. Concrete wiring happens at the composition root (e.g., `main.py`, dependency injection container).

**`[MAJOR] ARCH-07: Use cases must not contain presentation logic.`** No JSON serialization, HTTP status code construction, HTML rendering, or format-specific output in the application/use case layer.

**`[MAJOR] ARCH-08: Adapter layer must not contain business rules.`** Conditional logic based on domain state, domain calculations, or validation beyond schema validation belongs in the domain or use case layer, not in adapters/routers.

**`[MAJOR] ARCH-09: Adapter layer must not access the database directly.`** All data access must route through a Repository abstraction.

---

## 5. Type Safety Rules — MAJOR Tier

### 5.1 Annotations

**`[MAJOR] TYPE-01: Full type annotations on every function.`** Every function signature MUST have type annotations on all parameters and the return type. No exceptions.

```python
# NON-COMPLIANT
def process_paper(paper, options):
    ...

# COMPLIANT
def process_paper(paper: Paper, options: ProcessingOptions) -> ProcessingResult:
    ...
```

**`[MAJOR] TYPE-02: No untyped Any unless unavoidable and documented.`** If `Any` is required (e.g., wrapping an untyped third-party library), add a comment: `# TYPE: Any required because <reason>`.

**`[MAJOR] TYPE-03: Code MUST pass mypy --strict.`** This means: no implicit `Any`, no untyped defs, no missing return types, no untyped decorators.

### 5.2 Type Constructs

**`[MAJOR] TYPE-04: Use Protocol over ABC for interfaces.`** Prefer `typing.Protocol` (structural subtyping) over `abc.ABC` (nominal subtyping) unless shared implementation is needed in the base class.

**`[MAJOR] TYPE-05: Use T | None, not Optional[T].`** Use the union syntax (Python 3.10+). It is clearer and composes better in complex union types.

```python
# NON-COMPLIANT
from typing import Optional
def find_paper(arxiv_id: str) -> Optional[Paper]:
    ...

# COMPLIANT
def find_paper(arxiv_id: str) -> Paper | None:
    ...
```

### 5.3 Data Container Selection

**`[MAJOR] TYPE-06: Use the correct data container.`**

| Container | Use When |
|-----------|----------|
| `TypedDict` | Typed dictionary shapes (JSON-like data, backwards compatibility with dict-accepting APIs) |
| `NamedTuple` | Immutable, lightweight data; when you need tuple unpacking |
| `dataclass` | Mutable structured data with methods |
| `Pydantic BaseModel` | Validation at boundaries (API input/output, config parsing, external data) |

Do not use a plain `dict` when the shape is known. Do not use a `dataclass` at an API boundary where validation is needed — use Pydantic.

**`[MAJOR] TYPE-07: No forward-reference string literals (e.g., "UserModel") when from __future__ import annotations is present or when the actual type is importable in scope.`**

**`[MAJOR] TYPE-08: No tight coupling via concrete class inheritance across module boundaries.`** If removing the parent class requires changes beyond updating the class definition line, the dependency is too tight. Use Protocol instead.

**`[MINOR] TYPE-09: Do not mix Optional[T] and T | None in the same file.`** Pick one style and use it consistently.

---

## 6. OOP Design Rules — MAJOR Tier

> **Scope**: OOP rules apply to service classes, repositories, and adapters. For pure data transformation functions, see the [FP section](#7-functional-programming-rules--major-tier).

### 6.1 SOLID Principles — All Five, Non-Negotiable

**`[MAJOR] OOP-01: Single Responsibility Principle (SRP).`** A class has one reason to change. If you can describe a class's purpose with the word "and," it needs splitting.

```python
# NON-COMPLIANT — two responsibilities
class PaperService:
    def fetch_from_arxiv(self, arxiv_id: str) -> Paper: ...
    def send_digest_email(self, papers: list[Paper]) -> None: ...

# COMPLIANT — separated
class ArxivFetcher:
    def fetch(self, arxiv_id: str) -> Paper: ...

class DigestEmailSender:
    def send(self, papers: list[Paper]) -> None: ...
```

**`[MAJOR] OOP-02: Open/Closed Principle (OCP).`** Classes are open for extension, closed for modification. Use protocols, the strategy pattern, or plugin architectures to add behavior without modifying existing code.

**`[MAJOR] OOP-03: Liskov Substitution Principle (LSP).`** Subtypes MUST be substitutable for their base types without altering program correctness. A subclass MUST NOT strengthen preconditions or weaken postconditions.

**`[MAJOR] OOP-04: Interface Segregation Principle (ISP).`** No client should depend on methods it does not use. Prefer small, focused protocols over large, monolithic ones.

**`[MAJOR] OOP-05: Dependency Inversion Principle (DIP).`** High-level modules MUST NOT import low-level modules directly. Both should depend on abstractions (protocols).

### 6.2 Composition and Structure

**`[MAJOR] OOP-06: Composition over inheritance.`** Default to composing objects. Use inheritance only for genuine "is-a" relationships with shared behavior.

**`[MAJOR] OOP-07: Inheritance depth ≤ 3 levels.`** If the class hierarchy exceeds 3 levels, flatten it using composition.

**`[MAJOR] OOP-08: Domain dataclasses use frozen=True.`** Domain value objects MUST be immutable.

```python
@dataclass(frozen=True)
class ArxivId:
    value: str
```

**`[MAJOR] OOP-09: High-volume dataclasses use slots=True.`** Objects created in large quantities (e.g., search results, batch processing items) MUST use `__slots__` for memory efficiency.

**`[MAJOR] OOP-10: ≥ 4 parameters require kw_only=True.`** Dataclasses and functions with 4 or more parameters MUST use keyword-only arguments to prevent positional errors.

```python
# NON-COMPLIANT
@dataclass
class SearchQuery:
    text: str
    category: str
    after: str
    before: str
    limit: int

# COMPLIANT
@dataclass(kw_only=True)
class SearchQuery:
    text: str
    category: str
    after: str
    before: str
    limit: int
```

**`[MAJOR] OOP-11: Use context managers for all resources.`** Files, DB connections, locks, HTTP sessions — always use `with` statements or `contextlib.contextmanager`. Never leave resources to garbage collection.

**`[MAJOR] OOP-12: Protocols must be stateless.`** Protocols define behavioral contracts. They MUST NOT declare instance variables or mutable state. If shared state is needed, use an ABC instead.

**`[MAJOR] OOP-13: Mixins must be stateless.`** Mixins provide behavior, not state. A mixin class MUST NOT define `__init__` or instance variables. If it needs state, it should be a composed dependency instead.

**`[MAJOR] OOP-14: No isinstance() in business logic for type branching.`** Using `isinstance()` to branch on type in business logic is a Liskov Substitution Principle violation signal. Use polymorphism (method dispatch) or `functools.singledispatch` instead.

**`[MAJOR] OOP-15: __str__ for human presentation, __repr__ for debugging.`** `__str__` returns a human-readable representation. `__repr__` must return an eval()-reproducible string in the format `ClassName(field1=value1, field2=value2)`. Do not conflate them.

**`[MAJOR] OOP-16: No operator overloading on non-numeric/non-ordered domain types.`** Operator overloading (`__add__`, `__mul__`, `__lt__`, etc.) is appropriate for numeric types, ordered types, and collection types. Do not overload operators on general domain entities — it obscures intent.

**`[MAJOR] OOP-17: Core business logic classes must have at least one abstraction point.`** A Protocol they satisfy or an abstract method they declare — that allows behavior to be extended without modification.

**`[MAJOR] OOP-18: No raise NotImplementedError stubs to satisfy an oversized interface.`** If a class cannot implement all methods of a Protocol, the Protocol is too large and must be split (Interface Segregation Principle).

**`[WARNING] OOP-19: Cross-cutting capabilities (caching, logging, audit trails, serialization) should not be duplicated across multiple classes.`** Use Mixin composition or delegation to a shared collaborator.

**`[WARNING] OOP-20: __getitem__ or __len__ should not return a reference to an internal private data structure.`** Return a copy or expose a stable collection interface.

---

## 7. Functional Programming Rules — MAJOR Tier

> **Scope**: FP rules apply to inner domain data transformations — pure functions that compute, map, filter, or transform data. For service/class structure, see the [OOP section](#6-oop-design-rules--major-tier).

**`[MAJOR] FP-01: Pure functions have no side effects.`** A pure function's output depends only on its inputs. It does not modify external state, write to disk, or call APIs. Label impure functions clearly by placing I/O at the boundaries.

**`[MAJOR] FP-02: ≥ 3 sequential transforms require pipeline composition.`** When you have 3 or more sequential data transformations, compose them using a pipeline pattern (`functools.reduce`, a pipeline utility, or generator chaining). Do not nest function calls 3+ levels deep.

```python
# NON-COMPLIANT — deeply nested
result = format_output(classify(extract_entities(parse_pdf(download(url)))))

# COMPLIANT — pipeline
pipeline = [download, parse_pdf, extract_entities, classify, format_output]
result = functools.reduce(lambda data, fn: fn(data), pipeline, url)
```

**`[MAJOR] FP-03: No lru_cache on impure functions.`** Never cache a function that depends on external state (time, database, network, environment variables). Cached impure functions return stale and incorrect results.

**`[MAJOR] FP-04: ≥ 4 type-dispatch branches require singledispatch.`** When dispatching on type with 4 or more branches, use `functools.singledispatch` instead of if-elif chains.

**`[MAJOR] FP-05: ≥ 3 distinct data shapes require match/case.`** Use structural pattern matching when checking 3 or more distinct data shapes. Cleaner and more extensible than if-elif chains.

**`[WARNING] FP-06: Use Result types over None chains.`** Instead of returning `None` to signal failure (leading to `if x is not None` cascades), use a Result type (`Ok | Err`), raise domain-specific exceptions, or use a similar discriminated union pattern.

**`[MAJOR] FP-07: No logging/print/filesystem writes inside pure transformation functions.`** Pure functions must remain pure. Logging, printing, and filesystem writes are side effects. Move them to the calling code at the I/O boundary.

**`[WARNING] FP-08: functools.reduce requires a # rationale: comment.`** `reduce` is hard to read for most developers. Every use MUST include an inline comment explaining what the reduction computes and why `reduce` was chosen over an explicit loop.

**`[WARNING] FP-09: Multi-line lambdas should be extracted to named functions.`** If a lambda spans multiple lines (via line continuation or nested expressions), extract it to a named function with a descriptive name and a docstring.

**`[WARNING] FP-10: Recommend @functools.cache for pure functions called 2+ times with same args.`** If a pure function is called multiple times with the same arguments in a hot path, apply `@functools.cache` (or `@functools.lru_cache`) to avoid redundant computation.

**`[WARNING] FP-11: When >=3 sequential operations on the same data structure are implemented as separate assignment statements with intermediate mutable variables, consider refactoring to functional composition (e.g., toolz.pipe).`**

**`[WARNING] FP-12: Module-level variables should not be mutated across >=3 function calls in a data transformation pipeline.`** Pass state as explicit function arguments instead.

**`[MAJOR] FP-13: Mutable dict or list objects must not be used as shared state across threads without synchronization primitives (threading.Lock).`** Use immutable data structures, frozenset, tuple, or guarded mutable state.

**`[MAJOR] FP-14: No >=3 levels of for-loop nesting in data transformation functions.`** Decompose using helper functions or functional composition. This is stricter than the general nesting limit (PERF-04, ≤ 4 levels) because deeply nested loops in transformations are always decomposable.

---

## 8. Performance Rules — MAJOR Tier

### 8.1 Code Complexity Limits

**`[MAJOR] PERF-01: Cyclomatic complexity ≤ 10 per function.`** If a function has more than 10 independent paths, decompose it into smaller functions.

**`[MINOR] PERF-02: Function body ≤ 50 lines.`** Measured excluding docstrings and blank lines. If longer, extract helper functions.

**`[MINOR] PERF-03: File ≤ 500 lines.`** If a file exceeds 500 lines, it likely has multiple responsibilities. Split it into focused modules.

**`[MAJOR] PERF-04: Nesting depth ≤ 4 levels.`** No more than 4 levels of indentation. Use early returns, guard clauses, and function extraction to flatten logic.

```python
# NON-COMPLIANT — 5 levels of nesting
def process(papers):
    for paper in papers:
        if paper.has_pdf:
            for section in paper.sections:
                if section.is_relevant:
                    for entity in section.entities:
                        if entity.type == "model":
                            yield entity

# COMPLIANT — flattened with extraction and guards
def _relevant_entities(paper: Paper) -> Iterator[Entity]:
    if not paper.has_pdf:
        return
    for section in paper.sections:
        if not section.is_relevant:
            continue
        yield from (e for e in section.entities if e.type == "model")

def process(papers: Iterable[Paper]) -> Iterator[Entity]:
    for paper in papers:
        yield from _relevant_entities(paper)
```

### 8.2 Query and Data Patterns

**`[CRITICAL] PERF-05: No N+1 queries.`** N+1 queries cause unbounded database load that scales linearly with data size. When loading related objects, use joins or eager loading. Never issue one query per item in a loop.

```python
# NON-COMPLIANT — N+1
papers = session.query(Paper).all()
for paper in papers:
    authors = session.query(Author).filter(Author.paper_id == paper.id).all()

# COMPLIANT — eager load
papers = session.query(Paper).options(joinedload(Paper.authors)).all()
```

**`[MAJOR] PERF-06: No unbounded .all() without LIMIT.`** Every query that could return an unbounded result set MUST have a `LIMIT` (or equivalent pagination mechanism).

**`[MAJOR] PERF-07: Generator over list comprehension when only iterating.`** If you only iterate once and do not need random access or `len()`, use a generator expression or `yield`.

**`[MAJOR] PERF-08: No lazy-loaded ORM relationships accessed inside loops.`** Use `joinedload()`, `selectinload()`, or `subqueryload()` to eagerly load relationships when iterating.

```python
# NON-COMPLIANT — lazy load triggers N queries inside loop
papers = session.query(Paper).all()
for paper in papers:
    print(paper.authors)  # each access fires a separate SELECT

# COMPLIANT — eager load with joinedload
from sqlalchemy.orm import joinedload

papers = (
    session.query(Paper)
    .options(joinedload(Paper.authors))
    .all()
)
for paper in papers:
    print(paper.authors)  # already loaded, no additional queries
```

**`[MAJOR] PERF-09: Lazy imports for heavy modules.`** If a module is expensive to import (e.g., `torch`, `tensorflow`, `pandas`) and only used conditionally, import it inside the function that uses it.

---

## 9. Async & Concurrency Rules — MAJOR Tier

**`[CRITICAL] ASYNC-01: No blocking I/O in async def.`** Blocking the event loop halts all concurrent work in the process. If a function is `async`, every I/O call within it MUST be awaited. Blocking calls (`requests.get()`, synchronous file I/O on network filesystems) MUST be run via `asyncio.to_thread()`.

```python
# NON-COMPLIANT — blocking call in async context
async def fetch_paper(url: str) -> bytes:
    return requests.get(url).content  # blocks the event loop

# COMPLIANT
async def fetch_paper(url: str) -> bytes:
    response = await httpx.AsyncClient().get(url)
    return response.content

# COMPLIANT — wrapping unavoidable sync call
async def read_pdf(path: Path) -> bytes:
    return await asyncio.to_thread(path.read_bytes)
```

**`[CRITICAL] ASYNC-02: No nested asyncio.run().`** `asyncio.run()` creates a new event loop. Calling it inside an already-running loop raises `RuntimeError`. Nested event loops crash the process with RuntimeError. Use `await` instead.

**`[MAJOR] ASYNC-03: Store create_task() results.`** Always assign the return value of `asyncio.create_task()` to a variable. Unassigned tasks can be garbage collected before completion.

```python
# NON-COMPLIANT — task may be GC'd
asyncio.create_task(process_paper(paper_id))

# COMPLIANT
task = asyncio.create_task(process_paper(paper_id))
background_tasks.add(task)
task.add_done_callback(background_tasks.discard)
```

**`[MAJOR] ASYNC-04: Handle task exceptions.`** Either `await` the task, use `task.add_done_callback()`, or use `asyncio.TaskGroup` (Python 3.11+). Unhandled task exceptions are silently swallowed.

**`[MAJOR] ASYNC-05: Use asyncio.Lock for shared mutable state in async code.`** Do not use `threading.Lock` in async code. It blocks the event loop.

**`[MAJOR] ASYNC-06: An async def function with no await expression must have a docstring explaining why it is async without awaiting.`** For example, an async interface stub. Otherwise, the function should not be async.

**`[WARNING] ASYNC-07: Synchronous and asynchronous code mixed in the same module without a clean bridge layer (e.g., sync_-prefixed wrapper functions) is a code smell.`** Separate sync and async interfaces.

---

## 10. Testing Rules — MAJOR Tier

**`[MAJOR] TEST-01a: Coverage ≥ 80% overall.`** This is a hard minimum, not a target.

**`[CRITICAL] TEST-01b: Coverage ≥ 95% for the domain layer.`** Domain and business logic is the highest-value code. Gaps here are CRITICAL because domain bugs propagate to every consumer.

**`[CRITICAL] TEST-02: No live I/O in unit tests.`** Non-deterministic tests undermine the entire test suite — flaky tests erode trust and mask real failures. Unit tests MUST NOT hit the network, filesystem, or database. Mock all I/O boundaries. Integration tests that require I/O must be marked and separated.

**`[MAJOR] TEST-03: No shared mutable state between tests.`** Each test MUST be independent. Use fixtures for setup. Never rely on test execution order. Never use module-level mutable state that tests modify.

**`[MAJOR] TEST-04: Mocks use spec=.`** When mocking, always use `spec=SomeProtocol` or `spec=SomeClass` so the mock enforces the real interface. Unspec'd mocks silently accept any attribute access, hiding bugs.

```python
# NON-COMPLIANT — mock accepts anything
mock_repo = MagicMock()
mock_repo.find_by_nonexistent_method()  # no error, hides bug

# COMPLIANT — mock enforces interface
mock_repo = MagicMock(spec=PaperRepository)
mock_repo.find_by_nonexistent_method()  # raises AttributeError
```

**`[MINOR] TEST-05: Test naming: test_<subject>_<condition>_<expected_outcome>.`**

```python
# NON-COMPLIANT
def test_search(): ...

# COMPLIANT
def test_search_empty_query_returns_400(): ...
def test_search_valid_query_returns_ranked_results(): ...
```

**`[MAJOR] TEST-06: Arrange-Act-Assert structure.`** Every test has three clear phases, separated by blank lines if needed.

**`[MAJOR] TEST-07: Test behavior, not implementation.`** Tests verify observable outcomes (return values, state changes, raised exceptions), not internal method calls — unless the side effect IS the behavior being tested.

**`[MAJOR] TEST-08: Test files must be in tests/ mirroring source tree.`** Test files live in a `tests/` directory that mirrors the source tree structure. `backend/services/search.py` is tested by `backend/tests/services/test_search.py`.

**`[MAJOR] TEST-09: Every test function must contain at least one assertion.`** A test without an assertion proves nothing. Every test function MUST call at least one `assert` statement or `pytest.raises`.

**`[MAJOR] TEST-10: Session/module-scoped fixtures must not mutate shared state.`** Fixtures with `scope="session"` or `scope="module"` are shared across tests. They MUST NOT modify mutable state that other tests depend on. Use `scope="function"` for fixtures that mutate.

**`[WARNING] TEST-11: 3+ near-identical test functions should use @pytest.mark.parametrize.`** When three or more test functions differ only in input data and expected output, consolidate them into a single parametrized test to reduce duplication and make it easier to add new cases.

**`[MAJOR] TEST-12: Every public function in the application/use case layer must have at least one test covering it (non-zero test coverage).`**

**`[MINOR] TEST-13: Test files must import source modules via the installed package path (e.g., from mypackage.users import ...), not relative paths.`**

---

## 11. Production Readiness Rules — MAJOR Tier

**`[MAJOR] PROD-01: Use structured JSON logging.`** Use `structlog` or `python-json-logger`. Every log entry MUST be a parseable JSON object with consistent fields: `timestamp`, `level`, `message`, `context`.

**`[MAJOR] PROD-02: No PII in logs.`** Never log email addresses, passwords, tokens, IP addresses (unless required and documented), or user-identifiable data.

**`[MAJOR] PROD-03: Use Pydantic BaseSettings for configuration.`** Load and validate configuration from environment variables using `pydantic_settings.BaseSettings`. This provides type safety and validation at startup.

**`[MAJOR] PROD-04: Fail loudly on missing config.`** If a required configuration value is absent, raise an error at startup. Do not fall back to a silent default — this hides deployment mistakes.

```python
# NON-COMPLIANT — silent default hides missing config
API_KEY = os.getenv("API_KEY", "")

# COMPLIANT — fails at startup
class Settings(BaseSettings):
    api_key: str  # no default = required = error if missing
```

**`[MAJOR] PROD-05: Bounded retries with exponential backoff.`** When retrying I/O operations: use exponential backoff with jitter, set a maximum retry count of 3-5, never retry indefinitely.

**`[MAJOR] PROD-06: No bare except.`** Always catch a specific exception type. `except Exception` is acceptable as a last resort with logging. `except:` (bare) catches `KeyboardInterrupt` and `SystemExit`, which MUST propagate.

```python
# NON-COMPLIANT — catches KeyboardInterrupt
try:
    process()
except:
    log.error("failed")

# NON-COMPLIANT — too broad without logging
try:
    process()
except Exception:
    pass

# COMPLIANT
try:
    process()
except ProcessingError as e:
    log.error("processing_failed", error=str(e), paper_id=paper_id)
    raise
```

**`[MAJOR] PROD-07: Expose health checks.`** Every service MUST expose a `/health` endpoint that verifies connectivity to critical dependencies (database, cache, external APIs).

**`[MAJOR] PROD-08: Handle graceful shutdown.`** Handle `SIGTERM` and `SIGINT`. Finish in-progress work, close connections, then exit cleanly.

**`[MAJOR] PROD-09: Auth required on /debug, /admin, /internal, /metrics endpoints.`** Any endpoint under `/debug`, `/admin`, `/internal`, or `/metrics` MUST require authentication. Exposing these without auth leaks internal state and creates attack surface.

**`[MAJOR] PROD-10: os.environ.get() without None-guard is prohibited.`** Do not use `os.environ.get("KEY")` and then pass the result without checking for `None`. Use `os.environ["KEY"]` (which raises `KeyError` if missing) or `pydantic_settings.BaseSettings` for validated configuration.

**`[MAJOR] PROD-11: Multi-step database mutations must be wrapped in a transaction.`** A partial failure must not leave the database in an inconsistent state. Use Unit of Work or explicit transaction blocks.

**`[WARNING] PROD-12: Log messages should be filterable by service name, log level, and ISO 8601 timestamp via standard log aggregation tooling.`**

---

## 12. API & Service Contract Rules — MAJOR Tier

**`[MAJOR] API-01: Use correct HTTP status codes.`** Every endpoint MUST return the semantically correct status code:

| Operation | Status Code |
|-----------|-------------|
| Successful creation | `201 Created` |
| Successful deletion (no body) | `204 No Content` |
| Resource not found | `404 Not Found` |
| Duplicate resource conflict | `409 Conflict` |
| Validation failure | `422 Unprocessable Entity` |

Do not return `200 OK` for all success cases. Do not return `500` for client errors.

**`[MAJOR] API-02: Noun-based resource paths only.`** URLs MUST use nouns, not verbs. The HTTP method conveys the action.

```
# NON-COMPLIANT
POST /api/searchPapers
GET  /api/getPaper/123
POST /api/deletePaper/123

# COMPLIANT
POST /api/papers/search     (or GET /api/papers?q=...)
GET  /api/papers/123
DELETE /api/papers/123
```

**`[MAJOR] API-03: API versioning required.`** All API endpoints MUST be versioned via URL prefix (`/api/v1/...`). This allows breaking changes to be introduced under a new version without disrupting existing clients.

**`[MAJOR] API-04: No breaking changes without version increment.`** Removing a field, renaming a field, changing a field's type, or removing an endpoint are breaking changes. They MUST NOT be made to an existing API version. Introduce a new version instead.

**`[MAJOR] API-05: Response envelope consistency.`** All API responses MUST follow a consistent envelope structure within a version. If one endpoint returns `{"data": [...], "meta": {...}}`, all list endpoints in that version MUST use the same shape.

---

## 13. Import Hygiene Rules — MINOR Tier

**`[MAJOR] IMP-01: No wildcard imports outside __init__.py.`** `from module import *` makes dependencies invisible and breaks static analysis. Use explicit imports.

**`[CRITICAL] IMP-02: No circular imports.`** Circular imports can cause runtime failures (ImportError, partially initialized modules). If module A imports module B and module B imports module A, restructure. Common fixes:
- Extract shared types into a third module.
- Use `TYPE_CHECKING` for type-only imports.
- Invert the dependency via a protocol.

**`[MINOR] IMP-03: Import ordering: stdlib, third-party, local.`** Separated by blank lines. Use `isort` to automate. Configuration: `isort --profile black`.

**`[MAJOR] IMP-04: No private submodule imports from external packages.`** Do not import `_internal`, `_utils`, or any underscore-prefixed module from third-party libraries. These are not part of the public API and break without notice.

**`[MINOR] IMP-05: # noqa without inline explanation is a violation.`** Every `# noqa` comment MUST include a brief explanation of why the suppression is necessary. Bare `# noqa` hides problems silently.

```python
# NON-COMPLIANT
from module import *  # noqa

# COMPLIANT
from module import *  # noqa: F403 — re-exporting public API in __init__.py
```

**`[MINOR] IMP-06: # type: ignore without inline explanation is a violation.`** Every `# type: ignore` comment MUST include a brief explanation. Bare `# type: ignore` suppresses all type errors on the line and masks real bugs.

```python
# NON-COMPLIANT
result = untyped_lib.call()  # type: ignore

# COMPLIANT
result = untyped_lib.call()  # type: ignore[no-untyped-call] — library has no stubs
```

**`[MAJOR] IMP-07: Wildcard imports in __init__.py must be accompanied by an explicit __all__ list in the source module being imported from.`**

**`[MINOR] IMP-08: from __future__ import annotations must be used consistently across all files in the same package.`** Do not mix files with and without it.

**`[WARNING] IMP-09: If total # noqa and # type: ignore overrides exceed 5% of non-blank, non-comment source lines, the override density is too high.`** Reduce suppressions.

---

## 14. Formatting & Documentation Rules — MINOR Tier

**`[MINOR] FMT-01: 4-space indent, no tabs.`** Universal Python standard. Configure your formatter accordingly.

**`[MINOR] FMT-02: Lines ≤ 88 characters.`** Compatible with Black formatter defaults.

**`[MINOR] FMT-03: Google-style docstrings.`** Include `Args:`, `Returns:`, `Raises:` sections. Every public function and every public class MUST have a docstring.

```python
def search_papers(
    query: str,
    *,
    category: str | None = None,
    limit: int = 20,
) -> list[Paper]:
    """Search the paper library using hybrid semantic + keyword search.

    Args:
        query: The search query string. Supports metadata prefixes
            (e.g., "category:cs.AI", "after:2024-01-01").
        category: Optional arXiv category filter.
        limit: Maximum number of results to return.

    Returns:
        List of papers ranked by relevance score, most relevant first.

    Raises:
        SearchError: If the search backend is unavailable.
        ValueError: If query is empty.
    """
```

**`[MINOR] FMT-04: Comments explain WHY, not WHAT.`** The code says what it does. Comments explain the reasoning, constraints, or non-obvious decisions behind it.

```python
# NON-COMPLIANT — restates the code
# increment counter by 1
counter += 1

# COMPLIANT — explains why
# arXiv rate-limits to 1 request per 3 seconds; wait before next call
await asyncio.sleep(3)
```

**`[MINOR] FMT-05: No commented-out code.`** Dead code MUST be deleted, not commented. Version control preserves history.

**`[MINOR] FMT-05a: Follow naming conventions.`** Variables and functions use `snake_case`. Classes and exceptions use `PascalCase` (acronyms fully uppercased: `HTTPError`, not `HttpError`). Module-level constants use `UPPER_CASE`. Internal/non-public attributes use a single leading underscore (`_name`).

**`[MINOR] FMT-06: No backslash line continuations.`** Use implicit continuation inside parentheses, brackets, or braces.

**`[MINOR] FMT-07: In hanging-indent continuations, no argument on the same line as the opening parenthesis.`**

**`[MINOR] FMT-08: Docstrings must use triple double-quotes (""").`** Single-quote docstrings are not permitted.

**`[MINOR] FMT-09: Multi-line docstrings must have a blank line between the summary sentence and the body.`**

**`[WARNING] FMT-10: If inline comments appear on more than 20% of non-blank, non-docstring source lines, comment density is too high.`** Comments must be reserved for rationale not derivable from reading the code.

---

## 15. Self-Review Protocol

Before submitting any code, the agent MUST complete this self-review in order. The order is intentional: cheap automated checks first, expensive reasoning last.

### Phase 1: Automated / Static Checks (Fast, Deterministic)

1. **Formatting**: Does the code pass `ruff check` and `ruff format --check`?
2. **Type checking**: Does the code pass `mypy --strict`?
3. **Import hygiene**: No wildcards, no circulars, correct ordering?
4. **Line lengths**: All lines ≤ 88 characters?
5. **File lengths**: All files ≤ 500 lines?

### Phase 2: Structural Checks (Requires Reading)

6. **Architecture boundaries**: Does any import violate the dependency direction? Does the domain layer import any framework?
7. **SOLID compliance**: Does each class have a single responsibility? Are dependencies injected?
8. **Complexity**: Is cyclomatic complexity ≤ 10? Is nesting depth ≤ 4? Are function bodies ≤ 50 lines?
9. **Type completeness**: Are all functions annotated? Is `Any` justified where used?
10. **Resource management**: Are all resources (files, connections, sessions) managed by context managers?

### Phase 3: Semantic Checks (Requires Reasoning)

11. **Security**: Does the code introduce any of the SEC-01 through SEC-09 violations?
12. **Correctness**: Does the code handle edge cases? Empty inputs? None values? Concurrent access?
13. **Performance**: Are there N+1 queries? Unbounded result sets? Blocking I/O in async contexts?
14. **Test coverage**: Do the tests cover the happy path, error paths, and edge cases? Do they meet the coverage thresholds?
15. **Production readiness**: Is logging structured? Is configuration validated? Are retries bounded?

### Phase 4: Final Gate

16. **Pattern consistency**: Does the new code match existing patterns in the codebase?
17. **Blast radius**: Does the change modify only what the task requires?
18. **Override audit**: Are all rule overrides documented with justification?

If ANY check fails, fix it before proceeding. Do not submit code with known violations.

---

## 16. Hard Limits Quick Reference Table

All numeric limits from this document in one place.

| Metric | Limit | Rule ID |
|--------|-------|---------|
| Cyclomatic complexity per function | ≤ 10 | PERF-01 |
| Function body length (excl. docstrings, blanks) | ≤ 50 lines | PERF-02 |
| File length | ≤ 500 lines | PERF-03 |
| Nesting depth | ≤ 4 levels | PERF-04 |
| Inheritance depth | ≤ 3 levels | OOP-07 |
| Parameters before kw_only required | < 4 | OOP-10 |
| Line length | ≤ 88 characters | FMT-02 |
| Test coverage — overall | ≥ 80% | TEST-01a |
| Test coverage — domain/business logic | ≥ 95% | TEST-01b |
| if-elif branches before singledispatch | < 4 | FP-04 |
| Distinct data shapes before match/case | ≥ 3 | FP-05 |
| Sequential transforms before pipeline | ≥ 3 | FP-02 |
| Retry attempts (maximum) | 3–5 with exponential backoff | PROD-05 |
| Near-identical tests before parametrize | ≥ 3 | TEST-11 |
| HTTP 201 for creation, 204 for deletion | Required | API-01 |
| API version prefix | Required (`/api/v1/...`) | API-03 |
| # noqa / # type: ignore override density ceiling | ≤ 5% of non-blank, non-comment lines | IMP-09 |
| Inline comment density ceiling | ≤ 20% of non-blank, non-docstring lines | FMT-10 |
| Sequential operations before functional composition | ≥ 3 | FP-11 |
| Module-level variable mutations across pipeline calls | < 3 | FP-12 |
| Warning repetitions before escalation to MAJOR | 3 | Section 1.4 |

---

*End of document. All rules are binding. Follow the companion [Action Loop](coding_agent_action_loop.md) for the operational process.*
