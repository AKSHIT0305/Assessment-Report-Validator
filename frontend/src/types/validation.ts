export type ValidationIssue = {
  code: string;
  message: string;
  category: string;
  sheet?: string | null;
  cell?: string | null;
  expected?: unknown;
  actual?: unknown;
  severity?: "ERROR" | "WARNING";
};

export type FileValidationResult = {
  filename: string;
  status: "PASS" | "ERROR";
  template?: string | null;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
};

export type ValidationSummary = {
  correct: number;
  incorrect: number;
  percentage_correct: number;
};

export type ValidationResponse = {
  total_files: number;

  summary: ValidationSummary;

  correct_files: string[];

  incorrect_files: FileValidationResult[];

  files: FileValidationResult[];
};