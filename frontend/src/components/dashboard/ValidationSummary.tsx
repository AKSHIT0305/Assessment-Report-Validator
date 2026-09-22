import type { ValidationResponse } from "../../types/validation";

type ValidationSummaryProps = {
  data: ValidationResponse | null;
};

function ValidationSummary({ data }: ValidationSummaryProps) {
  if (!data) return null;

  const { summary, total_files } = data;

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-sm text-gray-600 mb-1">Total Files</div>
        <div className="text-3xl font-bold text-gray-800">{total_files}</div>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-sm text-gray-600 mb-1">PASS</div>
        <div className="text-3xl font-bold text-green-600">{summary.correct}</div>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-sm text-gray-600 mb-1">REVIEW</div>
        <div className="text-3xl font-bold text-yellow-600">{summary.review}</div>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-sm text-gray-600 mb-1">ERROR</div>
        <div className="text-3xl font-bold text-red-600">{summary.incorrect}</div>
      </div>
    </div>
  );
}

export default ValidationSummary;
