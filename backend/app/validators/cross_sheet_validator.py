class CrossSheetValidator:
    """
    Validates consistency between score_sheet and
    Batch Analysis - Tabular.
    """

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

        batch_id_col = columns.get("batch_id")

        if batch_id_col is None:
            return

        candidate_rows = [
            row
            for row in range(
                header_row + 1,
                score_ws.max_row + 1
            )
            if score_ws.cell(
                row,
                batch_id_col
            ).value is not None
        ]

        if not candidate_rows:
            return

        # --------------------------------------------------
        # Batch ID
        # --------------------------------------------------

        batch_id = score_ws.cell(
            candidate_rows[0],
            batch_id_col
        ).value

        tabular_batch_id = self._resolve_formula(
            tabular_ws["B3"].value,
            workbook
        )

        # If B3 is actually a label/header, don't compare it.
        if not self._looks_like_header(
            tabular_batch_id,
            "batch"
        ):

            if (
                batch_id is not None
                and tabular_batch_id is not None
                and str(batch_id).strip()
                != str(tabular_batch_id).strip()
            ):

                issues.append({
                    "code": "BATCH_ID_MISMATCH",
                    "category": "Cross Sheet",
                    "message": (
                        "Batch ID does not match between sheets."
                    ),
                    "sheet": "Batch Analysis - Tabular",
                    "cell": "B3",
                    "expected": batch_id,
                    "actual": tabular_batch_id,
                })

        # --------------------------------------------------
        # NOS names
        # --------------------------------------------------

        score_nos = self._get_score_nos(
            score_ws
        )

        for index, expected_nos in enumerate(
            score_nos,
            start=13
        ):

            actual_nos = tabular_ws.cell(
                index,
                1
            ).value

            actual_nos = self._resolve_formula(
                actual_nos,
                workbook
            )

            if actual_nos is None:
                continue

            if str(actual_nos).strip() == "":
                continue

            if str(actual_nos).strip() != str(
                expected_nos
            ).strip():

                issues.append({
                    "code": "NOS_MISMATCH",
                    "category": "Cross Sheet",
                    "message": (
                        f"NOS mismatch at Tabular A{index}."
                    ),
                    "sheet": "Batch Analysis - Tabular",
                    "cell": f"A{index}",
                    "expected": expected_nos,
                    "actual": actual_nos,
                })

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
                "batch id",
                "batchid",
            }:

                columns["batch_id"] = column

        return columns

    def _get_score_nos(self, ws):

        nos_list = []

        for column in range(
            1,
            ws.max_column + 1
        ):

            header = ws.cell(
                12,
                column
            ).value

            if header is None:
                continue

            if not isinstance(
                header,
                str
            ):
                continue

            header = header.strip()

            if " - Score" in header:

                nos = header.split(
                    " - Score",
                    1
                )[0].strip()

                nos_list.append(nos)

        return nos_list

    def _resolve_formula(
        self,
        value,
        workbook
    ):

        if not isinstance(
            value,
            str
        ):
            return value

        if not value.startswith("="):
            return value

        formula = value[1:].strip()

        if "!" not in formula:
            return value

        sheet_name, cell_ref = formula.split(
            "!",
            1
        )

        sheet_name = sheet_name.strip(
            "'"
        )

        if sheet_name not in workbook.sheetnames:
            return value

        return workbook[
            sheet_name
        ][cell_ref].value

    def _looks_like_header(
        self,
        value,
        header_type
    ):

        if value is None:
            return False

        normalized = str(
            value
        ).strip().lower()

        if header_type == "batch":
            return normalized in {
                "batch id",
                "batchid",
            }

        return False