import type { ValidationResponse, HistoryResponse, ReviewStateResponse, FileValidationResult } from "../types/validation";

const API_BASE = "http://127.0.0.1:8001/api";

export async function validateFiles(
  files: File[]
): Promise<ValidationResponse> {

  const form = new FormData();

  files.forEach((file) => {
    form.append("files", file);
  });

  const response = await fetch(
    `${API_BASE}/validate`,
    {
      method: "POST",
      body: form,
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    console.error("API Error Response:", errorText);
    throw new Error(
      `Validation failed (${response.status}): ${errorText}`
    );
  }

  return response.json();
}

export async function getHistory(): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE}/history`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch history (${response.status})`);
  }
  
  return response.json();
}

export async function getFileHistory(filename: string): Promise<{ filename: string; records: any[] }> {
  const response = await fetch(`${API_BASE}/history/${encodeURIComponent(filename)}`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch file history (${response.status})`);
  }
  
  return response.json();
}

export async function getReviewState(): Promise<ReviewStateResponse> {
  const response = await fetch(`${API_BASE}/review-state`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch review state (${response.status})`);
  }
  
  return response.json();
}

export async function updateReviewState(filename: string, decision: "VERIFIED" | "INCORRECT", reviewer?: string): Promise<{ filename: string; review_state: string }> {
  const response = await fetch(`${API_BASE}/review-state/${encodeURIComponent(filename)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ decision, reviewer }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to update review state (${response.status})`);
  }
  
  return response.json();
}