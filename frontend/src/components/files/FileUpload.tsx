import React, { useState } from "react";

type FileUploadProps = {
  onValidate: (files: File[]) => Promise<void>;
  loading: boolean;
};

function FileUpload({
  onValidate,
  loading,
}: FileUploadProps) {

  const [files, setFiles] = useState<File[]>([]);
  const [message, setMessage] = useState("");

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {

    if (!event.target.files) {
      return;
    }

    const selectedFiles = Array.from(event.target.files);

    setFiles(selectedFiles);
    setMessage("");
  };

  const handleValidate = async () => {

    if (files.length === 0) {
      setMessage("Please select at least one Excel file.");
      return;
    }

    setMessage("");

    try {
      await onValidate(files);
    } catch (error) {
      console.error(error);
      setMessage(
        "Something went wrong while validating the files."
      );
    }
  };

  return (
    <section>

      <h2>Upload Excel Files</h2>

      <input
        type="file"
        multiple
        accept=".xlsx,.xlsm"
        onChange={handleFileChange}
      />

      <p>
        {files.length > 0
          ? `${files.length} file(s) selected`
          : "No files selected"}
      </p>

      {files.length > 0 && (
        <ul>
          {files.map((file) => (
            <li key={file.name}>
              {file.name}
            </li>
          ))}
        </ul>
      )}

      <button
        onClick={handleValidate}
        disabled={loading || files.length === 0}
      >
        {loading
          ? "Validating..."
          : "Validate Files"}
      </button>

      {message && (
        <p>{message}</p>
      )}

    </section>
  );
}

export default FileUpload;