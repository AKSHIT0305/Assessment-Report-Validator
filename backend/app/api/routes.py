from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)

from backend.app.core.config import INCOMING_DIR
from backend.app.services.excel_validator import ExcelValidator


router = APIRouter(prefix="/api")

validator = ExcelValidator()


@router.post("/validate")
async def validate(
    files: Annotated[list[UploadFile], File()]
):

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files were provided."
        )

    INCOMING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    for file in files:

        # --------------------------------------------------
        # File extension
        # --------------------------------------------------

        if not file.filename:

            results.append({
                "filename": "unknown",
                "status": "ERROR",
                "errors": [{
                    "code": "INVALID_FILENAME",
                    "category": "File",
                    "message": "Invalid filename.",
                    "sheet": None,
                    "cell": None,
                    "expected": "Valid filename",
                    "actual": None,
                }],
                "warnings": [],
            })

            continue

        extension = Path(
            file.filename
        ).suffix.lower()

        if extension not in {
            ".xlsx",
            ".xlsm"
        }:

            results.append({
                "filename": file.filename,
                "status": "ERROR",
                "errors": [{
                    "code": "INVALID_FILE_TYPE",
                    "category": "File",
                    "message": (
                        "Only .xlsx and .xlsm files "
                        "are supported."
                    ),
                    "sheet": None,
                    "cell": None,
                    "expected": [
                        ".xlsx",
                        ".xlsm"
                    ],
                    "actual": extension,
                }],
                "warnings": [],
            })

            continue

        # --------------------------------------------------
        # Save file
        # --------------------------------------------------

        destination = (
            INCOMING_DIR /
            file.filename
        )

        try:

            content = await file.read()

            destination.write_bytes(
                content
            )

        except Exception as exc:

            results.append({
                "filename": file.filename,
                "status": "ERROR",
                "errors": [{
                    "code": "FILE_SAVE_FAILED",
                    "category": "File",
                    "message": "Could not save uploaded file.",
                    "sheet": None,
                    "cell": None,
                    "expected": "File saved successfully",
                    "actual": str(exc),
                }],
                "warnings": [],
            })

            continue

        # --------------------------------------------------
        # Actual Excel validation
        # --------------------------------------------------

        validation_result = validator.validate(
            destination
        )

        results.append({
            "filename": file.filename,
            **validation_result,
        })

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    correct_files = [
        result["filename"]
        for result in results
        if result["status"] == "PASS"
    ]

    incorrect_files = [
        result
        for result in results
        if result["status"] == "ERROR"
    ]

    total_files = len(results)

    correct_count = len(
        correct_files
    )

    incorrect_count = len(
        incorrect_files
    )

    return {
        "total_files": total_files,

        "summary": {
            "correct": correct_count,
            "incorrect": incorrect_count,
            "percentage_correct": (
                round(
                    correct_count /
                    total_files *
                    100,
                    2
                )
                if total_files
                else 0
            ),
        },

        "correct_files": correct_files,

        "incorrect_files": incorrect_files,

        "files": results,
    }