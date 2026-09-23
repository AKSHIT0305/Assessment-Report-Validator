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

export type ReviewClassification = "likely_valid" | "likely_issue" | "formatting_variation" | "unverifiable" | "needs_human_review";

export type AIReviewClassification = {
  classification?: ReviewClassification;
  confidence?: number;
  reasoning?: string;
  suggested_action?: string;
  model_used?: string;
  latency_ms?: number;
  error?: string;
};

export type AIReviewSummary = {
  enabled: boolean;
  classifications: AIReviewClassification[];
  total_review_items: number;
  successfully_classified: number;
  failed_classifications: number;
};

export type FileValidationResult = {
  filename: string;
  status: "PASS" | "ERROR" | "REVIEW";
  template?: string | null;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  review_items?: ValidationIssue[];
  ai_review?: AIReviewSummary;
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
  ai_review?: AIReviewSummary;
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
  ai_review?: AIReviewSummary;
};

export type ReviewStateResponse = {
  pending_files: ReviewStateFile[];
  total: number;
};