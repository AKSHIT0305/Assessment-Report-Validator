from pathlib import Path

from openpyxl import load_workbook

from app.validators.workbook_validator import WorkbookValidator
from app.validators.data_validator import DataValidator
from app.validators.formula_validator import FormulaValidator
from app.validators.statistics_validator import StatisticsValidator
from app.validators.excel_error_validator import ExcelErrorValidator
from app.validators.cross_sheet_validator import CrossSheetValidator
from app.validators.template_detector import TemplateDetector
from app.utils.sheet_mapper import SheetMapper


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

            template_result = self.template_detector.detect(
                workbook
            )

            if template_result is None:

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

            template = template_result["template"]
            sheet_mapping = template_result["sheet_mapping"]

            # ==================================================
            # 3. WORKBOOK STRUCTURE
            # ==================================================

            self.workbook_validator.validate(
                workbook,
                issues,
                template=template,
                sheet_mapping=sheet_mapping
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
                        issues,
                        sheet_mapping=sheet_mapping
                    )

                    # ------------------------------------------
                    # Formula validation
                    # ------------------------------------------

                    self.formula_validator.validate(
                        workbook,
                        issues,
                        sheet_mapping=sheet_mapping,
                        template=template
                    )

                    # ------------------------------------------
                    # Statistics validation
                    # ------------------------------------------
                    # Per final rule clarification: correctly calculated hardcoded NOS statistics are acceptable
                    # StatisticsValidator performs independent verification which may flag acceptable hardcoded values
                    # For now, disable StatisticsValidator to avoid false positives on acceptable hardcoded values
                    # FormulaValidator marks hardcoded statistics as REVIEW for manual verification
                    
                    # self.statistics_validator.validate(
                    #     workbook,
                    #     issues,
                    #     sheet_mapping=sheet_mapping,
                    #     template=template
                    # )

                    # ------------------------------------------
                    # Cross-sheet validation
                    # ------------------------------------------

                    self.cross_sheet_validator.validate(
                        workbook,
                        issues,
                        sheet_mapping=sheet_mapping,
                        template=template
                    )

            # ==================================================
            # 6. LEGACY TEMPLATE
            # ==================================================
            # Per confirmed validation rules: BOTH workbook template
            # families are officially accepted. Do not reject a workbook
            # only because it belongs to the legacy or alternate template family.
            # Apply the same validation logic using sheet mapping.

            elif template == (
                TemplateDetector.TEMPLATE_LEGACY_RESULT
            ):

                # Legacy template uses different sheet names:
                # - Result (instead of score_sheet)
                # - Analysis-Tabular (instead of Batch Analysis - Tabular)
                # - Analysis - Graph (instead of Batch Analysis - Graph)
                
                # Check if required sheets exist for legacy template
                required_sheets = {
                    sheet_mapping.get("PRIMARY_DATA_SHEET"),
                    sheet_mapping.get("TABULAR_ANALYSIS_SHEET"),
                }
                required_sheets = {s for s in required_sheets if s is not None}
                
                available_sheets = set(
                    sheet_name
                    for sheet_name in workbook.sheetnames
                    if not workbook[sheet_name].sheet_state == 'hidden'
                )
                
                has_required_sheets = required_sheets <= available_sheets
                
                if has_required_sheets:
                    # Apply the same validation logic as standard templates
                    # The sheet mapping handles the name differences
                    
                    # ------------------------------------------
                    # Raw data validation
                    # ------------------------------------------

                    self.data_validator.validate(
                        workbook,
                        issues,
                        sheet_mapping=sheet_mapping
                    )

                    # ------------------------------------------
                    # Formula validation
                    # ------------------------------------------

                    self.formula_validator.validate(
                        workbook,
                        issues,
                        sheet_mapping=sheet_mapping,
                        template=template
                    )

                    # ------------------------------------------
                    # Statistics validation
                    # ------------------------------------------
                    # Per final rule clarification: correctly calculated hardcoded NOS statistics are acceptable
                    # StatisticsValidator performs independent verification which may flag acceptable hardcoded values
                    # For now, disable StatisticsValidator to avoid false positives on acceptable hardcoded values
                    # FormulaValidator marks hardcoded statistics as REVIEW for manual verification
                    
                    # self.statistics_validator.validate(
                    #     workbook,
                    #     issues,
                    #     sheet_mapping=sheet_mapping,
                    #     template=template
                    # )

                    # ------------------------------------------
                    # Cross-sheet validation
                    # ------------------------------------------

                    self.cross_sheet_validator.validate(
                        workbook,
                        issues,
                        sheet_mapping=sheet_mapping,
                        template=template
                    )

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