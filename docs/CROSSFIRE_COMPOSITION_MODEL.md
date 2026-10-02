# CrossFire Composition Model

The project distinguishes three parallelism layers.

## Evidence parallelism
Six analytical lenses run independently against the same immutable snapshot: TypeScript breadth, Rust quality, Go fan-out, security, Cloudflare/runtime, and policy/reconciliation. The language migration policy reserves Rust for measured CPU/memory-sensitive kernels and Go for measured high-concurrency/network utilities; those roles are evidence-driven rather than blanket language preferences.

## AI parallelism
A separate provider crossfire can use up to six independently configured provider/API lanes. Five successful independent lanes is the strong evidence threshold; fewer lanes are reported as limited. Providers are never simulated when unavailable, and one model's answer is not passed to another during the evidence phase.

## Work parallelism
Independent read-only missions may run concurrently. Writes, merges, issue mutation, deployment, production promotion and rollback remain serialized.

## Combined flow
inventory -> risk partition -> six evidence lenses -> domain checks -> live runtime -> six-provider AI crossfire -> deterministic reconciliation -> one evidence receipt -> monitors

Existing scanners are detectors; workflows are orchestrators; dashboards are consumers; production, policy, provider and resource authorities remain canonical.

## Coverage
Every tracked inventory entry receives an explicit disposition and required lens assignment. Unsupported languages are delegated or marked not-applicable with a reason; they are never silently omitted.

## Failure semantics
A timeout, quota exhaustion, missing credential, crashed lane or unavailable runtime is an execution state, not a successful zero-finding result.

## Cost/token optimization
Use map-first retrieval and deterministic summaries before deep analysis. AI receives bounded evidence packets instead of whole-repository dumps. Navigation maps remain indexes, not authority.