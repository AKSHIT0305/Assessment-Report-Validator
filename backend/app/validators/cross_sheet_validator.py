from app.utils.sheet_mapper import SheetMapper
from app.utils.workbook_analyzer import WorkbookAnalyzer
from app.utils.score_utils import get_score_columns


class CrossSheetValidator:
    """
    Validates consistency between primary data sheet and
    tabular analysis sheet.
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
        
        # Per confirmed validation rules: ignore hidden sheets completely
        visible_sheets = [
            sheet_name
            for sheet_name in workbook.sheetnames
            if not workbook[sheet_name].sheet_state == 'hidden'
        ]
        
        # Both sheets are required for cross-sheet validation
        if primary_sheet_name is None or primary_sheet_name not in visible_sheets:
            return
        if tabular_sheet_name is None or tabular_sheet_name not in visible_sheets:
            return

        score_ws = workbook[primary_sheet_name]
        tabular_ws = workbook[tabular_sheet_name]

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
        # Dynamic batch ID location: use WorkbookAnalyzer
        batch_id_cell = WorkbookAnalyzer.find_batch_id_cell(tabular_ws)

        if batch_id_cell:
            batch_id_raw = score_ws.cell(
                candidate_rows[0],
                batch_id_col
            ).value
            
            # Resolve formula in score_sheet if present
            batch_id = self._resolve_formula(
                batch_id_raw,
                workbook,
                max_depth=5,
                current_sheet=primary_sheet_name
            )

            tabular_batch_id = self._resolve_formula(
                tabular_ws[batch_id_cell].value,
                workbook,
                max_depth=5,
                current_sheet=tabular_sheet_name
            )

            # If the cell is actually a label/header, don't compare it.
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
                        "sheet": tabular_sheet_name,
                        "cell": batch_id_cell,
                        "expected": batch_id,
                        "actual": tabular_batch_id,
                    })

        # --------------------------------------------------
        # NOS names
        # --------------------------------------------------
        # Per confirmed validation rules: NOS sets must match across
        # relevant sheets, but additional NOS-related rows such as
        # WEAK PCs are allowed. Distinguish valid additional rows
        # from actual missing or inconsistent NOS data.

        score_nos = self._get_score_nos(score_ws)

        # Find NOS section dynamically using WorkbookAnalyzer
        nos_section = WorkbookAnalyzer.find_nos_section(tabular_ws)
        
        if nos_section is None:
            # Can't validate NOS names without finding the section
            return
        
        nos_start_row = nos_section["start_row"]
        nos_end_row = nos_section["end_row"]

        # Collect all NOS codes from Tabular sheet (including additional rows)
        tabular_nos_list = []
        for row in range(nos_start_row, nos_end_row + 1):
            nos_value = tabular_ws.cell(row, 1).value
            if nos_value is None:
                continue
            
            resolved_nos = self._resolve_formula(
                nos_value,
                workbook,
                max_depth=3,
                current_sheet=tabular_sheet_name
            )
            
            if resolved_nos is None:
                continue
            
            normalized_nos = str(resolved_nos).strip()
            if normalized_nos == "":
                continue
            
            # Check if this is a valid NOS code (SSC/, MEP/, DGT/, TEL/, etc.)
            if self._is_valid_nos_code(normalized_nos):
                tabular_nos_list.append({
                    "row": row,
                    "nos": normalized_nos
                })

        # Validate that all score_sheet NOS are present in Tabular
        # Additional NOS (like WEAK PCs) are allowed
        missing_nos = []
        for expected_nos in score_nos:
            expected_normalized = str(expected_nos).strip()
            found = False
            for tabular_nos in tabular_nos_list:
                # Use fuzzy matching - the score NOS might have variations
                # Try exact match first
                if tabular_nos["nos"] == expected_normalized:
                    found = True
                    break
                # Try substring match (e.g., "DGT/VSQ/N0101" matches "DGT/VSQ/N0101-50.0")
                elif expected_normalized in tabular_nos["nos"] or tabular_nos["nos"] in expected_normalized:
                    found = True
                    break
            
            if not found:
                missing_nos.append(expected_normalized)

        if missing_nos:
            for missing_nos_item in missing_nos:
                issues.append({
                    "code": "NOS_MISMATCH",
                    "category": "Cross Sheet",
                    "message": (
                        f"NOS '{missing_nos_item}' from {primary_sheet_name} "
                        f"is missing from {tabular_sheet_name}."
                    ),
                    "sheet": tabular_sheet_name,
                    "cell": None,
                    "expected": missing_nos_item,
                    "actual": "Not found in tabular sheet",
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

            # Handle different score header patterns with improved normalization
            nos = header
            
            # First, remove max_score suffix (e.g., "DGT/VSQ/N0101-50.0" -> "DGT/VSQ/N0101")
            # This handles cases where the max_score is embedded in the NOS code itself
            if "-" in nos:
                parts = nos.rsplit("-", 1)
                if len(parts) == 2:
                    suffix = parts[1].strip()
                    # Check if suffix is a pure number (may contain decimal point)
                    if suffix.replace(".", "").isdigit():
                        nos = parts[0].strip()
            
            # Then split by "- Score" or "-Score"
            if " - Score" in nos:
                nos = nos.split(" - Score", 1)[0].strip()
            elif "- Score" in nos:
                nos = nos.split("- Score", 1)[0].strip()
            elif "-Score" in nos:
                nos = nos.split("-Score", 1)[0].strip()
            elif " - Total" in nos:
                nos = nos.split(" - Total", 1)[0].strip()
            elif "- Total" in nos:
                nos = nos.split("- Total", 1)[0].strip()
            
            # Strip trailing dots and special characters
            nos = nos.rstrip(".-")
            
            # Additional cleanup for remaining suffixes
            if nos.endswith("-Score"):
                nos = nos[:-6].strip()
            if nos.endswith("-Total"):
                nos = nos[:-6].strip()
            
            # Only add if it looks like a NOS code (contains /)
            if "/" in nos:
                nos_list.append(nos)

        return nos_list

    def _resolve_formula(
        self,
        value,
        workbook,
        max_depth=5,
        visited=None,
        current_sheet=None
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
            current_sheet: The current sheet name for same-sheet references
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
            # Same-sheet reference - use current_sheet if provided
            if current_sheet and current_sheet in workbook.sheetnames:
                resolved_value = workbook[current_sheet][formula].value
            else:
                # Can't resolve without current sheet context
                return value
        
        # Recursively resolve if the resolved value is also a formula
        if isinstance(resolved_value, str) and resolved_value.startswith("="):
            # Determine which sheet to use for the next resolution
            # If we just came from a cross-sheet reference, use that sheet
            # Otherwise, use the current_sheet parameter
            if "!" in formula:
                # We came from a cross-sheet reference, use that sheet
                next_sheet = sheet_name
            else:
                # Same-sheet reference, use current_sheet
                next_sheet = current_sheet
            return self._resolve_formula(
                resolved_value,
                workbook,
                max_depth - 1,
                visited,
                next_sheet
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

    def _is_valid_nos_code(self, nos_string):
        """
        Check if a string represents a valid NOS code.
        
        Per confirmed validation rules: NOS sets must match across
        relevant sheets, but additional NOS-related rows such as
        WEAK PCs are allowed. This method identifies valid NOS codes
        including WEAK PCs.
        """
        if not isinstance(nos_string, str):
            return False
        
        normalized = nos_string.strip().upper()
        
        # Standard NOS code patterns (SSC/, MEP/, DGT/, TEL/, etc.)
        nos_prefixes = ["SSC/", "MEP/", "DGT/", "TEL/", "AGRI/", "ELE/", "CONS/"]
        
        # Check for standard NOS codes
        for prefix in nos_prefixes:
            if normalized.startswith(prefix):
                return True
        
        # Check for WEAK PCs (additional NOS-related rows that are allowed)
        if "WEAK" in normalized or "PC" in normalized:
            return True
        
        return False

    def _get_score_nos(self, ws):
        """Extract NOS names from score sheet headers."""
        score_columns = get_score_columns(ws)
        return [info["nos"] for info in score_columns]