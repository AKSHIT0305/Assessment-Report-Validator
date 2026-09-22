import React from "react";

type FileUploadProps = {
  onFilesSelected: (files: File[]) => void;
  onValidate: () => Promise<void>;
  loading: boolean;
  selectedFiles: File[];
  onRemoveFile: (index: number) => void;
};

function FileUpload({
  onFilesSelected,
  onValidate,
  loading,
  selectedFiles,
  onRemoveFile,
}: FileUploadProps) {

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) {
      return;
    }
    const files = Array.from(event.target.files);
    onFilesSelected(files);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Upload Excel Files</h3>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-4">
        <input
          type="file"
          multiple
          accept=".xlsx,.xlsm"
          onChange={handleFileChange}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="cursor-pointer inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Pick Files
        </label>
        <p className="text-sm text-gray-500 mt-2">
          Select .xlsx or .xlsm files (multiple allowed)
        </p>
      </div>

      {selectedFiles.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Selected Files ({selectedFiles.length})</h4>
          <div className="space-y-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2"
              >
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-800">{file.name}</div>
                  <div className="text-xs text-gray-500">{formatFileSize(file.size)}</div>
                </div>
                <button
                  onClick={() => onRemoveFile(index)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={onValidate}
        disabled={loading || selectedFiles.length === 0}
        className={`w-full py-3 rounded-lg font-medium transition-colors ${
          loading || selectedFiles.length === 0
            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700"
        }`}
      >
        {loading ? "Processing..." : "Start Validation"}
      </button>
    </div>
  );
}

export default FileUpload;
