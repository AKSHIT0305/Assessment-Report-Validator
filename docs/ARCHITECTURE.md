# Architecture

Frontend
  -> FastAPI
  -> Excel validation orchestration
  -> deterministic validators
  -> independent calculation engine
  -> report service

Phase 2:
  -> assessor database reconciliation

The frontend's primary dashboard requirement is:
- If 9 of 10 files pass, clearly display `9 / 10 correct`.
- Show all 9 correct filenames.
- Show each incorrect filename.
- For every incorrect file, show exact errors, including category, sheet, cell, expected value and actual value where available.
