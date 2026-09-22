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
    
    # Generate consolidated review evidence report
    print("\n" + "=" * 80)
    print("REVIEW EVIDENCE REPORT")
    print("=" * 80)
    
    review_workbooks = [r for r in results if r.get("review_count", 0) > 0]
    
    if review_workbooks:
        print(f"\n{len(review_workbooks)} workbooks require review:\n")
        
        for result in review_workbooks:
            print(f"\n{'='*80}")
            print(f"Workbook: {result['filename']}")
            print(f"Status: {result['status']}")
            print(f"Template: {result.get('template', 'N/A')}")
            print(f"Total Review Items: {result['review_count']}")
            print(f"{'='*80}\n")
            
            for i, review_item in enumerate(result.get("review_items", []), 1):
                print(f"Review Item #{i}:")
                print(f"  Type: {review_item.get('code')}")
                print(f"  Sheet: {review_item.get('sheet', 'N/A')}")
                print(f"  Cell: {review_item.get('cell', 'N/A')}")
                print(f"  Actual Value: {review_item.get('actual', 'N/A')}")
                print(f"  Expected: {review_item.get('expected', 'N/A')}")
                print(f"  Message: {review_item.get('message')}")
                
                # Generate plain-English review instruction
                review_type = review_item.get('code')
                instruction = ""
                
                if review_type == "HARDCODED_SUMMARY_REVIEW":
                    instruction = "What the reviewer needs to check: Compare the hardcoded summary value against the underlying candidate data to verify accuracy."
                elif review_type == "HARDCODED_PASS_FAIL_REVIEW":
                    instruction = "What the reviewer needs to check: Find the declared pass criterion in the workbook and verify that the hardcoded Pass/Fail values correspond to the candidate scores."
                elif review_type == "NOS_STATISTIC_REVIEW":
                    instruction = "What the reviewer needs to check: Verify that the hardcoded NOS statistic matches the underlying candidate/NOS assessment data."
                else:
                    instruction = "What the reviewer needs to check: Review the item manually to verify correctness."
                
                print(f"  {instruction}")
                print()
        
        # Generate CSV-style summary table (truncated to first 5 items per workbook for readability)
        print(f"\n{'='*80}")
        print("CONSOLIDATED REVIEW TABLE (Sample - first 5 items per workbook)")
        print(f"{'='*80}\n")
        print("Workbook | Status | Review Type | Sheet | Cell | Actual Value | Review Instruction")
        print("-" * 200)
        
        for result in review_workbooks:
            count = 0
            for review_item in result.get("review_items", []):
                if count >= 5:  # Show only first 5 per workbook
                    print(f"{result['filename'][:20]} | {result['status'][:6]} | ... ({result['review_count'] - 5} more items)")
                    break
                
                review_type = review_item.get('code')
                instruction = ""
                
                if review_type == "HARDCODED_SUMMARY_REVIEW":
                    instruction = "Compare hardcoded summary against candidate data"
                elif review_type == "HARDCODED_PASS_FAIL_REVIEW":
                    instruction = "Verify Pass/Fail against declared pass criterion"
                elif review_type == "NOS_STATISTIC_REVIEW":
                    instruction = "Verify statistic matches assessment data"
                else:
                    instruction = "Manual review required"
                
                actual_val = str(review_item.get('actual', 'N/A'))[:20]  # Truncate long values
                print(f"{result['filename'][:20]} | {result['status'][:6]} | {review_type[:25]} | {review_item.get('sheet', 'N/A')[:20]} | {review_item.get('cell', 'N/A')[:10]} | {actual_val} | {instruction}")
                count += 1
        
        print(f"\n{'='*80}")
        print(f"Full review details available in: review_evidence_report.txt")
        print(f"{'='*80}")
        
        # Write full review evidence to file
        review_report_path = Path("/Users/akshitgoel/Desktop/office/assessment_report_validator/review_evidence_report.txt")
        with open(review_report_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("REVIEW EVIDENCE REPORT - FULL DETAILS\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total workbooks requiring review: {len(review_workbooks)}\n\n")
            
            for result in review_workbooks:
                f.write("=" * 80 + "\n")
                f.write(f"Workbook: {result['filename']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Template: {result.get('template', 'N/A')}\n")
                f.write(f"Total Review Items: {result['review_count']}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, review_item in enumerate(result.get("review_items", []), 1):
                    f.write(f"Review Item #{i}:\n")
                    f.write(f"  Type: {review_item.get('code')}\n")
                    f.write(f"  Sheet: {review_item.get('sheet', 'N/A')}\n")
                    f.write(f"  Cell: {review_item.get('cell', 'N/A')}\n")
                    f.write(f"  Actual Value: {review_item.get('actual', 'N/A')}\n")
                    f.write(f"  Expected: {review_item.get('expected', 'N/A')}\n")
                    f.write(f"  Message: {review_item.get('message')}\n")
                    
                    review_type = review_item.get('code')
                    instruction = ""
                    
                    if review_type == "HARDCODED_SUMMARY_REVIEW":
                        instruction = "What the reviewer needs to check: Compare the hardcoded summary value against the underlying candidate data to verify accuracy."
                    elif review_type == "HARDCODED_PASS_FAIL_REVIEW":
                        instruction = "What the reviewer needs to check: Find the declared pass criterion in the workbook and verify that the hardcoded Pass/Fail values correspond to the candidate scores."
                    elif review_type == "NOS_STATISTIC_REVIEW":
                        instruction = "What the reviewer needs to check: Verify that the hardcoded NOS statistic matches the underlying candidate/NOS assessment data."
                    else:
                        instruction = "What the reviewer needs to check: Review the item manually to verify correctness."
                    
                    f.write(f"  {instruction}\n\n")
                
                f.write("\n")
        
        print(f"Full review evidence written to: {review_report_path}")
    else:
        print("\nNo workbooks require review.")


if __name__ == "__main__":
    main()