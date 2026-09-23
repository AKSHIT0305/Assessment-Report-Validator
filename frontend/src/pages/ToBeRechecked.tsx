import { useState, useEffect, useCallback } from "react";
import { getReviewState, updateReviewState } from "../services/api";
import type { ReviewStateResponse, ReviewStateFile, AIReviewSummary, ReviewClassification } from "../types/validation";
import FileDetailsDrawer from "../components/common/FileDetailsDrawer";

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

function ToBeRechecked() {
  const [reviewState, setReviewState] = useState<ReviewStateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<ReviewStateFile | null>(null);

  const loadReviewState = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getReviewState();
      setReviewState(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load review state:", err);
      setError("Failed to load review state");
    } finally {
      setLoading(false);
    }
  }, []);

  // Load on mount
  useEffect(() => {
    loadReviewState();
  }, [loadReviewState]);

  const handleMarkVerified = async (filename: string) => {
    try {
      await updateReviewState(filename, "VERIFIED");
      await loadReviewState();
    } catch (err) {
      console.error("Failed to mark as verified", err);
      alert("Failed to mark as verified");
    }
  };

  const handleMarkIncorrect = async (filename: string) => {
    try {
      await updateReviewState(filename, "INCORRECT");
      await loadReviewState();
    } catch (err) {
      console.error("Failed to mark as incorrect", err);
      alert("Failed to mark as incorrect");
    }
  };

  if (loading) {
    return <div className="text-gray-600">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }

  const pendingFiles = reviewState?.pending_files || [];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">To Be Re-checked</h2>

      {pendingFiles.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-600">
          No files require review at this time.
        </div>
      ) : (
        <div className="space-y-4">
          {pendingFiles.map((file) => (
            <div
              key={file.filename}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800 mb-2">{file.filename}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                    <span>Status: <span className={`font-medium ${
                      file.status === "ERROR" ? "text-red-600" : "text-yellow-600"
                    }`}>{file.status}</span></span>
                    <span>•</span>
                    <span>{new Date(file.timestamp).toLocaleString()}</span>
                    <span>•</span>
                    <span>{file.error_count} errors</span>
                    <span>•</span>
                    <span>{file.review_count} review items</span>
                  </div>
                  
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Main issue:</span>{" "}
                    {file.validation_result.errors?.[0]?.message ||
                     file.validation_result.review_items?.[0]?.message ||
                     "See details for more information"}
                  </div>

                  {/* AI Assessment Section */}
                  {file.ai_review && file.ai_review.enabled && (
                    <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-semibold text-purple-700 uppercase tracking-wide">
                          AI Assessment
                        </span>
                        {file.ai_review.successfully_classified > 0 && (
                          <span className="text-xs text-purple-600">
                            ({file.ai_review.successfully_classified}/{file.ai_review.total_review_items} classified)
                          </span>
                        )}
                      </div>

                      {file.ai_review.classifications.length > 0 && (
                        <div className="space-y-2">
                          {file.ai_review.classifications.map((classification, idx) => (
                            <div key={idx} className="text-sm">
                              {classification.classification ? (
                                <>
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getClassificationColor(classification.classification)}`}>
                                      {formatClassificationLabel(classification.classification)}
                                    </span>
                                    {classification.confidence && (
                                      <span className="text-xs text-gray-600">
                                        {Math.round(classification.confidence * 100)}% confidence
                                      </span>
                                    )}
                                  </div>
                                  {classification.reasoning && (
                                    <div className="text-gray-700 text-xs mt-1">
                                      {classification.reasoning}
                                    </div>
                                  )}
                                  {classification.suggested_action && (
                                    <div className="text-gray-600 text-xs mt-1 italic">
                                      Suggested: {classification.suggested_action}
                                    </div>
                                  )}
                                </>
                              ) : classification.error ? (
                                <div className="text-xs text-red-600">
                                  AI classification failed: {classification.error}
                                </div>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      )}

                      {file.ai_review.failed_classifications > 0 && (
                        <div className="text-xs text-orange-600 mt-2">
                          {file.ai_review.failed_classifications} item(s) could not be classified
                        </div>
                      )}

                      <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-purple-200">
                        Human verification required. AI assistance is for informational purposes only.
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => setSelectedFile(file)}
                    className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleMarkVerified(file.filename)}
                    className="px-3 py-1.5 text-sm bg-green-100 text-green-700 hover:bg-green-200 rounded transition-colors"
                  >
                    Mark as Verified
                  </button>
                  <button
                    onClick={() => handleMarkIncorrect(file.filename)}
                    className="px-3 py-1.5 text-sm bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors"
                  >
                    Mark as Incorrect
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedFile && (
        <FileDetailsDrawer
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
          onMarkVerified={() => handleMarkVerified(selectedFile.filename)}
          onMarkIncorrect={() => handleMarkIncorrect(selectedFile.filename)}
        />
      )}
    </div>
  );
}

export default ToBeRechecked;
