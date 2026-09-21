"""
Workbook Analyzer - Dynamic detection of workbook structure.

This module provides utilities to analyze workbook structure dynamically
without relying on fixed cell references or row/column positions.
"""
import re


class WorkbookAnalyzer:
    """
    Analyzes workbook structure dynamically based on content patterns,
    labels, and meaningful structure rather than fixed positions.
    """
    
    # Common patterns for detection
    CANDIDATE_ID_PATTERNS = {"candidate id", "candidateid", "candidate", "candidate_id"}
    BATCH_ID_PATTERNS = {"batch id", "batchid", "batch", "batch_id"}
    GENDER_PATTERNS = {"gender", "sex"}
    ASSESSMENT_DATE_PATTERNS = {"assessment date", "assessmentdate", "date of assessment"}
    SCORE_PATTERNS = {"score", "marks", "points"}
    PASS_FAIL_PATTERNS = {"pass/fail", "passfail", "result", "status"}
    
    # NOS code prefixes
    NOS_PREFIXES = ["SSC/", "MEP/", "DGT/", "TEL/", "AGRI/", "ELE/", "CONS/"]
    
    # Summary label patterns
    SUMMARY_LABEL_PATTERNS = {
        "enrolled": ["enrolled", "total enrolled", "enrolled candidates", "total candidates"],
        "appeared": ["appeared", "total appeared", "appeared candidates", "present"],
        "passed": ["passed", "total passed", "passed candidates", "qualified"],
        "male": ["male", "male candidates", "total male", "male count"],
        "female": ["female", "female candidates", "total female", "female count"],
    }
    
    @staticmethod
    def normalize_text(value):
        """
        Normalize text for comparison.
        
        Args:
            value: The value to normalize
            
        Returns:
            Normalized string
        """
        if value is None:
            return ""
        
        return " ".join(
            str(value)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
            .split()
        )
    
    @staticmethod
    def find_header_row(worksheet):
        """
        Find the header row by searching for candidate-related headers.
        
        Args:
            worksheet: The worksheet to analyze
            
        Returns:
            Row number of header row or None if not found
        """
        # Search entire worksheet for Candidate ID header
        for row in range(1, worksheet.max_row + 1):
            for col in range(1, worksheet.max_column + 1):
                value = worksheet.cell(row, col).value
                if value is None:
                    continue
                
                normalized = WorkbookAnalyzer.normalize_text(value)
                
                if normalized in WorkbookAnalyzer.CANDIDATE_ID_PATTERNS:
                    return row
        
        return None
    
    @staticmethod
    def find_data_region(worksheet, header_row):
        """
        Find the data region (start and end rows) based on actual data.
        
        Args:
            worksheet: The worksheet to analyze
            header_row: The row number of the header
            
        Returns:
            Tuple of (data_start_row, data_end_row) or None if no data found
        """
        if header_row is None:
            return None
        
        # Data starts immediately after header
        data_start_row = header_row + 1
        
        # Find the last row with actual data
        data_end_row = header_row
        
        for row in range(header_row + 1, worksheet.max_row + 1):
            # Check if this row has any non-empty cell
            has_data = False
            for col in range(1, worksheet.max_column + 1):
                value = worksheet.cell(row, col).value
                if value is not None and str(value).strip() != "":
                    has_data = True
                    break
            
            if has_data:
                data_end_row = row
            else:
                # Empty row - check if there might be more data below
                # Sometimes there are blank rows in the middle
                pass
        
        if data_end_row <= header_row:
            return None
        
        return (data_start_row, data_end_row)
    
    @staticmethod
    def detect_columns(worksheet, header_row):
        """
        Detect column positions by analyzing header row.
        
        Args:
            worksheet: The worksheet to analyze
            header_row: The row number of the header
            
        Returns:
            Dictionary mapping column names to column numbers
        """
        columns = {}
        
        if header_row is None:
            return columns
        
        for col in range(1, worksheet.max_column + 1):
            value = worksheet.cell(header_row, col).value
            if value is None:
                continue
            
            normalized = WorkbookAnalyzer.normalize_text(value)
            
            # Check for various column types
            if normalized in WorkbookAnalyzer.CANDIDATE_ID_PATTERNS:
                columns["candidate_id"] = col
            elif normalized in WorkbookAnalyzer.BATCH_ID_PATTERNS:
                columns["batch_id"] = col
            elif normalized in WorkbookAnalyzer.GENDER_PATTERNS:
                columns["gender"] = col
            elif normalized in WorkbookAnalyzer.ASSESSMENT_DATE_PATTERNS:
                columns["assessment_date"] = col
            elif any(pattern in normalized for pattern in WorkbookAnalyzer.SCORE_PATTERNS):
                # This is a score column - we'll handle it separately
                pass
        
        return columns
    
    @staticmethod
    def find_summary_section(worksheet):
        """
        Find the summary section by looking for summary labels and their values.
        
        Args:
            worksheet: The worksheet to analyze
            
        Returns:
            Dictionary mapping summary field names to their cell coordinates
        """
        summary_cells = {}
        
        # Search for summary section indicators
        summary_section_found = False
        summary_start_row = None
        
        for row in range(1, min(worksheet.max_row, 50) + 1):
            for col in range(1, min(worksheet.max_column, 10) + 1):
                value = worksheet.cell(row, col).value
                if value is None:
                    continue
                
                normalized = str(value).strip().upper()
                
                # Look for summary section headers
                if any(term in normalized for term in ["SUMMARY", "TOTAL", "BATCH", "CANDIDATE"]):
                    summary_section_found = True
                    summary_start_row = row
                    break
            
            if summary_section_found:
                break
        
        if not summary_section_found:
            return summary_cells
        
        # Search for summary labels in the vicinity
        search_rows = range(summary_start_row, min(summary_start_row + 20, worksheet.max_row + 1))
        
        for row in search_rows:
            for col in range(1, min(worksheet.max_column, 10) + 1):
                value = worksheet.cell(row, col).value
                if value is None:
                    continue
                
                normalized = WorkbookAnalyzer.normalize_text(value)
                
                # Check if this cell matches any summary label pattern
                for field_name, patterns in WorkbookAnalyzer.SUMMARY_LABEL_PATTERNS.items():
                    if any(pattern in normalized for pattern in patterns):
                        # Found a label, check the cell to the right for the value
                        value_col = col + 1
                        if value_col <= worksheet.max_column:
                            coordinate = worksheet.cell(row, value_col).coordinate
                            summary_cells[field_name] = coordinate
                            # Remove this field from patterns to avoid duplicates
                            WorkbookAnalyzer.SUMMARY_LABEL_PATTERNS[field_name] = []
                            break
        
        return summary_cells
    
    @staticmethod
    def find_batch_id_cell(worksheet):
        """
        Find the batch ID cell by searching for batch ID labels.
        
        Args:
            worksheet: The worksheet to analyze
            
        Returns:
            Cell coordinate of batch ID value or None if not found
        """
        # Search for batch ID label
        for row in range(1, min(worksheet.max_row, 30) + 1):
            for col in range(1, min(worksheet.max_column, 10) + 1):
                value = worksheet.cell(row, col).value
                if value is None:
                    continue
                
                normalized = WorkbookAnalyzer.normalize_text(value)
                
                # Check if this cell is a batch ID label
                if normalized in WorkbookAnalyzer.BATCH_ID_PATTERNS:
                    # Found a label, check the cell to the right for the value
                    value_col = col + 1
                    if value_col <= worksheet.max_column:
                        return worksheet.cell(row, value_col).coordinate
        
        return None
    
    @staticmethod
    def find_nos_section(worksheet):
        """
        Find the NOS section by looking for NOS codes and related content.
        
        Args:
            worksheet: The worksheet to analyze
            
        Returns:
            Dictionary with 'start_row', 'end_row', and 'nos_codes' list
        """
        nos_codes = []
        nos_start_row = None
        nos_end_row = None
        
        # Search for NOS codes
        for row in range(1, worksheet.max_row + 1):
            for col in range(1, min(worksheet.max_column, 5) + 1):
                value = worksheet.cell(row, col).value
                if value is None:
                    continue
                
                normalized = str(value).strip().upper()
                
                # Check for NOS code patterns
                is_nos_code = False
                for prefix in WorkbookAnalyzer.NOS_PREFIXES:
                    if normalized.startswith(prefix):
                        is_nos_code = True
                        break
                
                # Also check for WEAK PCs and similar NOS-related content
                if "WEAK" in normalized or "PC" in normalized:
                    is_nos_code = True
                
                if is_nos_code:
                    if nos_start_row is None:
                        nos_start_row = row
                    nos_end_row = row
                    nos_codes.append({
                        "row": row,
                        "col": col,
                        "value": normalized,
                    })
                    break  # Found NOS code in this row, move to next row
        
        if nos_start_row is None:
            return None
        
        return {
            "start_row": nos_start_row,
            "end_row": nos_end_row,
            "nos_codes": nos_codes,
        }
    
    @staticmethod
    def detect_pass_criteria(worksheet):
        """
        Detect the pass criteria from the workbook.
        
        Args:
            worksheet: The worksheet to analyze
            
        Returns:
            Pass criteria as a decimal (e.g., 0.8 for 80%) or None if not found
        """
        # Search for pass criteria indicators
        pass_criteria_keywords = ["pass criteria", "passing score", "threshold", "passing %"]
        
        for row in range(1, min(worksheet.max_row, 30) + 1):
            for col in range(1, min(worksheet.max_column, 10) + 1):
                value = worksheet.cell(row, col).value
                if value is None:
                    continue
                
                normalized = str(value).strip().lower()
                
                # Check if this cell mentions pass criteria
                if any(keyword in normalized for keyword in pass_criteria_keywords):
                    # Check adjacent cells for the actual value
                    for offset in [-1, 1]:  # Check left and right
                        check_col = col + offset
                        if 1 <= check_col <= worksheet.max_column:
                            adj_value = worksheet.cell(row, check_col).value
                            if adj_value is not None:
                                criteria = WorkbookAnalyzer.parse_pass_criteria(adj_value)
                                if criteria is not None:
                                    return criteria
        
        # If not found in labels, check score headers for embedded criteria
        for row in range(1, min(worksheet.max_row, 20) + 1):
            for col in range(1, worksheet.max_column + 1):
                value = worksheet.cell(row, col).value
                if value is None:
                    continue
                
                # Look for patterns like "80/100" or "80%"
                criteria = WorkbookAnalyzer.parse_pass_criteria(value)
                if criteria is not None:
                    return criteria
        
        return None
    
    @staticmethod
    def parse_pass_criteria(value):
        """
        Parse pass criteria from various formats.
        
        Args:
            value: The value to parse
            
        Returns:
            Pass criteria as a decimal or None if not parseable
        """
        if value is None:
            return None
        
        try:
            # Handle percentage format (e.g., "80%", "80.5%")
            if isinstance(value, str) and value.endswith("%"):
                return float(value.rstrip("%")) / 100
            
            # Handle fraction format (e.g., "80/100", "40/50")
            if isinstance(value, str) and "/" in value:
                parts = value.split("/")
                if len(parts) == 2:
                    numerator = float(parts[0].strip())
                    denominator = float(parts[1].strip())
                    if denominator != 0:
                        return numerator / denominator
            
            # Handle decimal (e.g., 0.8, 0.75)
            if isinstance(value, (int, float)):
                if 0 <= value <= 1:
                    return float(value)
                if value > 1:
                    return value / 100  # Assume percentage as whole number
            
            # Handle text percentage (e.g., "80 percent")
            if isinstance(value, str) and "percent" in value.lower():
                num_part = value.lower().replace("percent", "").strip()
                return float(num_part) / 100
            
        except (ValueError, ZeroDivisionError):
            pass
        
        return None