"""
Calculation Verifier - Independent verification of calculated values.

This module provides utilities to independently calculate expected values
and compare them against workbook values for verification.
"""
import math
import statistics
from collections import Counter


class CalculationVerifier:
    """
    Independently verifies calculated values against workbook data.
    
    When verification is possible, returns PASS/FAIL based on match.
    When verification is impossible, returns REVIEW with explanation.
    """
    
    # Tolerance for numeric comparisons
    COUNT_TOLERANCE = 0
    PERCENTAGE_TOLERANCE = 0.01
    DECIMAL_TOLERANCE = 0.001
    
    @staticmethod
    def verify_enrolled_count(primary_sheet, header_row, columns):
        """
        Independently calculate and verify enrolled candidates count.
        
        Args:
            primary_sheet: The primary data worksheet
            header_row: The header row number
            columns: Detected column positions
            
        Returns:
            Dictionary with 'expected', 'actual', 'match', 'status', 'tolerance'
        """
        try:
            # Calculate expected: count of all candidate rows
            candidate_id_col = columns.get("candidate_id")
            batch_id_col = columns.get("batch_id")
            
            candidate_rows = []
            for row in range(header_row + 1, primary_sheet.max_row + 1):
                # Use candidate_id or batch_id to identify candidate rows
                has_data = False
                if candidate_id_col:
                    value = primary_sheet.cell(row, candidate_id_col).value
                    if value is not None and str(value).strip() != "":
                        has_data = True
                elif batch_id_col:
                    value = primary_sheet.cell(row, batch_id_col).value
                    if value is not None and str(value).strip() != "":
                        has_data = True
                
                # Fallback: check if row has any non-empty cell
                if not has_data:
                    for col in range(1, primary_sheet.max_column + 1):
                        value = primary_sheet.cell(row, col).value
                        if value is not None and str(value).strip() != "":
                            has_data = True
                            break
                
                if has_data:
                    candidate_rows.append(row)
            
            expected = len(candidate_rows)
            
            return {
                "expected": expected,
                "actual": None,  # Will be filled by caller
                "match": None,  # Will be filled by caller
                "status": "CALCULATED",  # Indicates calculation was successful
                "tolerance": CalculationVerifier.COUNT_TOLERANCE,
                "verification_possible": True,
            }
            
        except Exception as e:
            return {
                "expected": None,
                "actual": None,
                "match": None,
                "status": "REVIEW",
                "tolerance": None,
                "verification_possible": False,
                "reason": f"Cannot calculate enrolled count: {str(e)}",
            }
    
    @staticmethod
    def verify_appeared_count(primary_sheet, header_row, columns, score_columns):
        """
        Independently calculate and verify appeared candidates count.
        
        Args:
            primary_sheet: The primary data worksheet
            header_row: The header row number
            columns: Detected column positions
            score_columns: Score column information
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Calculate expected: count of candidates with at least one non-null score
            candidate_id_col = columns.get("candidate_id")
            
            appeared_count = 0
            for row in range(header_row + 1, primary_sheet.max_row + 1):
                # Check if this row has candidate data
                has_candidate = False
                if candidate_id_col:
                    value = primary_sheet.cell(row, candidate_id_col).value
                    if value is not None and str(value).strip() != "":
                        has_candidate = True
                
                if not has_candidate:
                    continue
                
                # Check if candidate has at least one score
                has_score = False
                for score_info in score_columns:
                    score_col = score_info["score_column"]
                    value = primary_sheet.cell(row, score_col).value
                    if value is not None and isinstance(value, (int, float)) and not isinstance(value, bool):
                        has_score = True
                        break
                
                if has_score:
                    appeared_count += 1
            
            expected = appeared_count
            
            return {
                "expected": expected,
                "actual": None,
                "match": None,
                "status": "CALCULATED",
                "tolerance": CalculationVerifier.COUNT_TOLERANCE,
                "verification_possible": True,
            }
            
        except Exception as e:
            return {
                "expected": None,
                "actual": None,
                "match": None,
                "status": "REVIEW",
                "tolerance": None,
                "verification_possible": False,
                "reason": f"Cannot calculate appeared count: {str(e)}",
            }
    
    @staticmethod
    def verify_passed_count(primary_sheet, header_row, columns, score_columns, pass_criteria=0.8):
        """
        Independently calculate and verify passed candidates count.
        
        Args:
            primary_sheet: The primary data worksheet
            header_row: The header row number
            columns: Detected column positions
            score_columns: Score column information
            pass_criteria: Pass criteria as decimal (default 0.8 for 80%)
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Calculate expected: count of candidates who passed all NOS
            candidate_id_col = columns.get("candidate_id")
            pass_fail_col = columns.get("pass_fail")
            
            passed_count = 0
            for row in range(header_row + 1, primary_sheet.max_row + 1):
                # Check if this row has candidate data
                has_candidate = False
                if candidate_id_col:
                    value = primary_sheet.cell(row, candidate_id_col).value
                    if value is not None and str(value).strip() != "":
                        has_candidate = True
                
                if not has_candidate:
                    continue
                
                # If Pass/Fail column exists, use it
                if pass_fail_col:
                    pass_fail_value = primary_sheet.cell(row, pass_fail_col).value
                    if pass_fail_value is not None:
                        normalized = str(pass_fail_value).strip().lower()
                        if normalized in {"pass", "p", "yes", "y", "1", "true"}:
                            passed_count += 1
                            continue
                        elif normalized in {"fail", "f", "no", "n", "0", "false"}:
                            continue
                
                # Otherwise, calculate from scores
                scores = []
                for score_info in score_columns:
                    score_col = score_info["score_column"]
                    max_score = score_info["max_score"]
                    value = primary_sheet.cell(row, score_col).value
                    
                    if value is not None and isinstance(value, (int, float)) and not isinstance(value, bool):
                        scores.append((value, max_score))
                
                if not scores:
                    continue
                
                # Candidate passes if all scores >= pass_criteria * max_score
                candidate_passed = all(
                    score >= max_score * pass_criteria
                    for score, max_score in scores
                )
                
                if candidate_passed:
                    passed_count += 1
            
            expected = passed_count
            
            return {
                "expected": expected,
                "actual": None,
                "match": None,
                "status": "CALCULATED",
                "tolerance": CalculationVerifier.COUNT_TOLERANCE,
                "verification_possible": True,
                "pass_criteria_used": pass_criteria,
            }
            
        except Exception as e:
            return {
                "expected": None,
                "actual": None,
                "match": None,
                "status": "REVIEW",
                "tolerance": None,
                "verification_possible": False,
                "reason": f"Cannot calculate passed count: {str(e)}",
            }
    
    @staticmethod
    def verify_gender_counts(primary_sheet, header_row, columns):
        """
        Independently calculate and verify gender counts.
        
        Args:
            primary_sheet: The primary data worksheet
            header_row: The header row number
            columns: Detected column positions
            
        Returns:
            Dictionary with 'male_count', 'female_count' and verification status
        """
        try:
            gender_col = columns.get("gender")
            candidate_id_col = columns.get("candidate_id")
            
            male_count = 0
            female_count = 0
            
            for row in range(header_row + 1, primary_sheet.max_row + 1):
                # Check if this row has candidate data
                has_candidate = False
                if candidate_id_col:
                    value = primary_sheet.cell(row, candidate_id_col).value
                    if value is not None and str(value).strip() != "":
                        has_candidate = True
                
                if not has_candidate:
                    continue
                
                if gender_col:
                    gender = primary_sheet.cell(row, gender_col).value
                    if gender is not None:
                        normalized = str(gender).strip().lower()
                        if normalized in {"male", "m"}:
                            male_count += 1
                        elif normalized in {"female", "f"}:
                            female_count += 1
            
            return {
                "male_count": male_count,
                "female_count": female_count,
                "status": "CALCULATED",
                "verification_possible": True,
            }
            
        except Exception as e:
            return {
                "male_count": None,
                "female_count": None,
                "status": "REVIEW",
                "verification_possible": False,
                "reason": f"Cannot calculate gender counts: {str(e)}",
            }
    
    @staticmethod
    def verify_nos_statistics(primary_sheet, header_row, score_columns, candidate_rows, nos_name, max_score):
        """
        Independently calculate and verify NOS statistics.
        
        Args:
            primary_sheet: The primary data worksheet
            header_row: The header row number
            score_columns: Score column information
            candidate_rows: List of candidate row numbers
            nos_name: Name of the NOS to verify
            max_score: Maximum score for this NOS
            
        Returns:
            Dictionary with calculated statistics
        """
        try:
            # Find the score column for this NOS
            score_col = None
            for score_info in score_columns:
                if score_info["nos"] == nos_name:
                    score_col = score_info["score_column"]
                    break
            
            if score_col is None:
                return {
                    "mean": None,
                    "median": None,
                    "min": None,
                    "max": None,
                    "std_dev": None,
                    "pass_percentage": None,
                    "status": "REVIEW",
                    "verification_possible": False,
                    "reason": f"Score column not found for NOS: {nos_name}",
                }
            
            # Collect scores
            scores = []
            for row in candidate_rows:
                value = primary_sheet.cell(row, score_col).value
                if value is not None and isinstance(value, (int, float)) and not isinstance(value, bool):
                    scores.append(float(value))
            
            if not scores:
                return {
                    "mean": None,
                    "median": None,
                    "min": None,
                    "max": None,
                    "std_dev": None,
                    "pass_percentage": None,
                    "status": "REVIEW",
                    "verification_possible": False,
                    "reason": f"No scores found for NOS: {nos_name}",
                }
            
            # Calculate statistics
            mean = statistics.mean(scores)
            median = statistics.median(scores)
            minimum = min(scores)
            maximum = max(scores)
            
            passed_count = sum(1 for score in scores if score >= max_score * 0.8)
            pass_percentage = passed_count / len(scores)
            
            std_dev = None
            if len(scores) >= 2:
                std_dev = statistics.stdev(scores)
            
            return {
                "mean": mean,
                "median": median,
                "min": minimum,
                "max": maximum,
                "std_dev": std_dev,
                "pass_percentage": pass_percentage,
                "status": "CALCULATED",
                "verification_possible": True,
            }
            
        except Exception as e:
            return {
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
                "std_dev": None,
                "pass_percentage": None,
                "status": "REVIEW",
                "verification_possible": False,
                "reason": f"Cannot calculate NOS statistics: {str(e)}",
            }
    
    @staticmethod
    def compare_values(expected, actual, tolerance, field_name):
        """
        Compare expected and actual values and determine pass/fail/review status.
        
        Args:
            expected: The calculated expected value
            actual: The actual value from the workbook
            tolerance: Acceptable tolerance for comparison
            field_name: Name of the field being compared
            
        Returns:
            Dictionary with comparison result
        """
        if expected is None:
            return {
                "expected": expected,
                "actual": actual,
                "match": None,
                "status": "REVIEW",
                "reason": f"Expected value cannot be calculated for {field_name}",
            }
        
        if actual is None:
            return {
                "expected": expected,
                "actual": actual,
                "match": None,
                "status": "REVIEW",
                "reason": f"Actual value not found for {field_name}",
            }
        
        # Try to normalize actual value to numeric
        numeric_actual = CalculationVerifier.normalize_to_numeric(actual)
        
        if numeric_actual is None:
            return {
                "expected": expected,
                "actual": actual,
                "match": None,
                "status": "REVIEW",
                "reason": f"Actual value cannot be normalized for {field_name}",
            }
        
        # Compare values
        difference = abs(numeric_actual - expected)
        match = difference <= tolerance
        
        return {
            "expected": expected,
            "actual": actual,
            "numeric_actual": numeric_actual,
            "difference": difference,
            "match": match,
            "status": "PASS" if match else "FAIL",
            "tolerance": tolerance,
        }
    
    @staticmethod
    def normalize_to_numeric(value):
        """
        Normalize various value representations to numeric.
        
        Args:
            value: The value to normalize
            
        Returns:
            Numeric value or None if not parseable
        """
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        
        if not isinstance(value, str):
            return None
        
        value = value.strip()
        
        # Handle percentage format
        if value.endswith("%"):
            try:
                return float(value.rstrip("%")) / 100
            except ValueError:
                pass
        
        # Handle text representations
        if "percent" in value.lower():
            try:
                num_part = value.lower().replace("percent", "").strip()
                return float(num_part) / 100
            except ValueError:
                pass
        
        # Handle decimal
        try:
            return float(value)
        except ValueError:
            pass
        
        return None