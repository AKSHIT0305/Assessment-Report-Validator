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

    # Per confirmed validation rules: Graph sheets are optional
    # Do not fail a workbook merely because a Graph sheet is absent
    OPTIONAL_SHEETS = {
        "Batch Analysis - Graph",
        "Analysis - Graph",
    }

    def validate(
        self,
        workbook,
        issues,
        template=None,
        sheet_mapping=None,
    ):
        # Per confirmed validation rules: ignore hidden sheets completely
        # Validation should focus only on the three relevant visible sheets
        existing_sheets = set(
            sheet_name
            for sheet_name in workbook.sheetnames
            if not workbook[sheet_name].sheet_state == 'hidden'
        )

        # --------------------------------------------------
        # Empty workbook
        # --------------------------------------------------

        if not existing_sheets:

            issues.append({
                "code": "NO_SHEETS",
                "category": "Workbook Structure",
                "message": "Workbook contains no visible worksheets.",
                "sheet": None,
                "cell": None,
                "expected": "At least one visible worksheet",
                "actual": "0 visible worksheets",
            })

            return

        # --------------------------------------------------
        # Determine required sheets using sheet mapping
        # --------------------------------------------------

        if sheet_mapping:
            # Use the provided sheet mapping from template detection
            required_sheets = {
                sheet_mapping.get("PRIMARY_DATA_SHEET"),
                sheet_mapping.get("TABULAR_ANALYSIS_SHEET"),
            }
            # Filter out None values
            required_sheets = {s for s in required_sheets if s is not None}
        elif template == "LEGACY_RESULT":

            required_sheets = self.LEGACY_REQUIRED_SHEETS - self.OPTIONAL_SHEETS

        elif template in {
            "STANDARD",
            "ALTERNATE_SCORE",
        }:

            required_sheets = self.STANDARD_REQUIRED_SHEETS - self.OPTIONAL_SHEETS
        else:
            # Fallback: try to identify sheets dynamically
            from backend.app.utils.sheet_mapper import SheetMapper
            primary = SheetMapper.identify_primary_data_sheet(workbook)
            tabular = SheetMapper.identify_tabular_analysis_sheet(workbook)
            
            required_sheets = set()
            if primary:
                required_sheets.add(primary)
            if tabular:
                required_sheets.add(tabular)

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

            # Check if worksheet is truly empty by examining all cells
            has_content = False
            for row in range(1, worksheet.max_row + 1):
                for col in range(1, worksheet.max_column + 1):
                    if worksheet.cell(row, col).value is not None:
                        has_content = True
                        break
                if has_content:
                    break
            
            if not has_content:

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
                    "cell": None,
                    "expected": "Populated worksheet",
                    "actual": "Empty",
                })