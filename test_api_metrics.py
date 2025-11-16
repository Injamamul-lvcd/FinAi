"""
Simple test script for API metrics collection middleware.
"""
import requests
import json
import time
from pymongo import MongoClient

def test_api_metrics_collection():
    """Test that API metrics are being collected"""
    base_url = "http://localhost:8000"
    
    print("Testing API Metrics Collection Middleware...")
    print("=" * 60)
    
    # Connect to MongoDB to verify metrics
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        db = client["financial_chatbot"]
        metrics_collection = db["api_metrics"]
        
        # Get initial count
        initial_count = metrics_collection.count_documents({})
        print(f"Initial metrics count: {initial_count}")
        print("-" * 60)
        
        # Make some test requests
        test_endpoints = [
            "/",
            "/api/v1/health",
            "/api/docs"
        ]
        
        print("\nMaking test requests...")
        for endpoint in test_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"  Requesting: {endpoint}")
                response = requests.get(url, timeout=10)
                print(f"    Status: {response.status_code}")
            except Exception as e:
                print(f"    Error: {e}")
        
        # Wait a moment for metrics to be written
        time.sleep(1)
        
        # Check if metrics were recorded
        final_count = metrics_collection.count_documents({})
        new_metrics = final_count - initial_count
        
        print("\n" + "-" * 60)
        print(f"Final metrics count: {final_count}")
        print(f"New metrics recorded: {new_metrics}")
        
        if new_metrics > 0:
            print("\n✓ API metrics are being collected successfully!")
            
            # Show some recent metrics
            print("\nRecent metrics:")
            recent_metrics = metrics_collection.find().sort("timestamp", -1).limit(5)
            for metric in recent_metrics:
                print(f"  {metric['method']} {metric['endpoint']} - "
                      f"Status: {metric['status_code']}, "
                      f"Time: {metric['response_time_ms']:.2f}ms")
        else:
            print("\n⚠ Warning: No new metrics were recorded")
            print("This might indicate the middleware is not working properly")
        
        client.close()
        
    except Exception as e:
        print(f"\n✗ Error connecting to MongoDB: {e}")
        print("Make sure MongoDB is running and accessible")

if __name__ == "__main__":
    test_api_metrics_collection()
