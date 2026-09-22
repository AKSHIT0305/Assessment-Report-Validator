import { useState, useCallback } from "react";

import { validateFiles } from "../services/api";
import type {
  ValidationResponse,
} from "../types/validation";


export function useValidation() {

  const [data, setData] = useState<ValidationResponse | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);


  const validate = useCallback(async (files: File[]) => {

    if (!files || files.length === 0) {

      setError("Please select at least one Excel file.");

      return null;
    }

    setLoading(true);
    setError(null);

    try {

      const result = await validateFiles(files);

      setData(result);

      return result;

    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong while validating the files.";

      if (message) {
        console.error("Validation error:", message);
      }

      setError(message);

      setData(null);

      throw err;

    } finally {

      setLoading(false);

    }
  }, []);


  const reset = useCallback(() => {

    setData(null);
    setError(null);

  }, []);


  return {
    validate,
    data,
    loading,
    error,
    reset,
  };
}