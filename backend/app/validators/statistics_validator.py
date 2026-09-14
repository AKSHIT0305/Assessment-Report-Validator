import math
import statistics

from backend.app.utils.score_utils import get_score_columns


class StatisticsValidator:

    def validate(self, workbook, issues):

        score_ws = workbook["score_sheet"]
        tabular_ws = workbook["Batch Analysis - Tabular"]

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

        for tabular_row, info in enumerate(
            score_columns,
            start=13
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

        self._check_number(
            tabular_ws,
            "C8",
            enrolled,
            issues,
            "Enrolled candidates"
        )

        self._check_number(
            tabular_ws,
            "C9",
            appeared,
            issues,
            "Appeared candidates"
        )

        self._check_number(
            tabular_ws,
            "C10",
            passed,
            issues,
            "Passed candidates"
        )

        self._check_number(
            tabular_ws,
            "F8",
            male,
            issues,
            "Male candidates"
        )

        self._check_number(
            tabular_ws,
            "G8",
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

        if not self._is_numeric(actual):
            return

        if abs(
            float(actual) - float(expected)
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
                    float(actual),
                    6
                ),
            })