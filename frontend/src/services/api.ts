import type { ValidationResponse } from "../types/validation";

export async function validateFiles(
  files: File[]
): Promise<ValidationResponse> {

  const form = new FormData();

  files.forEach((file) => {
    form.append("files", file);
  });

  const response = await fetch(
    "http://127.0.0.1:8001/api/validate",
    {
      method: "POST",
      body: form,
    }
  );

  if (!response.ok) {

    const errorText = await response.text();

    throw new Error(
      `Validation failed (${response.status}): ${errorText}`
    );
  }

  return response.json();
}