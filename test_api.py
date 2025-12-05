import requests
import json

API_URL = "http://localhost:8080"

def test_health():
    response = requests.get(f"{API_URL}/")
    print("Health Check:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_prediction():
    response = requests.post(f"{API_URL}/predict")
    print("Prediction:")
    print(json.dumps(response.json(), indent=2))
    print()

def test_contributors():
    response = requests.get(f"{API_URL}/contributors")
    print("Top Contributors:")
    data = response.json()
    print(f"Date: {data['date']}")
    print(f"Total Absolute Contribution: {data['total_abs_contribution']:.6f}")
    print("\nTop Contributors:")
    for contrib in data['contributors'][:10]:
        print(f"  {contrib['country']} {contrib['contribution']:+.6f}  {contrib['percentage']:.1f}%")
    print()

if __name__ == "__main__":
    print("Testing Oil GNN Prediction API\n")
    
    try:
        test_health()
        test_prediction()
        test_contributors()
        print("All tests completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
