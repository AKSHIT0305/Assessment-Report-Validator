from collections import Counter
from datetime import datetime, date

from app.utils.score_utils import get_score_columns
from app.utils.sheet_mapper import SheetMapper


class DataValidator:
    """
    Validates candidate-level raw data in score_sheet.
    """

    def validate(self, workbook, issues, sheet_mapping=None):
        
        # Resolve primary sheet name using sheet mapping
        if sheet_mapping:
            primary_sheet_name = sheet_mapping.get("PRIMARY_DATA_SHEET")
        else:
            # Fallback to dynamic detection
            primary_sheet_name = SheetMapper.identify_primary_data_sheet(workbook)
        
        if primary_sheet_name is None or primary_sheet_name not in workbook.sheetnames:
            # Cannot validate without primary sheet
            return
        
        ws = workbook[primary_sheet_name]

        # --------------------------------------------------
        # Find candidate header row
        # Perform thorough search across all rows and columns
        # --------------------------------------------------

        header_row = self._find_header_row(ws)

        if header_row is None:

            # Per confirmed validation rules: if Candidate ID cannot be found
            # after a complete search, place the workbook under REVIEW
            # instead of immediately treating it as a standard validation failure.
            issues.append({
                "code": "CANDIDATE_HEADER_NOT_FOUND",
                "category": "Data",
                "message": (
                    "Candidate ID header could not be found after "
                    "thorough search across all rows and columns. "
                    "Workbook requires manual review."
                ),
                "sheet": primary_sheet_name,
                "cell": None,
                "expected": "Header containing Candidate ID",
                "actual": None,
                "severity": "REVIEW",  # Custom severity to trigger REVIEW status
            })

            return

        # --------------------------------------------------
        # Detect columns from headers
        # --------------------------------------------------

        columns = self._detect_columns(
            ws,
            header_row
        )

        candidate_id_col = columns.get(
            "candidate_id"
        )

        batch_id_col = columns.get(
            "batch_id"
        )

        gender_col = columns.get(
            "gender"
        )

        assessment_date_col = columns.get(
            "assessment_date"
        )

        # --------------------------------------------------
        # Determine data rows dynamically
        # Do NOT use candidate_id as universal row marker.
        # A row is a data row if it has any non-empty cell
        # in the columns that exist for this template.
        # --------------------------------------------------

        candidate_rows = []
        for row in range(
            header_row + 1,
            ws.max_row + 1
        ):
            row_values = []
            for col in range(1, ws.max_column + 1):
                v = ws.cell(row, col).value
                if v is not None and str(v).strip() != "":
                    row_values.append(v)
            if row_values:
                candidate_rows.append(row)

        if not candidate_rows:

            issues.append({
                "code": "NO_CANDIDATE_DATA",
                "category": "Data",
                "message": "No candidate records were found.",
                "sheet": primary_sheet_name,
                "cell": None,
                "expected": "At least one candidate",
                "actual": "0 candidates",
            })

            return

        # --------------------------------------------------
        # Candidate ID
        # --------------------------------------------------

        candidate_ids = []

        if candidate_id_col is not None:

            for row in candidate_rows:

                candidate_id = ws.cell(
                    row,
                    candidate_id_col
                ).value

                if (
                    candidate_id is None
                    or str(candidate_id).strip() == ""
                ):

                    issues.append({
                        "code": "MISSING_CANDIDATE_ID",
                        "category": "Data",
                        "message": "Candidate ID is missing.",
                        "sheet": primary_sheet_name,
                        "cell": (
                            f"{self._column_letter(candidate_id_col)}"
                            f"{row}"
                        ),
                        "expected": "Candidate ID",
                        "actual": None,
                    })

                else:

                    candidate_ids.append(
                        str(candidate_id).strip()
                    )

        # --------------------------------------------------
        # Duplicate Candidate IDs
        # --------------------------------------------------

        duplicates = [
            candidate_id
            for candidate_id, count
            in Counter(candidate_ids).items()
            if count > 1
        ]

        for candidate_id in duplicates:

            issues.append({
                "code": "DUPLICATE_CANDIDATE_ID",
                "category": "Data",
                "message": (
                    f"Duplicate Candidate ID: "
                    f"{candidate_id}"
                ),
                "sheet": primary_sheet_name,
                "cell": None,
                "expected": "Unique Candidate IDs",
                "actual": candidate_id,
            })

        # --------------------------------------------------
        # Batch ID
        # --------------------------------------------------

        if batch_id_col is not None:

            batch_ids = []

            for row in candidate_rows:

                value = ws.cell(
                    row,
                    batch_id_col
                ).value

                if value is not None:

                    batch_ids.append(
                        str(value).strip()
                    )

            unique_batch_ids = set(
                batch_ids
            )

            if len(unique_batch_ids) > 1:

                issues.append({
                    "code": "MULTIPLE_BATCH_IDS",
                    "category": "Data",
                    "message": "Multiple Batch IDs found.",
                    "sheet": primary_sheet_name,
                    "cell": (
                        f"{self._column_letter(batch_id_col)}"
                        f"{candidate_rows[0]}:"
                        f"{self._column_letter(batch_id_col)}"
                        f"{candidate_rows[-1]}"
                    ),
                    "expected": "One Batch ID",
                    "actual": sorted(
                        unique_batch_ids
                    ),
                })

        # --------------------------------------------------
        # Gender
        # --------------------------------------------------

        if gender_col is not None:

            # Accepted gender values per confirmed validation rules:
            # M, F, Male, Female (standard)
            # -, NA (students who did not appear for assessment)
            allowed_genders = {
                "male",
                "female",
                "m",
                "f",
                "n/a",
                "na",
                "n.a.",
                "-",  # Student did not appear for assessment
            }

            for row in candidate_rows:

                gender = ws.cell(
                    row,
                    gender_col
                ).value

                if gender is None:
                    continue

                normalized_gender = str(
                    gender
                ).strip().lower()

                if normalized_gender not in allowed_genders:

                    issues.append({
                        "code": "INVALID_GENDER",
                        "category": "Data",
                        "message": (
                            f"Invalid gender value: "
                            f"{gender}"
                        ),
                        "sheet": primary_sheet_name,
                        "cell": (
                            f"{self._column_letter(gender_col)}"
                            f"{row}"
                        ),
                        "expected": [
                            "Female",
                            "Male",
                            "F",
                            "M",
                            "N/A",
                            "NA",
                            "-",
                        ],
                        "actual": gender,
                    })

        # --------------------------------------------------
        # Assessment Date
        # --------------------------------------------------

        if assessment_date_col is not None:

            for row in candidate_rows:

                date_value = ws.cell(
                    row,
                    assessment_date_col
                ).value

                if date_value is None:
                    continue

                if not self._is_valid_date(
                    date_value
                ):

                    issues.append({
                        "code": "INVALID_ASSESSMENT_DATE",
                        "category": "Data",
                        "message": (
                            "Invalid assessment date."
                        ),
                        "sheet": primary_sheet_name,
                        "cell": (
                            f"{self._column_letter(assessment_date_col)}"
                            f"{row}"
                        ),
                        "expected": (
                            "Valid Excel date or "
                            "valid date string"
                        ),
                        "actual": date_value,
                    })

        # --------------------------------------------------
        # Scores
        # --------------------------------------------------

        score_columns = get_score_columns(ws)

        for row in candidate_rows:

            for score_info in score_columns:

                column = score_info[
                    "score_column"
                ]

                maximum_score = score_info[
                    "max_score"
                ]
                
                nos = score_info.get("nos", "")
                header = score_info.get("header", "")
                
                # Skip range validation for aggregate/total columns
                # These columns contain summed values (e.g., "SSC/N0202- Total", "QP-Total")
                # and legitimately exceed individual score ranges
                # Check both the extracted NOS name and the original header
                if "total" in nos.lower() or "total" in header.lower():
                    continue

                value = ws.cell(
                    row,
                    column
                ).value

                cell = ws.cell(
                    row,
                    column
                ).coordinate

                # Empty score cells are handled separately
                # if the workbook requires them.
                if value is None:
                    continue

                if (
                    not isinstance(
                        value,
                        (int, float)
                    )
                    or isinstance(
                        value,
                        bool
                    )
                ):

                    issues.append({
                        "code": "INVALID_SCORE",
                        "category": "Data",
                        "message": (
                            "Score must be numeric."
                        ),
                        "sheet": primary_sheet_name,
                        "cell": cell,
                        "expected": (
                            f"Numeric value between "
                            f"0 and {maximum_score:g}"
                        ),
                        "actual": value,
                    })

                    continue

                if (
                    value < 0
                    or value > maximum_score
                ):

                    issues.append({
                        "code": "SCORE_OUT_OF_RANGE",
                        "category": "Data",
                        "message": (
                            "Score is outside "
                            "allowed range."
                        ),
                        "sheet": primary_sheet_name,
                        "cell": cell,
                        "expected": (
                            f"0 to "
                            f"{maximum_score:g}"
                        ),
                        "actual": value,
                    })

    # ======================================================
    # Helpers
    # ======================================================

    def _find_header_row(self, ws):

        for row in range(
            1,
            ws.max_row + 1
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
                .replace("-", " ")
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
                "batch id",
                "batchid",
            }:

                columns["batch_id"] = column

            elif normalized in {
                "gender",
                "sex",
            }:

                columns["gender"] = column

            elif normalized in {
                "assessment date",
                "assessmentdate",
                "date of assessment",
            }:

                columns[
                    "assessment_date"
                ] = column

        return columns

    def _is_valid_date(self, value):

        # Actual Excel/Python date
        if isinstance(
            value,
            (datetime, date)
        ):

            return True

        # String dates
        if not isinstance(
            value,
            str
        ):

            return False

        value = value.strip()

        if not value:
            return False

        supported_formats = (
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d-%m-%y",
            "%d/%m/%y",
        )

        for date_format in supported_formats:

            try:

                datetime.strptime(
                    value,
                    date_format
                )

                return True

            except ValueError:
                continue

        return False

    @staticmethod
    def _column_letter(column):

        result = ""

        while column:

            column, remainder = divmod(
                column - 1,
                26
            )

            result = (
                chr(65 + remainder)
                + result
            )

        return result