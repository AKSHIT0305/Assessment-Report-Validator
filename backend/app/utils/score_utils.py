import re


def get_score_columns(ws):
    """
    Dynamically identifies score/pass-fail column pairs.

    The function searches the workbook header area instead of
    assuming that score headers always occur on row 12.

    Returns:

    [
        {
            "score_column": 6,
            "pass_fail_column": 7,
            "nos": "SSC/N8417",
            "max_score": 100
        },
        ...
    ]
    """

    result = []

    # --------------------------------------------------
    # Search possible header rows
    # --------------------------------------------------

    header_candidates = []

    for row in range(
        1,
        min(ws.max_row, 20) + 1
    ):

        score_header_count = 0
        pass_fail_count = 0

        for column in range(
            1,
            ws.max_column + 1
        ):

            value = ws.cell(
                row,
                column
            ).value

            if not isinstance(value, str):
                continue

            normalized = value.strip().lower()

            if "pass/fail" in normalized:
                pass_fail_count += 1

            if (
                "score" in normalized
                or _extract_score_from_header(value) is not None
                or _is_score_header_pattern(value)
            ):
                score_header_count += 1

        if (
            score_header_count > 0
            and pass_fail_count > 0
        ):
            header_candidates.append(
                (
                    row,
                    score_header_count,
                    pass_fail_count,
                )
            )

    if not header_candidates:
        return []

    # Prefer the row with the most score/pass-fail headers.
    header_row = max(
        header_candidates,
        key=lambda item: (
            item[1] + item[2],
            item[2],
        )
    )[0]

    # --------------------------------------------------
    # Identify every Pass/Fail column
    # and look immediately to its left for score.
    # Pass/Fail columns are optional per confirmed validation rules.
    # --------------------------------------------------

    has_pass_fail = False
    for pass_fail_column in range(
        1,
        ws.max_column + 1
    ):

        pass_header = ws.cell(
            header_row,
            pass_fail_column
        ).value

        if not isinstance(
            pass_header,
            str
        ):
            continue

        if "pass/fail" not in pass_header.lower():
            continue

        has_pass_fail = True
        score_column = pass_fail_column - 1

        if score_column < 1:
            continue

        score_header = ws.cell(
            header_row,
            score_column
        ).value

        if score_header is None:
            continue

        # --------------------------------------------------
        # Determine maximum score
        # --------------------------------------------------

        max_score = _extract_score_from_header(
            score_header
        )

        if max_score is None:

            # Search first few candidate rows for a formula
            # that reveals the maximum score.
            for row in range(
                header_row + 1,
                min(
                    ws.max_row,
                    header_row + 10
                ) + 1
            ):

                formula = ws.cell(
                    row,
                    pass_fail_column
                ).value

                max_score = _extract_score_from_formula(
                    formula
                )

                if max_score is not None:
                    break

        if max_score is None:
            continue

        # --------------------------------------------------
        # NOS name
        # --------------------------------------------------

        nos = str(
            score_header
        ).strip()

        # Handle different score header patterns
        if " - Score" in nos:
            nos = nos.split(
                " - Score",
                1
            )[0].strip()
        elif "-Score" in nos:
            nos = nos.split(
                "-Score",
                1
            )[0].strip()
        elif _is_score_header_pattern(nos):
            # Extract NOS from pattern like "SSC/N2204-100.0"
            # Remove the score part at the end
            if "-" in nos:
                nos = nos.rsplit("-", 1)[0].strip()

        # Handle multiline headers.
        nos = nos.split(
            "\n",
            1
        )[0].strip()

        result.append({
            "score_column": score_column,
            "pass_fail_column": pass_fail_column,
            "nos": nos,
            "max_score": float(max_score),
        })

    # If no Pass/Fail columns found, try to identify score columns independently
    if not has_pass_fail:
        for column in range(1, ws.max_column + 1):
            header = ws.cell(header_row, column).value
            if header is None:
                continue
            
            normalized = str(header).strip().lower()
            
            # Check if this is a score column (with or without "score" word)
            if "score" in normalized or _is_score_header_pattern(header):
                score_column = column
                
                # Determine maximum score
                max_score = _extract_score_from_header(header)
                
                if max_score is None:
                    # Search first few candidate rows for a formula
                    for row in range(header_row + 1, min(ws.max_row, header_row + 10) + 1):
                        # Look for any formula in this column that might reveal max score
                        cell_value = ws.cell(row, score_column).value
                        if isinstance(cell_value, str) and cell_value.startswith("="):
                            max_score = _extract_score_from_formula(cell_value)
                            if max_score is not None:
                                break
                
                if max_score is None:
                    # If we still can't find max score, check if the column contains numeric data
                    # and use a default of 100 (common maximum score)
                    has_numeric_data = False
                    for row in range(header_row + 1, min(ws.max_row, header_row + 5) + 1):
                        cell_value = ws.cell(row, score_column).value
                        if isinstance(cell_value, (int, float)) and not isinstance(cell_value, bool):
                            has_numeric_data = True
                            break
                    
                    if has_numeric_data:
                        max_score = 100.0  # Default to 100 if we can't determine otherwise
                    else:
                        continue
                
                # NOS name
                nos = str(header).strip()
                if " - Score" in nos:
                    nos = nos.split(" - Score", 1)[0].strip()
                elif "-Score" in nos:
                    nos = nos.split("-Score", 1)[0].strip()
                elif _is_score_header_pattern(nos):
                    if "-" in nos:
                        nos = nos.rsplit("-", 1)[0].strip()
                
                nos = nos.split("\n", 1)[0].strip()
                
                result.append({
                    "score_column": score_column,
                    "pass_fail_column": None,  # No Pass/Fail column
                    "nos": nos,
                    "max_score": float(max_score),
                })

    return result


def _extract_score_from_header(header):
    """
    Extract maximum score from headers such as:

    SSC/N8417 - Score
    SSC/N8417 - Score 100
    SSC/N8417 - Score
    100
    SSC/N2204-100.0
    SSC/N2204-100
    """

    if header is None:
        return None

    if not isinstance(
        header,
        str
    ):
        return None

    # First try the traditional "score" word pattern
    if "score" in header.lower():
        matches = re.findall(
            r"(\d+(?:\.\d+)?)",
            header
        )

        if matches:
            return float(
                matches[-1]
            )
    
    # If no "score" word, try the pattern approach
    return _extract_score_from_pattern(header)


def _extract_score_from_formula(formula):
    """
    Extract maximum score from formulas such as:

    =IF(F13/100*100>=80,"Pass","Fail")

    =IF(R13/50*100>=80,"Pass","Fail")
    """

    if formula is None:
        return None

    if not isinstance(
        formula,
        str
    ):
        return None

    # Formula may contain _xlfn or other Excel prefixes.
    match = re.search(
        r"/\s*(\d+(?:\.\d+)?)\s*\*\s*100",
        formula,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return float(
        match.group(1)
    )


def _is_score_header_pattern(header):
    """
    Identify score header patterns that don't contain "score" word.
    
    Recognizes patterns like:
    - SSC/N2204-100.0
    - SSC/N2204-100
    - MEP/N2601-50
    
    These follow the pattern: PREFIX/NUMBER-SCORE
    """
    if header is None:
        return False
    
    if not isinstance(header, str):
        return False
    
    # Check for pattern like "SSC/N2204-100.0" or "SSC/N2204-100"
    # Pattern: letters/letters-numbers dash number
    pattern = r'^[A-Z]+/[A-Z0-9]+-\d+(?:\.\d+)?$'
    
    if re.match(pattern, header.strip(), re.IGNORECASE):
        return True
    
    return False


def _extract_score_from_pattern(header):
    """
    Extract maximum score from pattern headers like:
    - SSC/N2204-100.0
    - SSC/N2204-100
    - MEP/N2601-50
    """
    if header is None:
        return None
    
    if not isinstance(header, str):
        return None
    
    # Extract the number after the final dash
    # Pattern: something-123 or something-123.45
    match = re.search(r'-(\d+(?:\.\d+)?)$', header.strip())
    
    if match:
        return float(match.group(1))
    
    return None