from backend.app.utils.score_utils import get_score_columns


class FormulaValidator:
    """
    Validates formulas used in the assessment report.

    Important:
    - Label cells such as B8, B9 and B10 are NOT formulas.
    - Only actual calculated-value cells are required to contain formulas.
    - Metadata cells may be hardcoded or formula-driven depending on template.
    """

    def validate(self, workbook, issues):

        score_ws = workbook["score_sheet"]
        tabular_ws = workbook["Batch Analysis - Tabular"]

        score_columns = get_score_columns(score_ws)

        # --------------------------------------------------
        # Candidate rows
        # --------------------------------------------------

        candidate_rows = [
            row
            for row in range(13, score_ws.max_row + 1)
            if score_ws.cell(row, 1).value is not None
        ]

        # --------------------------------------------------
        # Candidate-level Pass/Fail formulas
        # --------------------------------------------------

        if score_columns:

            for row in candidate_rows:

                for info in score_columns:

                    score_col = info["score_column"]
                    pass_fail_col = info["pass_fail_column"]

                    score_cell = score_ws.cell(
                        row,
                        score_col
                    )

                    pass_fail_cell = score_ws.cell(
                        row,
                        pass_fail_col
                    )

                    formula = pass_fail_cell.value

                    # Pass/Fail column must contain a formula.
                    if not (
                        isinstance(formula, str)
                        and formula.startswith("=")
                    ):

                        issues.append({
                            "code": "MISSING_PASS_FAIL_FORMULA",
                            "category": "Formula",
                            "message": (
                                "Expected Pass/Fail formula is missing."
                            ),
                            "sheet": "score_sheet",
                            "cell": pass_fail_cell.coordinate,
                            "expected": "Excel formula",
                            "actual": formula,
                        })

                        continue

                    # --------------------------------------------------
                    # Formula should reference corresponding score cell
                    # --------------------------------------------------

                    score_reference = score_cell.coordinate

                    normalized_formula = formula.upper()
                    normalized_reference = score_reference.upper()

                    if normalized_reference not in normalized_formula:

                        issues.append({
                            "code": "PASS_FAIL_FORMULA_REFERENCE_ERROR",
                            "category": "Formula",
                            "message": (
                                "Pass/Fail formula does not reference "
                                "its corresponding score cell."
                            ),
                            "sheet": "score_sheet",
                            "cell": pass_fail_cell.coordinate,
                            "expected": score_reference,
                            "actual": formula,
                        })

        # --------------------------------------------------
        # Batch Analysis - Tabular
        # --------------------------------------------------
        #
        # B3, B4, B5, B6 and C6 are metadata/description cells.
        # They may legitimately contain hardcoded values.
        #
        # B8/B9/B10 are labels:
        #
        # B8 = Enrolled
        # B9 = Appeared
        # B10 = Passed
        #
        # Therefore they MUST NOT be validated as formulas.
        #
        # C8/C9/C10 are the calculated values and should be formulas.
        # --------------------------------------------------

        calculated_cells = [
            "C8",
            "C9",rt
            "C10",
        ]

        for coordinate in calculated_cells:

            value = tabular_ws[coordinate].value

            if not (
                isinstance(value, str)
                and value.startswith("=")
            ):

                issues.append({
                    "code": "MISSING_TABULAR_FORMULA",
                    "category": "Formula",
                    "message": (
                        f"Expected calculated formula "
                        f"is missing from {coordinate}."
                    ),
                    "sheet": "Batch Analysis - Tabular",
                    "cell": coordinate,
                    "expected": "Excel formula",
                    "actual": value,
                })

        # --------------------------------------------------
        # NOS statistics formulas
        # --------------------------------------------------

        if not score_columns:
            return

        for row_index in range(
            13,
            13 + len(score_columns)
        ):

            for column in "BCDEFG":

                coordinate = f"{column}{row_index}"

                value = tabular_ws[coordinate].value

                if not (
                    isinstance(value, str)
                    and value.startswith("=")
                ):

                    issues.append({
                        "code": "MISSING_NOS_FORMULA",
                        "category": "Formula",
                        "message": (
                            f"Expected NOS statistics "
                            f"formula is missing from "
                            f"{coordinate}."
                        ),
                        "sheet": "Batch Analysis - Tabular",
                        "cell": coordinate,
                        "expected": "Excel formula",
                        "actual": value,
                    })