// API response types matching backend structure

export interface Contributor {
    country: string;
    contribution: number;
    percentage: number;
    raw_prediction: number;
    attention_weight: number;
}

export interface PredictionRecord {
    feature_date: string;
    prediction_for_date: string;
    reference_close: number;
    predicted_delta: number;
    predicted_close: number;
    total_abs_contribution: number;
    num_countries: number;
    top_contributors: Contributor[];
    prediction_generated_at: string;
    actual_close?: number;
    actual_delta?: number;
    error_delta?: number;
    error_price?: number;
    actual_recorded_at?: string;
}
