# EventOps Intelligence — Deployment

## Deployment Objective

Deploy a complete, accessible AI engineering demonstration
without incurring cloud infrastructure or API usage charges.

Target infrastructure spending: R0.

## Current Status

Local backend development is operational.

No production deployment has been verified.

## Zero-Cost Requirements

- Do not provision paid cloud resources.
- Do not enable automatic billing upgrades.
- Use only confirmed free-tier services.
- Keep Gemini API usage within an unbilled project.
- Use synthetic data for external integration testing.
- Enforce bounded AI agent execution.
- Do not use paid APIs as automatic fallbacks.
- Do not expose API credentials to the frontend.
- Do not deploy until provider billing settings are verified.

## Local Development

Frontend: React/Vite, port 5173
Backend: FastAPI, port 5050
Database: PostgreSQL using Docker
Automation: n8n Community Edition using Docker

## Planned Cloud Architecture

Frontend: Free static hosting, subject to provider terms
Backend: Confirmed zero-cost Python hosting
Database: Confirmed free PostgreSQL hosting
AI: Gemini Developer API free tier
Integrations: Google Calendar, Gmail and public HTTP

Provider choices remain provisional until cost and
deployment constraints are verified.

## Persistence Requirements

Persistent application data must survive:

- Browser refresh
- Backend process restart
- Container restart
- Application redeployment

Conversation history, RAG metadata, agent execution
records and verification results must not depend
on ephemeral process memory.

## Cost and Quota Controls

The application will implement:

- Configurable model request limits
- Maximum agent iterations
- Bounded integration retries
- API request timeouts
- Controlled access to live external integrations
- Explicit quota-exceeded error handling
- No automatic paid-service fallback

## Deployment Verification

Before any production deployment:

1. Confirm provider plan and billing status.
2. Confirm no automatic paid usage is possible.
3. Verify database persistence.
4. Configure production environment variables.
5. Verify service-to-service connectivity.
6. Test live integrations using synthetic data.
7. Test browser refresh and backend restart.
8. Verify deployed RAG responses and agent execution.
9. Review provider usage dashboards.
10. Document the actual deployed URLs and limitations.

## Current Limitations

Cloud hosting has not yet been provisioned.

Live model and Google API usage require confirmed
free-tier account configuration.

A zero-charge outcome cannot be guaranteed solely
from advertised free-tier pricing.
