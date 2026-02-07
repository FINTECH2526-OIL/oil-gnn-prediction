const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export interface CountryContributor {
    contribution: number;
    percentage: number;
    raw_prediction: number;
    attention_weight: number;
}

export interface PredictionResponse {
    date: string;
    predicted_delta: number;
    predicted_direction: 'UP' | 'DOWN' | 'FLAT';
    top_contributors: Record<string, CountryContributor>;
    total_abs_contribution: number;
    num_countries: number;
    model_version: string;
}

export interface ContributorsResponse {
    date: string;
    contributors: Array<{
        country: string;
        contribution: number;
        percentage: number;
        raw_prediction: number;
        attention_weight: number;
    }>;
    total_abs_contribution: number;
}

export async function getPrediction(): Promise<PredictionResponse> {
    const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
}

export async function getContributors(): Promise<ContributorsResponse> {
    const response = await fetch(`${API_BASE_URL}/contributors`);

    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
}

export async function healthCheck(): Promise<{ status: string; model_loaded: boolean }> {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
}
