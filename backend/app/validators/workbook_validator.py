class WorkbookValidator:
    """
    Validates workbook-level structure.

    Different assessment report templates have different
    worksheet requirements.
    """

    STANDARD_REQUIRED_SHEETS = {
        "score_sheet",
        "Batch Analysis - Tabular",
        "Batch Analysis - Graph",
    }

    LEGACY_REQUIRED_SHEETS = {
        "Result",
        "Analysis-Tabular",
        "Analysis - Graph",
    }

    def validate(
        self,
        workbook,
        issues,
        template=None,
    ):
        existing_sheets = set(workbook.sheetnames)

        # --------------------------------------------------
        # Empty workbook
        # --------------------------------------------------

        if not workbook.sheetnames:

            issues.append({
                "code": "NO_SHEETS",
                "category": "Workbook Structure",
                "message": "Workbook contains no worksheets.",
                "sheet": None,
                "cell": None,
                "expected": "At least one worksheet",
                "actual": "0 worksheets",
            })

            return

        # --------------------------------------------------
        # Determine required sheets
        # --------------------------------------------------

        if template == "LEGACY_RESULT":

            required_sheets = self.LEGACY_REQUIRED_SHEETS

        elif template in {
            "STANDARD",
            "ALTERNATE_SCORE",
        }:

            required_sheets = self.STANDARD_REQUIRED_SHEETS

        else:

            # Unknown template:
            # don't blindly apply STANDARD requirements.
            return

        # --------------------------------------------------
        # Required sheets
        # --------------------------------------------------

        missing_sheets = (
            required_sheets - existing_sheets
        )

        for sheet_name in sorted(missing_sheets):

            issues.append({
                "code": "MISSING_SHEET",
                "category": "Workbook Structure",
                "message": (
                    f"Required sheet is missing: "
                    f"{sheet_name}"
                ),
                "sheet": sheet_name,
                "cell": None,
                "expected": "Sheet exists",
                "actual": "Missing",
            })

        # --------------------------------------------------
        # Empty required sheets
        #
        # A graph sheet may legitimately be empty in some
        # generated reports, so it is NOT treated as an
        # automatic error.
        # --------------------------------------------------

        for sheet_name in required_sheets:

            if sheet_name not in existing_sheets:
                continue

            worksheet = workbook[sheet_name]

            if (
                worksheet.max_row == 1
                and worksheet.max_column == 1
                and worksheet["A1"].value is None
            ):

                # Graph sheets are allowed to be empty.
                if "Graph" in sheet_name:
                    continue

                issues.append({
                    "code": "EMPTY_SHEET",
                    "category": "Workbook Structure",
                    "message": (
                        f"Required sheet '{sheet_name}' "
                        "is empty."
                    ),
                    "sheet": sheet_name,
                    "cell": "A1",
                    "expected": "Populated worksheet",
                    "actual": "Empty",
                })