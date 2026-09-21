from backend.app.utils.sheet_mapper import SheetMapper
from backend.app.utils.workbook_analyzer import WorkbookAnalyzer


class TemplateDetector:
    """
    Detects the assessment report template based on
    worksheet names and workbook structure.
    """

    TEMPLATE_STANDARD = "STANDARD"
    TEMPLATE_ALTERNATE_SCORE = "ALTERNATE_SCORE"
    TEMPLATE_LEGACY_RESULT = "LEGACY_RESULT"

    def detect(self, workbook):

        # Per confirmed validation rules: ignore hidden sheets completely
        # Validation should focus only on the three relevant visible sheets
        visible_sheets = set(
            sheet_name
            for sheet_name in workbook.sheetnames
            if not workbook[sheet_name].sheet_state == 'hidden'
        )

        # --------------------------------------------------
        # Legacy Result / PC-Wise template
        # --------------------------------------------------

        if {
            "Result",
            "Analysis-Tabular",
            "Analysis - Graph",
        }.issubset(visible_sheets):

            return {
                "template": self.TEMPLATE_LEGACY_RESULT,
                "sheet_mapping": SheetMapper.get_mapping(self.TEMPLATE_LEGACY_RESULT),
            }

        # --------------------------------------------------
        # score_sheet based templates
        # --------------------------------------------------

        if "score_sheet" not in visible_sheets:
            return None

        score_ws = workbook["score_sheet"]

        # --------------------------------------------------
        # Alternate layout
        # --------------------------------------------------

        header_row = self._find_candidate_header_row(
            score_ws
        )

        if header_row is None:
            return None

        headers = self._get_headers(
            score_ws,
            header_row
        )

        # Alternate template commonly uses
        # Batch ID + Gender + Assessment Date.
        has_batch_id = any(
            header in {
                "batch id",
                "batchid",
            }
            for header in headers
        )

        has_candidate_id = any(
            header in {
                "candidate id",
                "candidateid",
            }
            for header in headers
        )

        has_gender = "gender" in headers
        has_assessment_date = (
            "assessment date" in headers
            or "assessmentdate" in headers
        )

        if (
            has_batch_id
            and has_candidate_id
            and has_gender
            and has_assessment_date
        ):

            # If the metadata layout starts at row 1,
            # classify as alternate.
            # Check if there's content in the first few rows before the header
            has_metadata = False
            for row in range(1, header_row):
                for col in range(1, min(score_ws.max_column + 1, 5)):
                    if score_ws.cell(row, col).value is not None:
                        has_metadata = True
                        break
                if has_metadata:
                    break
            
            if has_metadata:
                return {
                    "template": self.TEMPLATE_ALTERNATE_SCORE,
                    "sheet_mapping": SheetMapper.get_mapping(self.TEMPLATE_ALTERNATE_SCORE),
                }

            return {
                "template": self.TEMPLATE_STANDARD,
                "sheet_mapping": SheetMapper.get_mapping(self.TEMPLATE_STANDARD),
            }

        # --------------------------------------------------
        # Standard template
        # --------------------------------------------------

        if (
            has_batch_id
            and has_candidate_id
        ):
            return {
                "template": self.TEMPLATE_STANDARD,
                "sheet_mapping": SheetMapper.get_mapping(self.TEMPLATE_STANDARD),
            }

        return None

    # ======================================================
    # Helpers
    # ======================================================

    def _find_candidate_header_row(self, ws):

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

                normalized = self._normalize(
                    value
                )

                if normalized in {
                    "candidate id",
                    "candidateid",
                }:
                    return row

        return None

    def _get_headers(
        self,
        ws,
        row
    ):

        headers = []

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

            headers.append(
                self._normalize(value)
            )

        return headers

    @staticmethod
    def _normalize(value):

        return " ".join(
            str(value)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
            .split()
        )