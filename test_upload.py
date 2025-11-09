"""
Simple test script for document upload endpoint.
"""
import requests
import os

# Create a simple test text file
test_content = """
Financial Report Q4 2024

Revenue: $10.5 million
Expenses: $7.2 million
Net Profit: $3.3 million

Key Highlights:
- Revenue increased by 15% compared to Q3
- Operating expenses decreased by 5%
- Strong customer acquisition in the enterprise segment
"""

# Create test file
test_file_path = "test_document.txt"
with open(test_file_path, "w") as f:
    f.write(test_content)

print(f"Created test file: {test_file_path}")

# Test the upload endpoint
url = "http://localhost:8000/api/v1/documents/upload"

try:
    with open(test_file_path, "rb") as f:
        files = {"file": (test_file_path, f, "text/plain")}
        response = requests.post(url, files=files)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 201:
        print("\n✓ Upload successful!")
    else:
        print("\n✗ Upload failed!")
        
except requests.exceptions.ConnectionError:
    print("\n✗ Could not connect to server. Make sure the API is running.")
except Exception as e:
    print(f"\n✗ Error: {e}")
finally:
    # Clean up test file
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
        print(f"\nCleaned up test file: {test_file_path}")
