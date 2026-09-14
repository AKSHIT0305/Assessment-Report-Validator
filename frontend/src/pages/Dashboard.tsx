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


  const handleValidate = async (files: File[]) => {

    await validate(files);

  };


  return (
    <main>

      <h1>Assessment Report Validator</h1>


      <FileUpload
        onValidate={handleValidate}
        loading={loading}
      />


      {error && (
        <p>
          {error}
        </p>
      )}


      <ValidationSummary
        data={data}
      />


      <FileResults
        data={data}
      />

    </main>
  );
}


export default Dashboard;