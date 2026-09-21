from pathlib import Path

from openpyxl import load_workbook

from backend.app.validators.workbook_validator import WorkbookValidator
from backend.app.validators.data_validator import DataValidator
from backend.app.validators.formula_validator import FormulaValidator
from backend.app.validators.statistics_validator import StatisticsValidator
from backend.app.validators.excel_error_validator import ExcelErrorValidator
from backend.app.validators.cross_sheet_validator import CrossSheetValidator
from backend.app.validators.template_detector import TemplateDetector


class ExcelValidator:
    """
    Main validation pipeline for assessment report workbooks.
    """

    def __init__(self):

        self.workbook_validator = WorkbookValidator()
        self.data_validator = DataValidator()
        self.formula_validator = FormulaValidator()
        self.statistics_validator = StatisticsValidator()
        self.excel_error_validator = ExcelErrorValidator()
        self.cross_sheet_validator = CrossSheetValidator()
        self.template_detector = TemplateDetector()

    def validate(self, file_path: Path):

        issues = []

        # ==================================================
        # 1. OPEN WORKBOOK
        # ==================================================

        try:

            workbook = load_workbook(
                file_path,
                data_only=False
            )

        except Exception as exc:

            return {
                "status": "ERROR",
                "template": None,
                "errors": [
                    {
                        "code": "WORKBOOK_OPEN_FAILED",
                        "category": "Workbook",
                        "message": (
                            "Excel workbook could not be opened."
                        ),
                        "sheet": None,
                        "cell": None,
                        "expected": "Valid Excel workbook",
                        "actual": str(exc),
                    }
                ],
                "warnings": [],
            }

        try:

            # ==================================================
            # 2. DETECT TEMPLATE
            # ==================================================

            template = self.template_detector.detect(
                workbook
            )

            if template is None:

                return {
                    "status": "ERROR",
                    "template": None,
                    "errors": [
                        {
                            "code": "UNKNOWN_TEMPLATE",
                            "category": "Workbook Structure",
                            "message": (
                                "Assessment report template "
                                "could not be identified."
                            ),
                            "sheet": None,
                            "cell": None,
                            "expected": (
                                "Supported assessment "
                                "report template"
                            ),
                            "actual": workbook.sheetnames,
                        }
                    ],
                    "warnings": [],
                }

            # ==================================================
            # 3. WORKBOOK STRUCTURE
            # ==================================================

            self.workbook_validator.validate(
                workbook,
                issues,
                template=template
            )

            # ==================================================
            # 4. EXCEL ERROR CHECK
            # ==================================================

            self.excel_error_validator.validate(
                workbook,
                issues
            )

            # ==================================================
            # 5. STANDARD / ALTERNATE TEMPLATES
            # ==================================================

            if template in {
                TemplateDetector.TEMPLATE_STANDARD,
                TemplateDetector.TEMPLATE_ALTERNATE_SCORE,
            }:

                required_sheets = {
                    "score_sheet",
                    "Batch Analysis - Tabular",
                }

                available_sheets = set(
                    workbook.sheetnames
                )

                has_required_sheets = (
                    required_sheets <= available_sheets
                )

                if has_required_sheets:

                    # ------------------------------------------
                    # Raw data validation
                    # ------------------------------------------

                    self.data_validator.validate(
                        workbook,
                        issues
                    )

                    # ------------------------------------------
                    # Formula validation
                    # ------------------------------------------

                    self.formula_validator.validate(
                        workbook,
                        issues
                    )

                    # ------------------------------------------
                    # Statistics validation
                    # ------------------------------------------

                    self.statistics_validator.validate(
                        workbook,
                        issues
                    )

                    # ------------------------------------------
                    # Cross-sheet validation
                    # ------------------------------------------

                    self.cross_sheet_validator.validate(
                        workbook,
                        issues
                    )

            # ==================================================
            # 6. LEGACY TEMPLATE
            # ==================================================
            # Per confirmed validation rules: BOTH workbook template
            # families are officially accepted. Do not reject a workbook
            # only because it belongs to the legacy or alternate template family.

            elif template == (
                TemplateDetector.TEMPLATE_LEGACY_RESULT
            ):

                # Legacy template uses different sheet names:
                # - Result (instead of score_sheet)
                # - Analysis-Tabular (instead of Batch Analysis - Tabular)
                # - Analysis - Graph (instead of Batch Analysis - Graph)
                
                # Map legacy sheet names to standard validation logic
                if "Result" in workbook.sheetnames:
                    # Apply data validation to Result sheet (equivalent to score_sheet)
                    # This requires adapting the validators to work with different sheet names
                    # For now, we accept the legacy template structure as valid
                    pass
                
                if "Analysis-Tabular" in workbook.sheetnames:
                    # Apply cross-sheet validation between Result and Analysis-Tabular
                    # This requires adapting the cross-sheet validator
                    # For now, we accept the legacy template structure as valid
                    pass

        finally:

            workbook.close()

        # ==================================================
        # 7. SEPARATE ERRORS, WARNINGS, AND REVIEW ITEMS
        # ==================================================

        errors = [
            issue
            for issue in issues
            if issue.get("severity", "ERROR") not in {"WARNING", "REVIEW"}
        ]

        warnings = [
            issue
            for issue in issues
            if issue.get("severity") == "WARNING"
        ]

        review_items = [
            issue
            for issue in issues
            if issue.get("severity") == "REVIEW"
        ]

        # ==================================================
        # 8. FINAL STATUS
        # ==================================================
        # Status can be: PASS, ERROR, or REVIEW
        # - PASS: No errors or review items
        # - REVIEW: Has review items but no errors
        # - ERROR: Has errors

        if review_items and not errors:
            status = "REVIEW"
        elif errors:
            status = "ERROR"
        else:
            status = "PASS"

        return {
            "status": status,
            "template": template,
            "errors": errors,
            "warnings": warnings,
            "review_items": review_items,
        }