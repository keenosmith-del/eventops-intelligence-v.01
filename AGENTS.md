# EventOps development instructions

- Develop in this original eventops-intelligence-v.01 checkout on main. Keep the existing frontend/backend structure and GitHub repository.
- Do not create external development worktrees, application copies or additional repositories. Do not touch eventops-intelligence-v.02.
- Preserve historical baselines via Git tags/history and record iteration changes in docs/iterations/post-submission/.
- Baseline tags: assessment-demonstrated-v0.1 (recorded assessment release) and pre-iteration-v0.1 (later repository snapshot including submission recordings).
- Preserve existing local credentials and database volumes. Default local ports: frontend 5173, backend 5050, PostgreSQL 55432.
- Run established backend, frontend and browser checks for changes. Distinguish fixtures, local integration and real external checks.
- Do not force-push, rewrite published history, apply production migrations or alter production records. Request explicit owner confirmation before pushing main, because Render may automatically deploy it.
- Consolidate and verify Phase 1 before beginning Phase 2. Phases 2–6 extend this application in place; keep their evidence and progress in the iteration documentation.
