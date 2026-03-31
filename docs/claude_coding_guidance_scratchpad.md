# Coding Agent Guidance Scratchpad

Extracted and adapted from the Reviewer Agent Guide v2.1, Action Loop, and Implementation Plan. These principles are reframed as **coding directives** — write code that satisfies every condition below.

---

## 1. AGENT IDENTITY & EXECUTION MODEL

### Sequential, Non-Skippable Execution

A coding agent follows a strict action loop. No step is optional.

0. **Receive task** — Parse the request. Identify scope, affected files, constraints.
1. **Validate inputs** — Confirm all required context is present before writing a single line. If context is insufficient, stop and ask. Never guess.
2. **Plan** — Outline the approach: which files change, what patterns apply, what tests are needed.
3. **Implement** — Write the code.
4. **Self-review** — Re-read every changed line against the rules in this document.
5. **Test** — Run or write tests that prove correctness.
6. **Report** — Summarize what changed and why.

### Core Behavioral Rules

- **Determinism**: Given the same task and codebase state, produce the same output. No randomness, no "it depends" without explicit conditions.
- **Never guess**: If you lack context (e.g., unclear requirements, missing type info, ambiguous architecture boundary), flag it as UNVERIFIABLE and ask. Do not invent behavior.
- **Agent-first language**: Express all conditions as measurable, machine-checkable predicates. Avoid subjective words like "clean," "nice," "simple." Instead: "function body ≤ 50 lines," "cyclomatic complexity ≤ 10."

---

## 2. SEVERITY AWARENESS (Write Code That Avoids These)

Understand the severity tiers so you never produce code that triggers a CRITICAL or MAJOR finding.

| Severity | What It Covers | Coding Agent Implication |
|----------|---------------|--------------------------|
| **CRITICAL** | Security holes, data corruption, architectural boundary violations | These are **never acceptable**. A single CRITICAL blocks the entire change. |
| **MAJOR** | SOLID violations, type safety gaps, structural design flaws | These require rework. Avoid by following the design rules below. |
| **MINOR** | Style, naming, docstring formatting | Fix these proactively. They are cheap to get right the first time. |
| **WARNING** | Best practice gaps with no immediate harm | Address these. A warning repeated 3 times across a codebase escalates to MAJOR. |

**Escalation rule**: If the same warning pattern appears 3+ times in your output, treat it as MAJOR and fix all instances.

---

## 3. SECURITY (CRITICAL tier — zero tolerance)

Every item below is a hard rule. Violating any one produces a CRITICAL finding.

- **SQL injection**: Use parameterized queries exclusively. Never interpolate variables into SQL strings. Use ORM query builders or `$1`-style placeholders.
- **Shell injection**: Never use `shell=True` with any variable input. Use `subprocess.run()` with a list of arguments.
- **No eval/exec**: Never use `eval()` or `exec()` unless there is explicit, documented justification and the input is provably trusted.
- **No pickle on external data**: Never deserialize untrusted data with `pickle`. Use JSON, MessagePack, or Protobuf.
- **YAML safety**: Always use `yaml.safe_load()` or `yaml.load(stream, Loader=yaml.SafeLoader)`. Never bare `yaml.load()`.
- **No hardcoded credentials**: Secrets come from environment variables or a secrets manager. Never commit API keys, passwords, tokens, or connection strings.
- **No debug=True in production**: Debug mode must be gated behind an environment check (e.g., `settings.DEBUG` sourced from env).
- **Path traversal prevention**: Validate and sanitize all file paths. Use `pathlib.Path.resolve()` and confirm the resolved path is within the expected root.
- **Bounded dependency versions**: Pin dependencies to specific versions or bounded ranges (e.g., `>=1.2,<2.0`). No unbounded `>=` without upper limit.

---

## 4. TYPE SAFETY (MAJOR tier)

- **Full type annotations**: Every function signature must have type annotations on all parameters and the return type. No `Any` unless unavoidable and documented.
- **mypy strict mode compliance**: Code must pass `mypy --strict`. This means no implicit `Any`, no untyped defs, no missing return types.
- **Protocol over ABC for interfaces**: When defining interfaces, prefer `typing.Protocol` (structural subtyping) over `abc.ABC` (nominal subtyping) unless you need shared implementation.
- **`T | None` over `Optional[T]`**: Use the union syntax (Python 3.10+). It is clearer and composes better.
- **Correct data container selection**:
  - `TypedDict` — When you need a typed dictionary (e.g., JSON-shaped data, backwards compat).
  - `NamedTuple` — Immutable, lightweight, when you need tuple unpacking.
  - `dataclass` — Mutable structured data with methods.
  - `Pydantic BaseModel` — Validation at boundaries (API input/output, config parsing).

---

## 5. TESTING (MAJOR tier)

- **Coverage targets**: 80% overall, 95% for domain/business logic layer.
- **No live I/O in unit tests**: Unit tests must never hit the network, filesystem, or database. Mock all I/O boundaries.
- **No shared mutable state between tests**: Each test must be independent. Use fixtures for setup; never rely on test execution order.
- **Mocks use `spec=`**: When mocking, always use `spec=SomeProtocol` or `spec=SomeClass` so the mock enforces the interface.
- **Test naming convention**: `test_<subject>_<condition>_<expected_outcome>`. Example: `test_search_empty_query_returns_400`.
- **Arrange-Act-Assert structure**: Every test has three clear phases. Separate them with blank lines if needed.
- **Test the behavior, not the implementation**: Tests should verify observable outcomes, not internal method calls (unless testing side effects).

---

## 6. PERFORMANCE (MAJOR tier)

- **Cyclomatic complexity ≤ 10**: If a function has more than 10 independent paths, decompose it.
- **Function body ≤ 50 lines**: Measured excluding docstrings and blank lines. If longer, extract helper functions.
- **File ≤ 500 lines**: If a file exceeds 500 lines, it likely has multiple responsibilities. Split it.
- **Nesting depth ≤ 4 levels**: No more than 4 levels of indentation. Use early returns, guard clauses, and extraction to flatten.
- **No N+1 queries**: When loading related objects, use joins or eager loading. Never issue one query per item in a loop.
- **No unbounded `.all()` without LIMIT**: Every query that could return an unbounded result set must have a `LIMIT` (or equivalent pagination).
- **Generator over list comprehension when only iterating**: If you only iterate once and don't need random access, use a generator expression or `yield`.
- **Lazy imports for heavy modules**: If a module is expensive to import and only used conditionally, import it inside the function.

---

## 7. OOP PRINCIPLES (MAJOR tier)

### SOLID — All Five, Non-Negotiable

1. **Single Responsibility Principle (SRP)**: A class has one reason to change. If you can describe a class's purpose with "and," it needs splitting.
2. **Open/Closed Principle (OCP)**: Open for extension, closed for modification. Use protocols, strategy pattern, or plugin architecture.
3. **Liskov Substitution Principle (LSP)**: Subtypes must be substitutable for their base types without altering program correctness.
4. **Interface Segregation Principle (ISP)**: No client should depend on methods it doesn't use. Prefer small, focused protocols.
5. **Dependency Inversion Principle (DIP)**: Depend on abstractions (protocols), not concretions. High-level modules must not import low-level modules directly.

### Additional OOP Rules

- **Composition over inheritance**: Default to composing objects. Use inheritance only for genuine "is-a" relationships.
- **Inheritance depth ≤ 3**: If your class hierarchy is deeper than 3 levels, flatten it with composition.
- **Domain dataclasses: `frozen=True`**: Domain value objects should be immutable.
- **High-volume dataclasses: `slots=True`**: For objects created in large quantities, use `__slots__` for memory efficiency.
- **≥4 parameters: `kw_only=True`**: When a dataclass or function has 4+ parameters, use keyword-only arguments to prevent positional mistakes.
- **Context managers for resources**: Files, DB connections, locks, HTTP sessions — always use `with` statements or `contextlib.contextmanager`.

---

## 8. FUNCTIONAL PROGRAMMING PATTERNS (MAJOR tier)

- **Pure functions: no side effects**: A pure function's output depends only on its inputs. It does not modify external state, write to disk, or call APIs.
- **Pipeline Decision Hierarchy**: When you have ≥3 sequential transformations, compose them functionally (e.g., `reduce`, `functools.reduce`, or a pipeline utility). Avoid deeply nested function calls.
- **No `lru_cache` on impure functions**: Caching a function that depends on external state (time, DB, network) produces stale/incorrect results.
- **`singledispatch` over if-elif chains ≥4 branches**: When dispatching on type with 4+ branches, use `functools.singledispatch` for extensibility.
- **`match/case` for ≥3 distinct shapes**: Use structural pattern matching when checking 3+ distinct data shapes. Cleaner than if-elif chains.
- **Result pattern over None chains**: Instead of returning `None` to signal failure (leading to `if x is not None` chains), use a Result type (e.g., `Ok | Err`) or raise domain-specific exceptions.

---

## 9. ARCHITECTURE (CRITICAL tier for boundary violations)

### Clean Architecture — Dependencies Point Inward Only

```
External (frameworks, DB, HTTP)
    ↓ depends on
Interface Adapters (routers, repos, gateways)
    ↓ depends on
Use Cases / Application Services
    ↓ depends on
Domain (entities, value objects, domain services)
```

- **Domain layer: no framework imports**. The domain must not import FastAPI, SQLAlchemy, Django, or any infrastructure framework. It contains only pure Python, dataclasses, protocols, and domain logic.
- **Use cases: no direct DB/HTTP instantiation**. Application services receive dependencies via injection. They never call `Session()`, `httpx.Client()`, or similar constructors directly.
- **Repository Protocol pattern**: Define a `Repository` protocol in the domain or application layer. Implement it in the infrastructure layer. Inject the implementation.
- **Unit of Work for multi-repo transactions**: When a use case touches multiple repositories in a single transaction, use a Unit of Work pattern to manage the transaction boundary.
- **Dependency injection over concrete instantiation**: Constructors and functions receive their dependencies as parameters. No hardcoded `import` of concrete implementations in business logic.

---

## 10. ASYNC (MAJOR tier)

- **No blocking I/O in `async def`**: If a function is `async`, every I/O call within it must be awaited (async). Blocking calls (e.g., `requests.get()`, `open().read()` on network FS) must be run in an executor via `asyncio.to_thread()`.
- **No nested `asyncio.run()`**: `asyncio.run()` creates a new event loop. Calling it inside an already-running loop raises `RuntimeError`. Use `await` instead.
- **Store `create_task()` results**: Always assign the return value of `asyncio.create_task()` to a variable. Unassigned tasks can be garbage collected before completion.
- **Handle task exceptions**: Either `await` the task, use `task.add_done_callback()`, or use `asyncio.TaskGroup` (3.11+). Unhandled task exceptions are silently swallowed.
- **`asyncio.Lock` for shared mutable state**: When multiple coroutines access shared state, protect it with `asyncio.Lock()`. Do not use `threading.Lock` in async code.

---

## 11. PRODUCTION READINESS (MAJOR tier)

- **Structured JSON logging**: Use `structlog` or `python-json-logger`. Every log entry should be a parseable JSON object with consistent fields (timestamp, level, message, context).
- **No PII in logs**: Never log email addresses, passwords, tokens, IP addresses (unless required and documented), or user-identifiable data.
- **Pydantic Settings for config**: Use `pydantic_settings.BaseSettings` to load and validate configuration from environment variables. This provides type safety and validation at startup.
- **Fail loudly on missing config**: If a required configuration value is absent, raise an error at startup. Do not fall back to a default silently — this hides deployment mistakes.
- **Bounded retries with exponential backoff**: When retrying I/O operations, use exponential backoff with jitter. Set a maximum retry count (e.g., 3-5). Never retry indefinitely.
- **No bare `except`**: Always catch a specific exception type. `except Exception` is acceptable as a last resort. `except:` (bare) catches `KeyboardInterrupt` and `SystemExit`, which must propagate.
- **Health checks**: Expose a `/health` endpoint that verifies connectivity to critical dependencies (DB, cache, external APIs).
- **Graceful shutdown**: Handle `SIGTERM` and `SIGINT`. Finish in-progress work, close connections, then exit.

---

## 12. IMPORTS (MINOR tier, but enforced)

- **No wildcard imports outside `__init__.py`**: `from module import *` makes dependencies invisible. Explicit imports only.
- **No circular imports**: If A imports B and B imports A, restructure. Common fixes: extract shared types into a third module, use `TYPE_CHECKING` for type-only imports, or invert the dependency.
- **Import ordering**: `stdlib` → `third-party` → `local`, separated by blank lines. Use `isort` to automate.
- **No private submodule imports from external packages**: Do not import `_internal` or `_utils` from third-party libraries. These are not part of the public API and can break without notice.

---

## 13. FORMATTING & DOCUMENTATION (MINOR tier)

- **4-space indent, no tabs**: Universal Python standard.
- **Lines ≤ 88 characters**: Compatible with Black formatter defaults.
- **Google-style docstrings**: Include `Args:`, `Returns:`, `Raises:` sections. Every public function and class must have a docstring.
- **Comments explain WHY, not WHAT**: The code says what it does. Comments explain the reasoning, constraints, or non-obvious decisions behind it.
- **No commented-out code**: Dead code should be deleted, not commented. Version control preserves history.

---

## 14. WORKFLOW PATTERNS FOR THE CODING AGENT

### Validate Before Executing

Before writing code:
1. Confirm the task is clear and complete.
2. Identify which files will be modified.
3. Check for existing patterns in the codebase — follow them.
4. Identify architectural boundaries that must not be violated.

### Cheap Checks First, Expensive Checks Last

When self-reviewing:
1. **Automated/static checks** (formatting, types, imports) — fast, deterministic.
2. **Structural checks** (SOLID, architecture boundaries, complexity) — requires reading.
3. **Semantic checks** (correctness, edge cases, security) — requires reasoning.

### Structured Output

When reporting changes:
- List every file modified and why.
- Note any architectural decisions made.
- Flag any trade-offs or areas of uncertainty.
- If a rule was intentionally bent, document the justification.

### Delta Tracking on Iterations

When revising code after feedback:
- Track what changed between iterations.
- Do not re-introduce previously fixed issues.
- Confirm each piece of feedback is addressed.

### Override Mechanism

If a rule must be violated:
- Document the specific rule being overridden.
- Provide explicit justification.
- Limit the scope of the override to the minimum necessary.
- Add a code comment at the violation site (e.g., `# OVERRIDE: <rule> — <reason>`).

---

## 15. DESIGN META-PRINCIPLES

These are the principles behind the rules — use them to make judgment calls when no specific rule applies.

1. **Determinism**: Every rule produces the same verdict from the same input. When writing code, every function should produce the same output from the same input (where possible).
2. **Completeness**: Cover the full surface area of risk. Do not leave gaps in validation, error handling, or test coverage.
3. **Actionability**: Every piece of code should make its intent and behavior obvious. A reader should know exactly what it does and why.
4. **Efficiency**: Do the cheap thing first. Validate inputs before processing. Fail fast on bad data.
5. **Agent-First**: Write code that is machine-parseable and machine-testable. Prefer explicit over implicit. Prefer structured data over free-form strings. Prefer types over conventions.

---

## QUICK REFERENCE: HARD LIMITS

| Metric | Limit |
|--------|-------|
| Cyclomatic complexity | ≤ 10 per function |
| Function body length | ≤ 50 lines |
| File length | ≤ 500 lines |
| Nesting depth | ≤ 4 levels |
| Inheritance depth | ≤ 3 levels |
| Parameters before kw_only | < 4 |
| Line length | ≤ 88 chars |
| Test coverage (overall) | ≥ 80% |
| Test coverage (domain) | ≥ 95% |
| if-elif branches before singledispatch | < 4 |
| Shapes before match/case | ≥ 3 |
| Transforms before pipeline composition | ≥ 3 |
| Retry attempts (max) | 3-5 with exponential backoff |
| Warning repetitions before escalation | 3 |
