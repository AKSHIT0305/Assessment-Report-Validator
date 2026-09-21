"""
Sheet Mapper - Abstracts template-specific sheet names into logical roles.

This allows validators to work with both standard and legacy templates
without hardcoding sheet names.
"""


class SheetMapper:
    """
    Maps template-specific sheet names to logical roles.
    
    Logical roles:
    - PRIMARY_DATA_SHEET: Contains candidate assessment data
    - TABULAR_ANALYSIS_SHEET: Contains tabular statistics
    - GRAPH_SHEET: Contains graphs (optional)
    """
    
    # Logical role constants
    PRIMARY_DATA_SHEET = "PRIMARY_DATA_SHEET"
    TABULAR_ANALYSIS_SHEET = "TABULAR_ANALYSIS_SHEET"
    GRAPH_SHEET = "GRAPH_SHEET"
    
    # Template-specific sheet mappings
    STANDARD_MAPPING = {
        PRIMARY_DATA_SHEET: "score_sheet",
        TABULAR_ANALYSIS_SHEET: "Batch Analysis - Tabular",
        GRAPH_SHEET: "Batch Analysis - Graph",
    }
    
    LEGACY_MAPPING = {
        PRIMARY_DATA_SHEET: "Result",
        TABULAR_ANALYSIS_SHEET: "Analysis-Tabular",
        GRAPH_SHEET: "Analysis - Graph",
    }
    
    # All possible sheet names for each logical role
    SHEET_NAME_PATTERNS = {
        PRIMARY_DATA_SHEET: ["score_sheet", "Result"],
        TABULAR_ANALYSIS_SHEET: ["Batch Analysis - Tabular", "Analysis-Tabular"],
        GRAPH_SHEET: ["Batch Analysis - Graph", "Analysis - Graph"],
    }
    
    @classmethod
    def get_mapping(cls, template):
        """
        Get the sheet name mapping for a given template.
        
        Args:
            template: Template type (STANDARD, ALTERNATE_SCORE, LEGACY_RESULT)
            
        Returns:
            Dictionary mapping logical roles to actual sheet names
        """
        if template == "LEGACY_RESULT":
            return cls.LEGACY_MAPPING.copy()
        else:
            # STANDARD and ALTERNATE_SCORE use the same sheet names
            return cls.STANDARD_MAPPING.copy()
    
    @classmethod
    def resolve_logical_name(cls, workbook, logical_name, template=None):
        """
        Resolve a logical sheet name to the actual sheet name in the workbook.
        
        This handles cases where sheet names might vary slightly or
        where we need to find the sheet dynamically.
        
        Args:
            workbook: The workbook object
            logical_name: The logical role (PRIMARY_DATA_SHEET, etc.)
            template: Template type (optional, for better resolution)
            
        Returns:
            Actual sheet name or None if not found
        """
        # If template is provided, use the expected mapping
        if template:
            mapping = cls.get_mapping(template)
            expected_name = mapping.get(logical_name)
            if expected_name and expected_name in workbook.sheetnames:
                return expected_name
        
        # If template mapping didn't work, search for the sheet by patterns
        possible_names = cls.SHEET_NAME_PATTERNS.get(logical_name, [])
        
        # Check each possible name
        for possible_name in possible_names:
            if possible_name in workbook.sheetnames:
                return possible_name
        
        # If exact match not found, try fuzzy matching
        for sheet_name in workbook.sheetnames:
            normalized_sheet = sheet_name.lower().replace(" ", "").replace("-", "")
            for possible_name in possible_names:
                normalized_possible = possible_name.lower().replace(" ", "").replace("-", "")
                if normalized_sheet == normalized_possible:
                    return sheet_name
        
        return None
    
    @classmethod
    def identify_primary_data_sheet(cls, workbook):
        """
        Dynamically identify the primary data sheet by content analysis.
        
        This doesn't rely on template detection - it looks for sheets
        that contain candidate assessment data.
        
        Args:
            workbook: The workbook object
            
        Returns:
            Sheet name or None if not found
        """
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            
            # Skip hidden sheets
            if worksheet.sheet_state == 'hidden':
                continue
            
            # Look for Candidate ID header
            for row in range(1, min(worksheet.max_row, 50) + 1):
                for col in range(1, min(worksheet.max_column, 20) + 1):
                    value = worksheet.cell(row, col).value
                    if value is None:
                        continue
                    
                    normalized = str(value).strip().lower().replace("_", " ").replace("-", " ")
                    
                    if normalized in {"candidate id", "candidateid"}:
                        return sheet_name
        
        return None
    
    @classmethod
    def identify_tabular_analysis_sheet(cls, workbook):
        """
        Dynamically identify the tabular analysis sheet by content analysis.
        
        Args:
            workbook: The workbook object
            
        Returns:
            Sheet name or None if not found
        """
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            
            # Skip hidden sheets
            if worksheet.sheet_state == 'hidden':
                continue
            
            # Look for NOS SUMMARY or statistical patterns
            for row in range(1, min(worksheet.max_row, 30) + 1):
                for col in range(1, min(worksheet.max_column, 10) + 1):
                    value = worksheet.cell(row, col).value
                    if value is None:
                        continue
                    
                    normalized = str(value).strip().upper()
                    
                    # Check for NOS SUMMARY or statistical indicators
                    if "NOS SUMMARY" in normalized or "ANALYSIS" in normalized:
                        return sheet_name
                    
                    # Check for NOS code patterns
                    if any(prefix in normalized for prefix in ["SSC/", "MEP/", "DGT/", "TEL/"]):
                        return sheet_name
        
        return None