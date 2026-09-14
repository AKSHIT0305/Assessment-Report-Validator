# AGENTS.md

## Project Overview

This project is an Assessment Report Validator.

It validates Excel-based assessment/report workbooks and identifies structural, data, formula, and consistency issues.

The project contains a React/TypeScript frontend and a Python/FastAPI backend.

---

## Core Development Principles

- Understand the existing architecture before making changes.
- Preserve existing functionality unless the requested change explicitly requires modifying it.
- Do not make unrelated changes.
- Prefer small, focused changes over large rewrites.
- Reuse existing utilities, validators, services, and dependencies whenever possible.
- Do not introduce a new dependency when the existing project can solve the problem cleanly.
- Keep frontend and backend responsibilities separated.
- Follow the existing coding style and project conventions.

---

## Excel Validation — IMPORTANT

The Excel validation system MUST remain flexible.

Do NOT assume that every workbook has:

- The same number of rows.
- The same number of columns.
- The same column order.
- The same sheet dimensions.
- Identical sheet layouts.
- Identical formatting.
- Identical capitalization or wording.

Validation logic should identify the meaning of data rather than relying only on fixed positions.

### Column Matching

Do not depend exclusively on exact column names.

Equivalent column names should be normalized and matched where appropriate.

For example:

- `Gender`
- `gender`
- `GENDER`
- `Sex`

may represent the same logical field when the validation rules allow it.

Column order must not be treated as significant unless a specific rule explicitly requires it.

### Value Normalization

Equivalent representations of the same logical value should be normalized before validation where appropriate.

For example:

- `Male` → `M`
- `Female` → `F`
- `male` → `M`
- `female` → `F`
- `M` → `M`
- `F` → `F`

Normalization must be implemented carefully and should not incorrectly merge genuinely different values.

### Rows

Do not assume a fixed number of data rows.

The validator should determine the actual populated data range dynamically.

Empty rows should not automatically be treated as invalid data unless the relevant validation rule explicitly requires them to contain data.

### Columns

Do not assume that required columns are always located at the same Excel column index.

Find columns based on their logical identity/header rather than hardcoded positions whenever possible.

---

## Sheet Handling

Do not assume every workbook contains exactly the same sheets.

Where possible:

1. Detect available sheets.
2. Identify relevant sheets based on their purpose/content.
3. Validate only the applicable rules.
4. Report missing required sheets clearly when a sheet is genuinely required.

Do not fail simply because an optional or irrelevant sheet is absent.

---

## Validation Architecture

Keep validation logic modular.

Prefer:

- Separate validators for separate validation concerns.
- Reusable normalization utilities.
- Configurable validation rules.
- Clear error categories.
- Structured validation results.

Avoid putting all validation logic into one large function.

When adding a new validation rule, determine whether it belongs in an existing validator before creating a new module.

---

## Error Handling

Validation errors should be:

- Clear.
- Actionable.
- Specific.
- Associated with the relevant workbook/sheet/cell when possible.
- Structured consistently with existing error objects.

Do not silently swallow validation errors.

Do not replace a useful existing error with a generic exception.

---

## Backend

The backend uses Python and FastAPI.

Before modifying backend code:

1. Understand the existing API/service/validator structure.
2. Follow existing patterns.
3. Keep API routes thin.
4. Put business logic in appropriate services/validators.
5. Avoid embedding Excel validation logic directly inside API routes.

---

## Frontend

The frontend uses React and TypeScript.

Before modifying frontend code:

- Reuse existing components.
- Follow existing state-management patterns.
- Avoid duplicating UI logic.
- Keep API communication consistent with existing implementation.
- Do not redesign unrelated UI.

---

## Testing

After meaningful code changes:

1. Run the relevant tests.
2. Run broader tests when appropriate.
3. Fix failures caused by the change.
4. Do not simply remove or weaken tests to make them pass.

When modifying Excel validation logic, add tests for:

- Different column orders.
- Different row counts.
- Different capitalization.
- Equivalent value representations.
- Missing required columns.
- Missing optional columns.
- Different workbook/sheet structures.
- Existing valid workbooks.
- Existing invalid workbooks.

Prefer representative fixtures over hardcoded assumptions.

---

## Before Making Changes

For non-trivial tasks:

1. Inspect the relevant code.
2. Understand the current implementation.
3. Identify the files that need to change.
4. Briefly explain the planned approach.
5. Then implement the change.

Do not modify files simply to explore the repository.

---

## Scope Control

Do not:

- Rewrite working modules without a clear reason.
- Rename large numbers of files unnecessarily.
- Change APIs unnecessarily.
- Change database/schema structures unless required.
- Remove existing functionality without explicit justification.
- Modify unrelated files.

If a requested change requires a potentially breaking architectural change, explain the impact before implementing it.

---

## Autonomous Coding Workflow

For implementation tasks, follow this workflow:

1. Understand the requirement.
2. Inspect the relevant repository code.
3. Create a concise implementation plan.
4. Implement the smallest appropriate change.
5. Run relevant tests.
6. Inspect failures.
7. Fix issues caused by the implementation.
8. Run tests again.
9. Review the final changes for unintended side effects.
10. Summarize the files changed, implementation, and verification performed.

Do not stop after writing code if tests or verification can reasonably be performed.

---

## Safety

Never:

- Expose API keys, secrets, passwords, or environment variables.
- Commit secrets.
- Delete project data without explicit instruction.
- Modify `.env` files unless explicitly required.
- Run destructive commands without confirmation.
- Make broad changes when a targeted change is sufficient.

---

## Communication

When completing a task, report:

1. What was changed.
2. Which files were changed.
3. Why those files were changed.
4. Tests/commands that were run.
5. Whether verification passed.
6. Any remaining concerns or limitations.

For large changes, clearly separate implemented work from recommended future work.