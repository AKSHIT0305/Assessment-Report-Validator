export type ValidationIssue = {
  code: string;
  message: string;
  category: string;
  sheet?: string | null;
  cell?: string | null;
  expected?: unknown;
  actual?: unknown;
  severity?: "ERROR" | "WARNING" | "REVIEW";
};

export type FileValidationResult = {
  filename: string;
  status: "PASS" | "ERROR" | "REVIEW";
  template?: string | null;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  review_items?: ValidationIssue[];
};

export type ValidationSummary = {
  correct: number;
  incorrect: number;
  review: number;
  percentage_correct: number;
};

export type ValidationResponse = {
  total_files: number;

  summary: ValidationSummary;

  correct_files: string[];

  incorrect_files: FileValidationResult[];

  review_files: FileValidationResult[];

  files: FileValidationResult[];
};

export type HistoryRecord = {
  filename: string;
  timestamp: string;
  status: "PASS" | "ERROR" | "REVIEW";
  template?: string | null;
  error_count: number;
  review_count: number;
  validation_result: FileValidationResult;
  review_state: "PENDING" | "VERIFIED" | "INCORRECT";
};

export type HistoryResponse = {
  history: HistoryRecord[];
  total: number;
};

export type ReviewStateFile = {
  filename: string;
  timestamp: string;
  status: "PASS" | "ERROR" | "REVIEW";
  template?: string | null;
  error_count: number;
  review_count: number;
  review_state: "PENDING" | "VERIFIED" | "INCORRECT";
  validation_result: FileValidationResult;
};

export type ReviewStateResponse = {
  pending_files: ReviewStateFile[];
  total: number;
};