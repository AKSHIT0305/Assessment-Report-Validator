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
        # Find header row and candidate ID column
        # --------------------------------------------------

        header_row = self._find_header_row(score_ws)
        
        if header_row is None:
            # Can't validate candidate-level formulas without header
            return
        
        columns = self._detect_columns(score_ws, header_row)
        candidate_id_col = columns.get("candidate_id")

        # --------------------------------------------------
        # Candidate rows
        # --------------------------------------------------
        # Determine data rows dynamically from the actual data region.
        # A row is a data row if it has any non-empty cell in the columns
        # that exist for this template. Do NOT use candidate_id as the
        # universal row marker - a missing candidate ID must still be validated.

        candidate_rows = []
        for row in range(header_row + 1, score_ws.max_row + 1):
            row_values = []
            for col in range(1, score_ws.max_column + 1):
                v = score_ws.cell(row, col).value
                if v is not None and str(v).strip() != "":
                    row_values.append(v)
            if row_values:
                candidate_rows.append(row)

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
                    # Check for string formulas or ArrayFormula objects
                    is_formula = False
                    
                    if isinstance(formula, str) and formula.startswith("="):
                        is_formula = True
                    elif hasattr(formula, 'text'):  # ArrayFormula objects have a text attribute
                        is_formula = True
                    elif hasattr(formula, '__class__') and 'ArrayFormula' in str(formula.__class__):
                        is_formula = True

                    if not is_formula:

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

                    # Extract formula text from ArrayFormula objects if needed
                    formula_text = formula
                    if hasattr(formula, 'text'):
                        formula_text = formula.text
                    elif hasattr(formula, '__class__') and 'ArrayFormula' in str(formula.__class__):
                        # For ArrayFormula, try to get the formula text
                        formula_text = str(formula)  # fallback to string representation

                    normalized_formula = str(formula_text).upper()
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
        # Business rule: C8, C9, C10 are calculated summary cells
        # that should contain formulas for Enrolled, Appeared, and
        # Passed counts respectively. These are template-specific
        # positions for the current ALTERNATE_SCORE template.
        #
        # Exception: BSDM template variation uses hardcoded values
        # instead of formulas in C8/C9/C10. Detect this variation.
        # --------------------------------------------------

        # Check if this is a BSDM template variation
        is_bsdm_template = self._is_bsdm_template(tabular_ws)

        if not is_bsdm_template:
            calculated_cells = [
                "C8",
                "C9",
                "C10",
            ]

            for coordinate in calculated_cells:

                value = tabular_ws[coordinate].value

                # Check if the value is a formula (string starting with "=")
                # or an ArrayFormula object which contains a formula
                is_formula = False
                
                if isinstance(value, str) and value.startswith("="):
                    is_formula = True
                elif hasattr(value, 'text'):  # ArrayFormula objects have a text attribute
                    is_formula = True
                elif hasattr(value, '__class__') and 'ArrayFormula' in str(value.__class__):
                    is_formula = True

                if not is_formula:

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

        # Find NOS section start row dynamically
        nos_start_row = self._find_nos_start_row(tabular_ws)
        
        if nos_start_row is None:
            # Can't validate NOS formulas without knowing where they start
            return

        for row_index in range(
            nos_start_row,
            nos_start_row + len(score_columns)
        ):

            for column in "BCDEFG":

                coordinate = f"{column}{row_index}"

                value = tabular_ws[coordinate].value

                # Check if the value is a formula (string starting with "=")
                # or an ArrayFormula object which contains a formula
                is_formula = False
                
                if isinstance(value, str) and value.startswith("="):
                    is_formula = True
                elif hasattr(value, 'text'):  # ArrayFormula objects have a text attribute
                    is_formula = True
                elif hasattr(value, '__class__') and 'ArrayFormula' in str(value.__class__):
                    is_formula = True

                if not is_formula:

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

    # ======================================================
    # Helpers
    # ======================================================

    def _find_header_row(self, ws):
        """Find the row containing 'Candidate ID' header."""
        for row in range(1, ws.max_row + 1):
            for column in range(1, ws.max_column + 1):
                value = ws.cell(row, column).value
                if value is None:
                    continue
                normalized = (
                    str(value)
                    .strip()
                    .lower()
                    .replace("_", " ")
                )
                if normalized in {"candidate id", "candidateid"}:
                    return row
        return None

    def _detect_columns(self, ws, header_row):
        """Detect column positions from header row."""
        columns = {}
        for column in range(1, ws.max_column + 1):
            value = ws.cell(header_row, column).value
            if value is None:
                continue
            normalized = (
                str(value)
                .strip()
                .lower()
                .replace("_", " ")
                .replace("-", " ")
            )
            normalized = " ".join(normalized.split())
            
            if normalized in {"candidate id", "candidateid"}:
                columns["candidate_id"] = column
            elif normalized in {"batch id", "batchid"}:
                columns["batch_id"] = column
            elif normalized in {"gender", "sex"}:
                columns["gender"] = column
            elif normalized in {"assessment date", "assessmentdate", "date of assessment"}:
                columns["assessment_date"] = column
        return columns

    def _find_nos_start_row(self, tabular_ws):
        """Find the row where NOS statistics begin in Tabular sheet."""
        # Look for NOS SUMMARY header or first NOS code
        nos_summary_row = None
        first_nos_code_row = None
        
        for row in range(1, min(tabular_ws.max_row, 30) + 1):
            value = tabular_ws.cell(row, 1).value
            if value is None:
                continue
            cell_value = str(value).strip()
            # Check for NOS SUMMARY header
            if "NOS SUMMARY" in cell_value.upper():
                nos_summary_row = row
            # Check for actual NOS codes (SSC/, MEP/, DGT/, etc.)
            if any(prefix in cell_value.upper() for prefix in ["SSC/", "MEP/", "DGT/", "TEL/"]):
                first_nos_code_row = row
                break  # Found first actual NOS code, stop searching
        
        # If we found actual NOS codes, that's the start row
        if first_nos_code_row:
            return first_nos_code_row
        
        # If we only found NOS SUMMARY header, NOS data typically starts 2 rows after
        # (row + 1 is usually headers, row + 2 is data)
        if nos_summary_row:
            return nos_summary_row + 2
        
        return None

    def _is_bsdm_template(self, tabular_ws):
        """
        Detect BSDM template variation where C8/C9/C10 contain
        hardcoded values instead of formulas.
        
        BSDM workbooks have:
        - Row 3: Batch ID as hardcoded value (not formula)
        - Row 7: QP Result with specific hardcoded values
        - C8, C9, C10: Integer values instead of formulas
        """
        # Check if B3 contains a hardcoded value instead of formula
        b3_value = tabular_ws["B3"].value
        
        # If B3 is a formula, this is not BSDM template
        if isinstance(b3_value, str) and b3_value.startswith("="):
            return False
        
        # Check if B3 is a numeric value (hardcoded)
        if isinstance(b3_value, (int, float)):
            return True
        
        # Check row 7 for BSDM-specific patterns
        row_7_col_1 = tabular_ws.cell(7, 1).value
        if row_7_col_1 and "SSC/Q" in str(row_7_col_1):
            return True
        
        # Check if C8, C9, C10 are hardcoded integers
        for coordinate in ["C8", "C9", "C10"]:
            value = tabular_ws[coordinate].value
            if isinstance(value, (int, float)):
                # If any of these are hardcoded numbers, it's likely BSDM
                return True
        
        return False