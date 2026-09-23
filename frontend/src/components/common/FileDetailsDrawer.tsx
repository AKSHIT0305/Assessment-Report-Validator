import React from "react";
import type { HistoryRecord, ReviewStateFile, FileValidationResult, AIReviewSummary, ReviewClassification } from "../types/validation";

// Helper function to format classification label
const formatClassificationLabel = (classification: ReviewClassification): string => {
  const labels: Record<ReviewClassification, string> = {
    likely_valid: "Likely Valid",
    likely_issue: "Likely Issue",
    formatting_variation: "Formatting Variation",
    unverifiable: "Unverifiable",
    needs_human_review: "Needs Human Review",
  };
  return labels[classification] || classification;
};

// Helper function to get classification color
const getClassificationColor = (classification: ReviewClassification): string => {
  const colors: Record<ReviewClassification, string> = {
    likely_valid: "text-green-600 bg-green-50",
    likely_issue: "text-red-600 bg-red-50",
    formatting_variation: "text-blue-600 bg-blue-50",
    unverifiable: "text-gray-600 bg-gray-50",
    needs_human_review: "text-yellow-600 bg-yellow-50",
  };
  return colors[classification] || "text-gray-600 bg-gray-50";
};

type FileDetailsDrawerProps = {
  file: HistoryRecord | ReviewStateFile | FileValidationResult;
  onClose: () => void;
  onMarkVerified?: () => void;
  onMarkIncorrect?: () => void;
  showReviewActions?: boolean;
};

function FileDetailsDrawer({ file, onClose, onMarkVerified, onMarkIncorrect, showReviewActions = true }: FileDetailsDrawerProps) {
  // Handle both HistoryRecord and ReviewStateFile which have validation_result
  const validationResult = "validation_result" in file ? file.validation_result : file;
  const errors = validationResult.errors || [];
  const reviewItems = validationResult.review_items || [];
  const warnings = validationResult.warnings || [];
  const aiReview = validationResult.ai_review;
  const filename = "filename" in file ? file.filename : file.filename;
  const status = "status" in file ? file.status : file.status;
  const template = "template" in file ? file.template : file.template;

  const getReviewInstruction = (code: string) => {
    if (code === "HARDCODED_SUMMARY_REVIEW") {
      return "Compare the hardcoded summary value against the underlying candidate data to verify accuracy.";
    } else if (code === "HARDCODED_PASS_FAIL_REVIEW") {
      return "Find the declared pass criterion in the workbook and verify that the hardcoded Pass/Fail values correspond to the candidate scores.";
    } else if (code === "NOS_STATISTIC_REVIEW") {
      return "Verify that the hardcoded NOS statistic matches the underlying candidate/NOS assessment data.";
    }
    return "Review the item manually to verify correctness.";
  };

  const groupedIssues = {
    errors: errors,
    review: reviewItems,
    warnings: warnings,
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">{filename}</h3>
            <p className="text-sm text-gray-600">
              Status: <span className={`font-medium ${
                status === "PASS" ? "text-green-600" :
                status === "ERROR" ? "text-red-600" :
                "text-yellow-600"
              }`}>{status}</span>
              {" • "}
              Template: {template || "N/A"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Summary */}
          <div className="mb-6 grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Errors</div>
              <div className="text-2xl font-bold text-red-600">{errors.length}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Review Items</div>
              <div className="text-2xl font-bold text-yellow-600">{reviewItems.length}</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Warnings</div>
              <div className="text-2xl font-bold text-blue-600">{warnings.length}</div>
            </div>
          </div>

          {/* Errors */}
          {errors.length > 0 && (
            <div className="mb-6">
              <h4 className="font-semibold text-gray-800 mb-3">Errors ({errors.length})</h4>
              <div className="space-y-2">
                {errors.slice(0, 10).map((error, index) => (
                  <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-red-800">{error.code}</span>
                      <span className="text-xs text-red-600">{error.sheet || "N/A"}:{error.cell || "N/A"}</span>
                    </div>
                    <p className="text-sm text-gray-700">{error.message}</p>
                    {(error.expected !== undefined || error.actual !== undefined) && (
                      <div className="mt-2 text-xs text-gray-600">
                        Expected: {String(error.expected)} | Actual: {String(error.actual)}
                      </div>
                    )}
                  </div>
                ))}
                {errors.length > 10 && (
                  <div className="text-center text-sm text-gray-600 py-2">
                    ... and {errors.length - 10} more errors
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Review Items */}
          {reviewItems.length > 0 && (
            <div className="mb-6">
              <h4 className="font-semibold text-gray-800 mb-3">Review Items ({reviewItems.length})</h4>
              <div className="space-y-2">
                {reviewItems.slice(0, 10).map((item, index) => (
                  <div key={index} className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-yellow-800">{item.code}</span>
                      <span className="text-xs text-yellow-600">{item.sheet || "N/A"}:{item.cell || "N/A"}</span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{item.message}</p>
                    <div className="mt-2 p-2 bg-yellow-100 rounded">
                      <p className="text-xs text-yellow-800 font-medium">What the reviewer needs to check:</p>
                      <p className="text-xs text-yellow-900">{getReviewInstruction(item.code)}</p>
                    </div>
                  </div>
                ))}
                {reviewItems.length > 10 && (
                  <div className="text-center text-sm text-gray-600 py-2">
                    ... and {reviewItems.length - 10} more review items
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Assessment */}
          {aiReview && aiReview.enabled && (
            <div className="mb-6">
              <h4 className="font-semibold text-gray-800 mb-3">AI Assessment</h4>
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs font-semibold text-purple-700 uppercase tracking-wide">
                    AI-Powered Classification
                  </span>
                  {aiReview.successfully_classified > 0 && (
                    <span className="text-xs text-purple-600">
                      ({aiReview.successfully_classified}/{aiReview.total_review_items} classified)
                    </span>
                  )}
                </div>

                {aiReview.classifications.length > 0 && (
                  <div className="space-y-3">
                    {aiReview.classifications.map((classification, idx) => (
                      <div key={idx} className="bg-white rounded p-3 border border-purple-100">
                        {classification.classification ? (
                          <>
                            <div className="flex items-center gap-2 mb-2">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getClassificationColor(classification.classification)}`}>
                                {formatClassificationLabel(classification.classification)}
                              </span>
                              {classification.confidence && (
                                <span className="text-xs text-gray-600">
                                  {Math.round(classification.confidence * 100)}% confidence
                                </span>
                              )}
                              {classification.model_used && (
                                <span className="text-xs text-gray-500">
                                  via {classification.model_used}
                                </span>
                              )}
                            </div>
                            {classification.reasoning && (
                              <div className="text-gray-700 text-sm mb-2">
                                {classification.reasoning}
                              </div>
                            )}
                            {classification.suggested_action && (
                              <div className="text-gray-600 text-sm italic">
                                💡 {classification.suggested_action}
                              </div>
                            )}
                          </>
                        ) : classification.error ? (
                          <div className="text-sm text-red-600">
                            Classification failed: {classification.error}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}

                {aiReview.failed_classifications > 0 && (
                  <div className="text-sm text-orange-600 mt-3">
                    {aiReview.failed_classifications} item(s) could not be classified
                  </div>
                )}

                <div className="text-xs text-gray-500 mt-3 pt-3 border-t border-purple-200">
                  ⚠️ This AI assessment is for informational purposes only. The deterministic validation result remains authoritative. Human verification is still required.
                </div>
              </div>
            </div>
          )}

          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="mb-6">
              <h4 className="font-semibold text-gray-800 mb-3">Warnings ({warnings.length})</h4>
              <div className="space-y-2">
                {warnings.slice(0, 5).map((warning, index) => (
                  <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-blue-800">{warning.code}</span>
                      <span className="text-xs text-blue-600">{warning.sheet || "N/A"}:{warning.cell || "N/A"}</span>
                    </div>
                    <p className="text-sm text-gray-700">{warning.message}</p>
                  </div>
                ))}
                {warnings.length > 5 && (
                  <div className="text-center text-sm text-gray-600 py-2">
                    ... and {warnings.length - 5} more warnings
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {showReviewActions && (status === "REVIEW" || status === "ERROR") && (
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            {onMarkVerified && (
              <button
                onClick={onMarkVerified}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Mark as Verified
              </button>
            )}
            {onMarkIncorrect && (
              <button
                onClick={onMarkIncorrect}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Mark as Incorrect
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default FileDetailsDrawer;
