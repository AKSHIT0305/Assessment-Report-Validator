import { useState } from "react";
import type { ValidationResponse, FileValidationResult } from "../../types/validation";
import FileDetailsDrawer from "../common/FileDetailsDrawer";

type FileResultsProps = {
  data: ValidationResponse | null;
};

function FileResults({ data }: FileResultsProps) {
  const [selectedFile, setSelectedFile] = useState<FileValidationResult | null>(null);

  if (!data) return null;

  const { files } = data;

  if (files.length === 0) return null;

  const allPass = files.every(f => f.status === "PASS");

  return (
    <div>
      {allPass && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-6 py-4 rounded-lg mb-6">
          All files are correct.
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Filename</th>
              <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Status</th>
              <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Errors</th>
              <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Review Items</th>
              <th className="text-left px-6 py-3 text-sm font-semibold text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            {files.map((file) => (
              <tr key={file.filename} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-800">{file.filename}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    file.status === "PASS" ? "bg-green-100 text-green-700" :
                    file.status === "ERROR" ? "bg-red-100 text-red-700" :
                    "bg-yellow-100 text-yellow-700"
                  }`}>
                    {file.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{file.errors.length}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{file.review_items?.length || 0}</td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => setSelectedFile(file)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedFile && (
        <FileDetailsDrawer
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
          showReviewActions={false}
        />
      )}
    </div>
  );
}

export default FileResults;
