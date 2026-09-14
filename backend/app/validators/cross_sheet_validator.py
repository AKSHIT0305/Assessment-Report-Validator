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
        # Business rule: B3 in Tabular sheet contains the Batch ID
        # for the current ALTERNATE_SCORE template.

        batch_id = score_ws.cell(
            candidate_rows[0],
            batch_id_col
        ).value

        tabular_batch_id = self._resolve_formula(
            tabular_ws["B3"].value,
            workbook,
            max_depth=5
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

        # Find NOS section start row dynamically
        nos_start_row = self._find_nos_start_row(tabular_ws)
        
        if nos_start_row is None:
            # Can't validate NOS names without knowing where they start
            return

        for index, expected_nos in enumerate(
            score_nos,
            start=nos_start_row
        ):

            actual_nos = tabular_ws.cell(
                index,
                1
            ).value

            actual_nos = self._resolve_formula(
                actual_nos,
                workbook,
                max_depth=3
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

        # Find the header row dynamically
        header_row = self._find_header_row(ws)
        
        if header_row is None:
            return []

        for column in range(
            1,
            ws.max_column + 1
        ):

            header = ws.cell(
                header_row,
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

            # Handle different score header patterns
            if " - Score" in header:
                nos = header.split(
                    " - Score",
                    1
                )[0].strip()
                nos_list.append(nos)
            elif "-Score" in header:
                nos = header.split(
                    "-Score",
                    1
                )[0].strip()
                nos_list.append(nos)

        return nos_list

    def _resolve_formula(
        self,
        value,
        workbook,
        max_depth=5,
        visited=None
    ):
        """
        Resolve Excel cell references recursively.
        
        Handles chained references like:
        - Tabular B3 -> score_sheet!B9
        - score_sheet B9 -> A13
        - A13 -> actual value
        
        Args:
            value: The cell value to resolve
            workbook: The workbook object
            max_depth: Maximum recursion depth to prevent infinite loops
            visited: Set of already visited cell references to prevent cycles
        """
        if visited is None:
            visited = set()
        
        if max_depth <= 0:
            return value
        
        if not isinstance(
            value,
            str
        ):
            return value

        if not value.startswith("="):
            return value

        formula = value[1:].strip()

        # Handle both cross-sheet references (sheet!cell) and same-sheet references (cell)
        if "!" in formula:
            sheet_name, cell_ref = formula.split(
                "!",
                1
            )
            sheet_name = sheet_name.strip("'")
            
            # Prevent cycles
            reference_key = f"{sheet_name}!{cell_ref}"
            if reference_key in visited:
                return value
            visited.add(reference_key)

            if sheet_name not in workbook.sheetnames:
                return value

            resolved_value = workbook[
                sheet_name
            ][cell_ref].value
        else:
            # Same-sheet reference - assume current sheet context
            # For this implementation, we can't resolve same-sheet references
            # without knowing the current sheet, so return as-is
            return value
        
        # Recursively resolve if the resolved value is also a formula
        if isinstance(resolved_value, str) and resolved_value.startswith("="):
            return self._resolve_formula(
                resolved_value,
                workbook,
                max_depth - 1,
                visited
            )
        
        return resolved_value

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