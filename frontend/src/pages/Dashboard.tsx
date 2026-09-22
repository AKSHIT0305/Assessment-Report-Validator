import { useState } from "react";
import { useValidation } from "../hooks/useValidation";

import FileUpload from "../components/files/FileUpload";
import ValidationSummary from "../components/dashboard/ValidationSummary";
import FileResults from "../components/dashboard/FileResults";

function Dashboard() {
  const {
    validate,
    data,
    loading,
    error,
  } = useValidation();

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleFilesSelected = (files: File[]) => {
    setSelectedFiles(files);
  };

  const handleValidate = async () => {
    if (selectedFiles.length === 0) {
      return;
    }
    await validate(selectedFiles);
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>

      <FileUpload
        onFilesSelected={handleFilesSelected}
        onValidate={handleValidate}
        loading={loading}
        selectedFiles={selectedFiles}
        onRemoveFile={handleRemoveFile}
      />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {data && (
        <>
          <ValidationSummary data={data} />
          <FileResults data={data} />
        </>
      )}
    </div>
  );
}

export default Dashboard;
