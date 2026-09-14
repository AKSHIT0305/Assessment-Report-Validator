# Assessment Report Validator

Web-based Excel QA and validation system for daily assessment-agency result workbooks.

## Planned user flow
1. Upload 8–10 Excel files from the frontend.
2. Backend validates every workbook.
3. Dashboard shows `9/10 Correct`, correct filenames, incorrect filenames, and exact errors.
4. Validation history is retained.
5. Phase 2 will add assessor database reconciliation.

## Environment
- Windows 11 Pro
- Dell Latitude 5300
- Intel Core i7-8665U
- 16 GB RAM

## Architecture
- Frontend: React + TypeScript + Tailwind
- Backend: Python + FastAPI
- Excel engine: openpyxl + spreadsheet calculation engine
- Phase 2: assessor database integration

This repository is the initial production-oriented skeleton. Validation rules are intentionally kept modular so they can be expanded without changing the UI.
