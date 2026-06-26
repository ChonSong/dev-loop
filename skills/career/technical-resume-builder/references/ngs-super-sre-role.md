# NGS Super — Site Reliability Engineer Role Research

**Source:** Elmo Talent Portal (job/view/160)
**Date:** June 2026
**Closes:** 24/06/2026

## Company Context
- NGS Super is an award-winning $18B public offer industry super fund focused on the education and community sectors
- Sydney CBD office
- Seeking their **first** SRE — greenfield role, high ownership, building reliability practices from scratch

## Job Requirements

**Must have (5+ years desired, but portfolio can compensate):**
- SRE/DevOps/Platform/SysEng experience improving production service reliability
- Incident response, RCA, blameless post-incident reviews
- SLIs/SLOs/error budgets for prioritisation
- Observability tooling (logging, metrics, tracing, alerting, dashboards)
- Strong troubleshooting across app/infra/network layers
- Cloud platforms (ideally AWS)
- CI/CD, IaC, deployment safety, rollback strategies
- Scripting/automation (Node.js, Python, JavaScript)
- Security fundamentals, governance, compliance
- On-call participation
- Clear communication, documentation, coaching

**Nice to have:**
- Regulated environment (financial services/APRA)
- Incident management practice design
- Serverless/container platforms and orchestration
- Performance engineering, capacity planning
- Cloud certifications (AWS)
- Building reliability in a newly formed/growing team

## Mapping Sean's Profile

| Requirement | Sean's Evidence |
|-------------|----------------|
| Production service reliability | Self-hosted 9-container platform with health cascades, monitoring, automated backup |
| Incident response | Dead-letter queues, retry with backoff, health cascade `depends_on: service_healthy` |
| Observability | Prometheus-format metrics, telemetry server, structlog, health check endpoints |
| CI/CD/IaC | GitHub Actions matrix builds, Docker Compose, Cloudflare Terraform |
| Automation/scripting | Go webhook emitter, Python ETL pipelines, bash/systemd automation |
| Security | systemd hardening (NoNewPrivileges, ProtectSystem), HMAC signing, Cloudflare Access |
| Cloud | Cloudflare (tunnels, DNS, Access, Terraform) — not AWS but directly transferable |

## Application Strategy
- Use the Systems Engineer CV variant (same format as Harvey Robinson application)
- In the cover email, frame the self-hosted infrastructure as "production reliability engineering" rather than "home lab"
- Lead with the observability/monitoring and automation work
- Address the experience gap by emphasising depth over years
