const API_BASE_URL = "/api/v1";

export type HealthResponse = {
  status: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error("Health check failed");
  }

  return (await response.json()) as HealthResponse;
}
