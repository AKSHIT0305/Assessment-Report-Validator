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
    # --------------------------------------------------

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

        if " - Score" in nos:

            nos = nos.split(
                " - Score",
                1
            )[0].strip()

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

    return result


def _extract_score_from_header(header):
    """
    Extract maximum score from headers such as:

    SSC/N8417 - Score
    SSC/N8417 - Score 100
    SSC/N8417 - Score
    100
    """

    if header is None:
        return None

    if not isinstance(
        header,
        str
    ):
        return None

    # Only extract a score when the header looks like
    # an actual score header.
    if "score" not in header.lower():
        return None

    matches = re.findall(
        r"(\d+(?:\.\d+)?)",
        header
    )

    if not matches:
        return None

    return float(
        matches[-1]
    )


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