import math
import statistics

from app.utils.score_utils import get_score_columns
from app.utils.sheet_mapper import SheetMapper
from app.utils.workbook_analyzer import WorkbookAnalyzer


class StatisticsValidator:

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

        header_row = self._find_header_row(score_ws)

        if header_row is None:
            return

        columns = self._detect_columns(
            score_ws,
            header_row
        )

        candidate_id_col = columns.get("candidate_id")
        gender_col = columns.get("gender")

        if candidate_id_col is None:
            return

        candidate_rows = [
            row
            for row in range(
                header_row + 1,
                score_ws.max_row + 1
            )
            if score_ws.cell(
                row,
                candidate_id_col
            ).value is not None
        ]

        if not candidate_rows:
            return

        score_columns = get_score_columns(score_ws)

        if not score_columns:

            issues.append({
                "code": "NO_SCORE_COLUMNS",
                "category": "Statistics",
                "message": "No score columns found.",
                "sheet": "score_sheet",
                "cell": None,
                "expected": "At least one score column",
                "actual": None,
            })

            return

        # --------------------------------------------------
        # Candidate counts
        # --------------------------------------------------

        enrolled = len(candidate_rows)
        appeared = 0
        passed = 0

        for row in candidate_rows:

            scores = []

            for info in score_columns:

                value = score_ws.cell(
                    row,
                    info["score_column"]
                ).value

                if self._is_numeric(value):

                    scores.append(
                        (
                            float(value),
                            info["max_score"]
                        )
                    )

            if scores:

                appeared += 1

                candidate_passed = all(
                    score >= max_score * 0.80
                    for score, max_score in scores
                )

                if candidate_passed:
                    passed += 1

        # --------------------------------------------------
        # Gender
        # --------------------------------------------------

        male = 0
        female = 0

        if gender_col is not None:

            for row in candidate_rows:

                gender = str(
                    score_ws.cell(
                        row,
                        gender_col
                    ).value or ""
                ).strip().lower()

                if gender in {"male", "m"}:
                    male += 1

                elif gender in {"female", "f"}:
                    female += 1

        # --------------------------------------------------
        # NOS statistics
        # --------------------------------------------------

        # Find NOS section start row dynamically
        nos_start_row = self._find_nos_start_row(tabular_ws)
        
        if nos_start_row is None:
            # Can't validate NOS statistics without knowing where they start
            return

        for tabular_row, info in enumerate(
            score_columns,
            start=nos_start_row
        ):

            score_col = info["score_column"]
            nos_name = info["nos"]
            max_score = info["max_score"]

            scores = []

            for row in candidate_rows:

                value = score_ws.cell(
                    row,
                    score_col
                ).value

                if self._is_numeric(value):
                    scores.append(float(value))

            if not scores:
                continue

            passed_students = sum(
                score >= max_score * 0.80
                for score in scores
            )

            pass_percentage = (
                passed_students / len(scores)
            )

            mean = statistics.mean(scores)
            minimum = min(scores)
            maximum = max(scores)
            median = statistics.median(scores)

            standard_deviation = (
                statistics.stdev(scores)
                if len(scores) >= 2
                else None
            )

            self._check_number(
                tabular_ws,
                f"B{tabular_row}",
                pass_percentage,
                issues,
                f"{nos_name} pass percentage"
            )

            self._check_number(
                tabular_ws,
                f"C{tabular_row}",
                mean,
                issues,
                f"{nos_name} mean"
            )

            self._check_number(
                tabular_ws,
                f"D{tabular_row}",
                minimum,
                issues,
                f"{nos_name} minimum"
            )

            self._check_number(
                tabular_ws,
                f"E{tabular_row}",
                maximum,
                issues,
                f"{nos_name} maximum"
            )

            self._check_number(
                tabular_ws,
                f"F{tabular_row}",
                median,
                issues,
                f"{nos_name} median"
            )

            if standard_deviation is None:

                actual = tabular_ws[
                    f"G{tabular_row}"
                ].value

                if actual is not None:

                    issues.append({
                        "code": "SD_UNDEFINED_SINGLE_CANDIDATE",
                        "category": "Statistics",
                        "message": (
                            f"Standard deviation for {nos_name} "
                            "cannot be calculated from one candidate."
                        ),
                        "sheet": "Batch Analysis - Tabular",
                        "cell": f"G{tabular_row}",
                        "expected": "Business-rule dependent",
                        "actual": actual,
                        "severity": "WARNING",
                    })

            else:

                self._check_number(
                    tabular_ws,
                    f"G{tabular_row}",
                    standard_deviation,
                    issues,
                    f"{nos_name} standard deviation"
                )

        # --------------------------------------------------
        # Batch totals
        # --------------------------------------------------
        # Dynamic summary cell detection: Locate summary cells
        # based on labels/headers rather than fixed positions.
        # Per confirmed validation rules, summary values do not
        # have to be located at fixed cells.

        summary_cells = self._find_summary_cells(tabular_ws)

        for cell_info in summary_cells:
            coordinate = cell_info["coordinate"]
            label = cell_info["label"]

            if label == "enrolled":
                self._check_number(
                    tabular_ws,
                    coordinate,
                    enrolled,
                    issues,
                    "Enrolled candidates"
                )
            elif label == "appeared":
                self._check_number(
                    tabular_ws,
                    coordinate,
                    appeared,
                    issues,
                    "Appeared candidates"
                )
            elif label == "passed":
                self._check_number(
                    tabular_ws,
                    coordinate,
                    passed,
                    issues,
                    "Passed candidates"
                )
            elif label == "male":
                self._check_number(
                    tabular_ws,
                    coordinate,
                    male,
                    issues,
                    "Male candidates"
                )
            elif label == "female":
                self._check_number(
                    tabular_ws,
                    coordinate,
                    female,
                    issues,
                    "Female candidates"
                )

    # ======================================================
    # Helpers
    # ======================================================

    def _find_header_row(self, ws):

        for row in range(
            1,
            min(ws.max_row, 30) + 1
        ):

            for column in range(
                1,
                ws.max_column + 1
            ):

                value = ws.cell(
                    row,
                    column
                ).value

                if value is None:
                    continue

                normalized = (
                    str(value)
                    .strip()
                    .lower()
                    .replace("_", " ")
                )

                if normalized in {
                    "candidate id",
                    "candidateid",
                }:
                    return row

        return None

    def _detect_columns(
        self,
        ws,
        header_row
    ):

        columns = {}

        for column in range(
            1,
            ws.max_column + 1
        ):

            value = ws.cell(
                header_row,
                column
            ).value

            if value is None:
                continue

            normalized = (
                str(value)
                .strip()
                .lower()
                .replace("_", " ")
            )

            normalized = " ".join(
                normalized.split()
            )

            if normalized in {
                "candidate id",
                "candidateid",
            }:
                columns["candidate_id"] = column

            elif normalized in {
                "gender",
                "sex",
            }:
                columns["gender"] = column

        return columns

    def _is_numeric(self, value):

        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and not math.isnan(float(value))
        )

    def _check_number(
        self,
        ws,
        cell,
        expected,
        issues,
        field_name,
        tolerance=0.01,
    ):

        actual = ws[cell].value

        if isinstance(
            actual,
            str
        ) and actual.startswith("="):
            return

        if actual is None:
            return

        # Per confirmed validation rules: Accept valid pass-criteria
        # representations such as decimals, percentages, numeric values,
        # and textual representations. Validate the meaning/value rather
        # than relying only on formatting.
        
        # Convert actual value to numeric if it's a percentage or text representation
        numeric_actual = self._normalize_to_numeric(actual)
        
        if numeric_actual is None:
            return

        if abs(
            numeric_actual - float(expected)
        ) > tolerance:

            issues.append({
                "code": "STATISTIC_MISMATCH",
                "category": "Statistics",
                "message": (
                    f"{field_name} does not match "
                    "independent calculation."
                ),
                "sheet": ws.title,
                "cell": cell,
                "expected": round(
                    float(expected),
                    6
                ),
                "actual": round(
                    numeric_actual,
                    6
                ),
            })

    def _normalize_to_numeric(self, value):
        """
        Normalize various pass-criteria representations to numeric value.
        
        Per confirmed validation rules: Accept valid pass-criteria
        representations such as decimals, percentages, numeric values,
        and textual representations. Validate the meaning/value rather
        than relying only on formatting.
        """
        if self._is_numeric(value):
            return float(value)
        
        if isinstance(value, str):
            value = value.strip()
            
            # Handle percentage format (e.g., "80%", "80.5%")
            if value.endswith("%"):
                try:
                    return float(value.rstrip("%")) / 100
                except ValueError:
                    pass
            
            # Handle text representations (e.g., "80 percent", "80.5 percent")
            if "percent" in value.lower():
                try:
                    num_part = value.lower().replace("percent", "").strip()
                    return float(num_part) / 100
                except ValueError:
                    pass
            
            # Handle decimal text (e.g., "0.8", "0.805")
            try:
                return float(value)
            except ValueError:
                pass
        
        return None

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

    def _find_summary_cells(self, tabular_ws):
        """
        Dynamically locate summary cells based on labels/headers.
        
        Returns list of dicts with 'coordinate' and 'label' for:
        - Enrolled candidates
        - Appeared candidates
        - Passed candidates
        - Male candidates
        - Female candidates
        
        Per confirmed validation rules, summary values do not have
        to be located at fixed cells. This method searches for
        labels and identifies the corresponding value cells.
        """
        summary_cells = []
        
        # Common label patterns to search for
        label_patterns = {
            "enrolled": ["enrolled", "total enrolled", "enrolled candidates"],
            "appeared": ["appeared", "total appeared", "appeared candidates"],
            "passed": ["passed", "total passed", "passed candidates"],
            "male": ["male", "male candidates", "total male"],
            "female": ["female", "female candidates", "total female"],
        }
        
        # Search first 30 rows for labels
        for row in range(1, min(tabular_ws.max_row, 30) + 1):
            for col in range(1, min(tabular_ws.max_column, 10) + 1):
                cell_value = tabular_ws.cell(row, col).value
                if cell_value is None:
                    continue
                
                normalized = str(cell_value).strip().lower()
                
                # Check if this cell matches any label pattern
                for label_type, patterns in label_patterns.items():
                    if any(pattern in normalized for pattern in patterns):
                        # Found a label, check the cell to the right for the value
                        value_col = col + 1
                        if value_col <= tabular_ws.max_column:
                            coordinate = tabular_ws.cell(row, value_col).coordinate
                            summary_cells.append({
                                "coordinate": coordinate,
                                "label": label_type,
                            })
                            # Remove this label from patterns to avoid duplicates
                            label_patterns[label_type] = []
        
        # Fallback to default positions if dynamic detection fails
        if not summary_cells:
            # Use traditional positions as fallback
            summary_cells = [
                {"coordinate": "C8", "label": "enrolled"},
                {"coordinate": "C9", "label": "appeared"},
                {"coordinate": "C10", "label": "passed"},
                {"coordinate": "F8", "label": "male"},
                {"coordinate": "G8", "label": "female"},
            ]
        
        return summary_cells