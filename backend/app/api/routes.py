from pathlib import Path
from typing import Annotated
from datetime import datetime
import json
import os

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
)

from app.core.config import INCOMING_DIR
from app.services.excel_validator import ExcelValidator


router = APIRouter(prefix="/api")

validator = ExcelValidator()

# File history storage
HISTORY_FILE = Path("/Users/akshitgoel/Desktop/office/assessment_report_validator/file_history.json")
REVIEW_STATE_FILE = Path("/Users/akshitgoel/Desktop/office/assessment_report_validator/review_state.json")

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def load_review_state():
    if REVIEW_STATE_FILE.exists():
        with open(REVIEW_STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_review_state(state):
    with open(REVIEW_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


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
            destination,
            filename=file.filename
        )

        # Save to history
        history = load_history()
        history_entry = {
            "filename": file.filename,
            "timestamp": datetime.now().isoformat(),
            "status": validation_result["status"],
            "template": validation_result.get("template"),
            "error_count": len(validation_result.get("errors", [])),
            "review_count": len(validation_result.get("review_items", [])),
            "validation_result": validation_result,
            "review_state": "PENDING" if validation_result["status"] in ["REVIEW", "ERROR"] else "VERIFIED",
            "ai_review": validation_result.get("ai_review")
        }
        history.append(history_entry)
        save_history(history)

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

    review_files = [
        result
        for result in results
        if result["status"] == "REVIEW"
    ]

    total_files = len(results)

    correct_count = len(
        correct_files
    )

    incorrect_count = len(
        incorrect_files
    )

    review_count = len(
        review_files
    )

    return {
        "total_files": total_files,

        "summary": {
            "correct": correct_count,
            "incorrect": incorrect_count,
            "review": review_count,
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

        "review_files": review_files,

        "files": results,
    }


@router.get("/history")
async def get_history():
    """Get complete file validation history."""
    history = load_history()
    return {
        "history": history,
        "total": len(history)
    }


@router.get("/history/{filename}")
async def get_file_history(filename: str):
    """Get history for a specific file."""
    history = load_history()
    file_records = [record for record in history if record["filename"] == filename]
    
    if not file_records:
        raise HTTPException(status_code=404, detail="File not found in history")
    
    return {
        "filename": filename,
        "records": file_records
    }


@router.get("/review-state")
async def get_review_state():
    """Get current review state for all files."""
    history = load_history()
    review_state = load_review_state()
    
    # Filter files that need review (REVIEW or ERROR status)
    pending_files = [
        {
            "filename": record["filename"],
            "timestamp": record["timestamp"],
            "status": record["status"],
            "template": record.get("template"),
            "error_count": record["error_count"],
            "review_count": record["review_count"],
            "review_state": review_state.get(record["filename"], "PENDING"),
            "validation_result": record["validation_result"]
        }
        for record in history
        if record["status"] in ["REVIEW", "ERROR"]
    ]
    
    return {
        "pending_files": pending_files,
        "total": len(pending_files)
    }


@router.post("/review-state/{filename}")
async def update_review_state(filename: str, decision: dict):
    """Update review state for a file (VERIFIED or INCORRECT)."""
    history = load_history()
    review_state = load_review_state()
    
    # Check if file exists in history
    file_exists = any(record["filename"] == filename for record in history)
    if not file_exists:
        raise HTTPException(status_code=404, detail="File not found in history")
    
    # Update review state
    decision_type = decision.get("decision")
    if decision_type not in ["VERIFIED", "INCORRECT"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be VERIFIED or INCORRECT")
    
    review_state[filename] = {
        "decision": decision_type,
        "timestamp": datetime.now().isoformat(),
        "reviewer": decision.get("reviewer", "system")
    }
    save_review_state(review_state)
    
    # Update the latest history entry
    for record in reversed(history):
        if record["filename"] == filename:
            record["review_state"] = decision_type
            break
    save_history(history)
    
    return {
        "filename": filename,
        "review_state": decision_type
    }