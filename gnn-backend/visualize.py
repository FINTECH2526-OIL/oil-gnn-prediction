import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from google.cloud import storage
import json
import gzip

from app.config import config
from app.data_loader import DataLoader
from app.inference import ModelInference

def visualize_contributions():
    print("Loading data and models...")
    data_loader = DataLoader()
    model_inference = ModelInference()
    
    df = data_loader.get_latest_data()
    
    feature_cols = [c for c in df.columns 
                   if c not in ['country', 'date', 'node_id', 'country_iso3'] 
                   and 'next' not in c 
                   and 'surprise' not in c
                   and df[c].dtype != 'object']
    
    latest_dates = sorted(df['date'].unique())[-30:]
    
    attention_history = []
    
    print("Computing predictions for last 30 days...")
    for date in latest_dates:
        result = model_inference.get_prediction_with_explanation(df, feature_cols, date)
        
        country_contributions = {
            country: data['contribution'] 
            for country, data in result['top_contributors'].items()
        }
        
        attention_history.append({
            'date': date,
            'prediction': result['predicted_delta'],
            'country_contributions': country_contributions
        })
    
    print("Creating visualizations...")
    
    rows = []
    for r in attention_history:
        d = pd.to_datetime(r["date"])
        for c, v in r.get("country_contributions", {}).items():
            rows.append({
                "date": d, 
                "country": c, 
                "contribution": float(v), 
                "abs_contribution": abs(float(v))
            })
    
    contrib_df = pd.DataFrame(rows)
    
    avg_abs = contrib_df.groupby("country")["abs_contribution"].mean().sort_values(ascending=False)
    top_k = min(12, len(avg_abs))
    top_countries = avg_abs.index[:top_k].tolist()
    
    sub = contrib_df[contrib_df["country"].isin(top_countries)]
    pivot = sub.pivot_table(index="date", columns="country", values="contribution", aggfunc="sum").fillna(0.0)
    pivot = pivot.reindex(columns=top_countries)
    
    plt.figure(figsize=(18, 12))
    cols = 4
    rows_grid = int(np.ceil(top_k / cols))
    
    for i, c in enumerate(top_countries, 1):
        ax = plt.subplot(rows_grid, cols, i)
        ax.plot(pivot.index, pivot[c], linewidth=2)
        ax.set_title(c, fontsize=10, fontweight='bold')
        ax.tick_params(labelsize=8)
        ax.grid(True, alpha=0.3)
        if i % cols != 1:
            ax.set_ylabel("")
        if i <= (rows_grid - 1) * cols:
            ax.set_xlabel("")
    
    plt.suptitle("Country Contributions Over Time (Last 30 Days)", y=0.995, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('country_contributions_timeseries.png', dpi=150, bbox_inches='tight')
    print("Saved: country_contributions_timeseries.png")
    plt.show()
    
    plt.figure(figsize=(16, 8))
    plt.imshow(pivot.values.T, aspect="auto", interpolation="nearest", cmap='RdBu_r')
    plt.yticks(ticks=np.arange(len(top_countries)), labels=top_countries, fontsize=10)
    plt.xticks(
        ticks=np.linspace(0, len(pivot.index)-1, min(10, len(pivot.index))).astype(int),
        labels=[pd.to_datetime(pivot.index[i]).strftime("%Y-%m-%d") 
                for i in np.linspace(0, len(pivot.index)-1, min(10, len(pivot.index))).astype(int)],
        rotation=45, 
        ha="right",
        fontsize=9
    )
    plt.title("Country Contribution Heatmap", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Date", fontsize=11)
    plt.ylabel("Country", fontsize=11)
    cbar = plt.colorbar()
    cbar.set_label('Contribution', fontsize=10)
    plt.tight_layout()
    plt.savefig('country_contributions_heatmap.png', dpi=150, bbox_inches='tight')
    print("Saved: country_contributions_heatmap.png")
    plt.show()
    
    plt.figure(figsize=(12, 8))
    avg_abs.head(top_k).iloc[::-1].plot(kind="barh", color='steelblue', edgecolor='black')
    plt.title("Average Absolute Contribution by Country", fontsize=14, fontweight='bold')
    plt.xlabel("Average |Contribution|", fontsize=11)
    plt.ylabel("Country", fontsize=11)
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig('country_average_contributions.png', dpi=150, bbox_inches='tight')
    print("Saved: country_average_contributions.png")
    plt.show()
    
    print("\nTop 10 Countries by Average Contribution:")
    for i, (country, value) in enumerate(avg_abs.head(10).items(), 1):
        print(f"{i:2d}. {country:3s}: {value:.6f}")

if __name__ == "__main__":
    visualize_contributions()
