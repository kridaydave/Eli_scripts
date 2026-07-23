# Backend Code Sources — Research Report

## Language Distribution
| Language | % of Training | Rationale |
|----------|--------------|-----------|
| Go | 35% | Highest density of battle-tested infra code |
| Python | 25% | Most mature web backend ecosystem |
| Rust | 20% | Highest correctness signal |
| Java | 10% | Enterprise patterns at scale |
| TypeScript | 10% | Modern async backend patterns |

## Top Repos by Language
### CEO Additions
- Linux
- Hermes Agent
- Openclaw

### Go
- kubernetes/kubernetes — gold standard for PR review (OWNERS, sig-review, LGTM)
- etcd-io/etcd — distributed consensus, heavily refactored
- cockroachdb/cockroach — formal PR template, TLA+ specs alongside Go
- traefik/traefik — cloud-native proxy, mandatory tests
- hashicorp/consul — structured review with CHANGELOG requirements
- minio/minio — S3-compatible, clean Go, heavy test coverage
- golang/go — Gerrit-based, Google-level review
- prometheus/prometheus — OWNERS review, extensive testing
- thanos-io/thanos — Prometheus at scale, clean Go

### Rust
- tokio-rs/tokio — async runtime, rigorous review, perf benchmarks
- huggingface/candle — ML framework, clean Rust
- vectordotdev/vector — observability pipeline, heavy testing
- firecracker-microvm/firecracker — AWS microVM, security-critical, exhaustive review
- risingwavelabs/risingwave — streaming DB, good Rust patterns

### Python
- django/django — 20+ years, formal DEP process, mandatory tests
- encode/django-rest-framework — excellent PR discussions, strong test culture
- tiangolo/fastapi — very active, well-reviewed, pytest patterns
- getsentry/sentry — heavy test coverage, clean architecture
- apache/airflow — Apache formal review, extensive tests
- celery/celery — very old, well-reviewed, significant refactoring

### TypeScript
- nestjs/nest — exceptional PR culture, mandatory tests
- trpc/trpc — active, well-reviewed, good TypeScript patterns
- calcom/cal.com — real production backend, active PR reviews
- directus/directus — very active, strong review, tests

### Java
- spring-projects/spring-boot — extreme review rigor
- elastic/elasticsearch — mature, detailed PR process
- apache/kafka — Apache formal review, heavy testing
- keycloak/keycloak — auth backend, well-structured review

## Top Orgs
golang, kubernetes, cockroachdb, hashicorp, spring-projects, apache, elastic, timescale, tokio-rs, pingcap, neondatabase, getsentry, encode, vercel

## How to Find More

### GitHub Search Queries
```
stars:>5000 pushed:>2026-01-01 language:go NOT topic:frontend NOT topic:cli
org:kubernetes stars:>1000 pushed:>2026-01-01
```

### Quality Scoring Signals
| Signal | Weight | Measure |
|--------|--------|---------|
| PR discussion density | High | >5 comments per PR avg |
| Time-to-merge | Medium | 2h-7d median |
| % code in tests | High | >30% of repo |
| OWNERS/CODEOWNERS | Medium | Presence of formal files |
| Refactoring commits | High | grep "refactor" in commit messages |
| Used as dependency | Medium | 100+ dependents |

### Tools
- Libraries.io — dependency analysis
- CNCF Landscape — curated cloud-native projects
- OSS Insight — PR review metrics comparison
- GitHub Code Quality dashboard (2026)
