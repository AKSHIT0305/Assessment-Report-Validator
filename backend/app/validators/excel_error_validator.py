class ExcelErrorValidator:
    """
    Detects actual Excel error values in every worksheet.
    """

    EXCEL_ERRORS = {
        "#DIV/0!",
        "#VALUE!",
        "#REF!",
        "#NAME?",
        "#N/A",
        "#NUM!",
        "#NULL!",
        "#SPILL!",
        "#CALC!",
    }

    def validate(self, workbook, issues):

        for worksheet in workbook.worksheets:

            for row in worksheet.iter_rows():

                for cell in row:

                    value = cell.value

                    if value in self.EXCEL_ERRORS:

                        issues.append({
                            "code": "EXCEL_ERROR",
                            "category": "Excel Error",
                            "message": (
                                f"Excel error '{value}' "
                                f"found in cell {cell.coordinate}."
                            ),
                            "sheet": worksheet.title,
                            "cell": cell.coordinate,
                            "expected": "No Excel error",
                            "actual": value,
                        })