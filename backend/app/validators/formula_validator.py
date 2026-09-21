from backend.app.utils.score_utils import get_score_columns
from backend.app.utils.sheet_mapper import SheetMapper
from backend.app.utils.workbook_analyzer import WorkbookAnalyzer
from backend.app.utils.calculation_verifier import CalculationVerifier


class FormulaValidator:
    """
    Validates formulas used in the assessment report.

    Important:
    - Label cells such as B8, B9 and B10 are NOT formulas.
    - Only actual calculated-value cells are required to contain formulas.
    - Metadata cells may be hardcoded or formula-driven depending on template.
    """

    def validate(self, workbook, issues, sheet_mapping=None, template=None):
        
        # Resolve sheet names using sheet mapping
        if sheet_mapping:
            primary_sheet_name = sheet_mapping.get("PRIMARY_DATA_SHEET")
            tabular_sheet_name = sheet_mapping.get("TABULAR_ANALYSIS_SHEET")
        else:
            # Fallback to dynamic detection
            primary_sheet_name = SheetMapper.identify_primary_data_sheet(workbook)
            tabular_sheet_name = SheetMapper.identify_tabular_analysis_sheet(workbook)
        
        if primary_sheet_name is None or primary_sheet_name not in workbook.sheetnames:
            # Cannot validate without primary sheet
            return
        
        score_ws = workbook[primary_sheet_name]
        
        # Tabular sheet is optional
        tabular_ws = None
        if tabular_sheet_name and tabular_sheet_name in workbook.sheetnames:
            tabular_ws = workbook[tabular_sheet_name]

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
        # Pass/Fail columns are optional per confirmed validation rules.
        # Only validate if Pass/Fail columns exist in the workbook.

        if score_columns:

            for row in candidate_rows:

                for info in score_columns:

                    score_col = info["score_column"]
                    pass_fail_col = info.get("pass_fail_column")

                    # Skip validation if Pass/Fail column doesn't exist
                    if pass_fail_col is None:
                        continue

                    score_cell = score_ws.cell(
                        row,
                        score_col
                    )

                    pass_fail_cell = score_ws.cell(
                        row,
                        pass_fail_col
                    )

                    formula = pass_fail_cell.value

                    # Pass/Fail column may contain a formula OR a hardcoded value
                    # Check for string formulas or ArrayFormula objects
                    is_formula = False
                    
                    if isinstance(formula, str) and formula.startswith("="):
                        is_formula = True
                    elif hasattr(formula, 'text'):  # ArrayFormula objects have a text attribute
                        is_formula = True
                    elif hasattr(formula, '__class__') and 'ArrayFormula' in str(formula.__class__):
                        is_formula = True

                    if is_formula:
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
                                "sheet": primary_sheet_name,
                                "cell": pass_fail_cell.coordinate,
                                "expected": score_reference,
                                "actual": formula,
                            })
                    else:
                        # Hardcoded value - verify against score and pass criteria
                        score_value = score_cell.value
                        max_score = info["max_score"]
                        
                        # Detect pass criteria from workbook
                        pass_criteria = WorkbookAnalyzer.detect_pass_criteria(score_ws)
                        if pass_criteria is None:
                            # Per confirmed validation rules: Do not assume 80% pass threshold
                            # if the workbook's actual criteria can be detected. If criteria
                            # cannot be reliably determined, mark REVIEW.
                            issues.append({
                                "code": "HARDCODED_PASS_FAIL_REVIEW",
                                "category": "Formula",
                                "message": (
                                    "Hardcoded Pass/Fail value cannot be verified "
                                    "because pass criteria could not be reliably detected. "
                                    "Manual review required."
                                ),
                                "sheet": primary_sheet_name,
                                "cell": pass_fail_cell.coordinate,
                                "expected": "Depends on pass criteria",
                                "actual": formula,
                                "severity": "REVIEW",
                            })
                            continue
                        
                        # Determine expected Pass/Fail based on score
                        if score_value is not None and isinstance(score_value, (int, float)):
                            expected_pass = score_value >= (max_score * pass_criteria)
                        else:
                            # Cannot verify without score value
                            issues.append({
                                "code": "HARDCODED_PASS_FAIL_REVIEW",
                                "category": "Formula",
                                "message": (
                                    "Hardcoded Pass/Fail value cannot be verified "
                                    "because score value is missing or invalid."
                                ),
                                "sheet": primary_sheet_name,
                                "cell": pass_fail_cell.coordinate,
                                "expected": "Depends on score value",
                                "actual": formula,
                                "severity": "REVIEW",
                            })
                            continue
                        
                        # Normalize the hardcoded value
                        normalized_value = str(formula).strip().lower()
                        actual_pass = normalized_value in {"pass", "p", "yes", "y", "1", "true"}
                        actual_fail = normalized_value in {"fail", "f", "no", "n", "0", "false"}
                        
                        if not (actual_pass or actual_fail):
                            # Invalid Pass/Fail value
                            issues.append({
                                "code": "INVALID_PASS_FAIL_VALUE",
                                "category": "Formula",
                                "message": (
                                    "Hardcoded Pass/Fail value is not a valid "
                                    "Pass/Fail indicator."
                                ),
                                "sheet": primary_sheet_name,
                                "cell": pass_fail_cell.coordinate,
                                "expected": "Pass or Fail",
                                "actual": formula,
                            })
                            continue
                        
                        # Verify if hardcoded value matches expected
                        if actual_pass != expected_pass:
                            issues.append({
                                "code": "HARDCODED_PASS_FAIL_MISMATCH",
                                "category": "Formula",
                                "message": (
                                    f"Hardcoded Pass/Fail value does not match "
                                    f"expected result based on score "
                                    f"({score_value}/{max_score}, pass criteria: {pass_criteria*100}%)."
                                ),
                                "sheet": primary_sheet_name,
                                "cell": pass_fail_cell.coordinate,
                                "expected": "Pass" if expected_pass else "Fail",
                                "actual": formula,
                            })
                        # If it matches, accept it as valid (no error)

        # --------------------------------------------------
        # Batch Analysis - Tabular (optional)
        # --------------------------------------------------
        #
        # Dynamic summary cell detection: Locate summary cells
        # based on labels/headers rather than fixed positions.
        # Per confirmed validation rules, summary values do not
        # have to be located at fixed cells.
        # --------------------------------------------------

        if tabular_ws is None:
            # Tabular sheet is optional - skip validation
            return

        # Dynamically locate summary cells using WorkbookAnalyzer
        summary_cells_dict = WorkbookAnalyzer.find_summary_section(tabular_ws)
        
        # Convert dictionary format to list format for compatibility
        summary_cells = []
        if summary_cells_dict:
            for field_name, coordinate in summary_cells_dict.items():
                summary_cells.append({
                    "coordinate": coordinate,
                    "label": field_name,
                })
        
        is_bsdm_template = self._is_bsdm_template(tabular_ws)

        if not is_bsdm_template and summary_cells:
            for cell_info in summary_cells:
                coordinate = cell_info["coordinate"]
                label = cell_info["label"]

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
                    # Per confirmed validation rules: Hardcoded calculated values
                    # may be accepted, but independently verify that the final
                    # formulas/calculations and resulting values are mathematically
                    # correct wherever validation is applicable.
                    
                    # For now, add a REVIEW item since we cannot independently verify
                    # without implementing the full calculation verification logic
                    issues.append({
                        "code": "HARDCODED_SUMMARY_REVIEW",
                        "category": "Formula",
                        "message": (
                            f"Hardcoded summary value for {label} cannot be "
                            f"independently verified. Manual review required."
                        ),
                        "sheet": tabular_sheet_name,
                        "cell": coordinate,
                        "expected": "Calculated from source data",
                        "actual": value,
                        "severity": "REVIEW",
                    })
                    continue

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
        Detect BSDM template variation where summary cells contain
        hardcoded values instead of formulas.
        
        BSDM workbooks have:
        - Batch ID as hardcoded value (not formula)
        - QP Result with specific hardcoded values
        - Summary cells: Integer values instead of formulas
        """
        # Check row 7 for BSDM-specific patterns (QP Result)
        row_7_col_1 = tabular_ws.cell(7, 1).value
        row_7_col_2 = tabular_ws.cell(7, 2).value
        if (row_7_col_1 and "SSC/Q" in str(row_7_col_1)) or (row_7_col_2 and "SSC/Q" in str(row_7_col_2)):
            return True
        
        # Check if batch ID cell contains a hardcoded value instead of formula
        batch_id_cell = WorkbookAnalyzer.find_batch_id_cell(tabular_ws)
        
        if batch_id_cell:
            batch_id_value = tabular_ws[batch_id_cell].value
            
            # If batch ID is a formula, this is not BSDM template
            if isinstance(batch_id_value, str) and batch_id_value.startswith("="):
                return False
            
            # Check if batch ID is a numeric value (hardcoded)
            if isinstance(batch_id_value, (int, float)):
                return True
        
        # Check for BSDM-specific patterns in summary section
        summary_cells = WorkbookAnalyzer.find_summary_section(tabular_ws)
        
        # If summary cells are found and they contain hardcoded integers
        # instead of formulas, this might be BSDM template
        if summary_cells:
            for field_name, coordinate in summary_cells.items():
                cell_value = tabular_ws[coordinate].value
                if isinstance(cell_value, (int, float)) and not isinstance(cell_value, bool):
                    # Found a hardcoded integer in summary cells
                    return True
        
        return False