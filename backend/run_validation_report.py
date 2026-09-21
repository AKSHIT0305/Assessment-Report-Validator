#!/usr/bin/env python3
"""
Run validation against all test workbooks and generate a comprehensive report.
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.excel_validator import ExcelValidator


def main():
    test_data_dir = Path("/Users/akshitgoel/Desktop/office/assessment_report_validator/test_data")
    
    if not test_data_dir.exists():
        print(f"Test data directory not found: {test_data_dir}")
        return
    
    # Find all Excel files
    excel_files = list(test_data_dir.glob("*.xlsx")) + list(test_data_dir.glob("*.xls"))
    
    if not excel_files:
        print("No Excel files found in test data directory")
        return
    
    print(f"Found {len(excel_files)} Excel files to validate")
    print("=" * 80)
    
    validator = ExcelValidator()
    
    results = []
    pass_count = 0
    error_count = 0
    review_count = 0
    
    for file_path in sorted(excel_files):
        print(f"\nValidating: {file_path.name}")
        
        try:
            result = validator.validate(file_path)
            results.append({
                "filename": file_path.name,
                "status": result["status"],
                "template": result.get("template"),
                "error_count": len(result.get("errors", [])),
                "warning_count": len(result.get("warnings", [])),
                "review_count": len(result.get("review_items", [])),
                "errors": result.get("errors", []),
                "warnings": result.get("warnings", []),
                "review_items": result.get("review_items", []),
            })
            
            if result["status"] == "PASS":
                pass_count += 1
                print(f"  ✓ Status: PASS")
            elif result["status"] == "ERROR":
                error_count += 1
                print(f"  ✗ Status: ERROR ({len(result.get('errors', []))} errors)")
            elif result["status"] == "REVIEW":
                review_count += 1
                print(f"  ⚠ Status: REVIEW ({len(result.get('review_items', []))} review items)")
            
            if result.get("template"):
                print(f"  Template: {result['template']}")
                
        except Exception as e:
            print(f"  ✗ Error processing file: {e}")
            results.append({
                "filename": file_path.name,
                "status": "ERROR",
                "error": str(e),
            })
            error_count += 1
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total files: {len(excel_files)}")
    print(f"PASS: {pass_count} ({pass_count/len(excel_files)*100:.1f}%)")
    print(f"ERROR: {error_count} ({error_count/len(excel_files)*100:.1f}%)")
    print(f"REVIEW: {review_count} ({review_count/len(excel_files)*100:.1f}%)")
    
    # Detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    
    for result in results:
        print(f"\n{result['filename']}")
        print(f"  Status: {result['status']}")
        if result.get("template"):
            print(f"  Template: {result['template']}")
        
        if result.get("error_count", 0) > 0:
            print(f"  Errors ({result['error_count']}):")
            for error in result.get("errors", [])[:3]:  # Show first 3 errors
                print(f"    - {error.get('code')}: {error.get('message')}")
            if result['error_count'] > 3:
                print(f"    ... and {result['error_count'] - 3} more errors")
        
        if result.get("review_count", 0) > 0:
            print(f"  Review Items ({result['review_count']}):")
            for review_item in result.get("review_items", [])[:3]:  # Show first 3
                print(f"    - {review_item.get('code')}: {review_item.get('message')}")
            if result['review_count'] > 3:
                print(f"    ... and {result['review_count'] - 3} more review items")
    
    # Save detailed report to JSON
    report_path = Path("/Users/akshitgoel/Desktop/office/assessment_report_validator/validation_report.json")
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_files": len(excel_files),
            "pass_count": pass_count,
            "error_count": error_count,
            "review_count": review_count,
            "pass_percentage": pass_count/len(excel_files)*100 if excel_files else 0,
        },
        "results": results,
    }
    
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    main()