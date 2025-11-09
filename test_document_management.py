"""
Test script for document management endpoints.
Tests the GET /documents, DELETE /documents/{id}, and GET /documents/stats endpoints.
"""
import requests
import os

BASE_URL = "http://localhost:8000/api/v1/documents"

def test_list_documents():
    """Test listing all documents."""
    print("\n=== Testing GET /api/v1/documents ===")
    try:
        response = requests.get(BASE_URL)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ List documents successful!")
            return response.json()
        else:
            print("✗ List documents failed!")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def test_get_stats():
    """Test getting document statistics."""
    print("\n=== Testing GET /api/v1/documents/stats ===")
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Get stats successful!")
            return response.json()
        else:
            print("✗ Get stats failed!")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def test_delete_document(document_id):
    """Test deleting a document."""
    print(f"\n=== Testing DELETE /api/v1/documents/{document_id} ===")
    try:
        response = requests.delete(f"{BASE_URL}/{document_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Delete document successful!")
            return True
        elif response.status_code == 404:
            print("✓ Document not found (expected for non-existent ID)")
            return True
        else:
            print("✗ Delete document failed!")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_delete_nonexistent():
    """Test deleting a non-existent document."""
    print("\n=== Testing DELETE with non-existent ID ===")
    fake_id = "doc_nonexistent123"
    try:
        response = requests.delete(f"{BASE_URL}/{fake_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 404:
            print("✓ Correctly returned 404 for non-existent document!")
            return True
        else:
            print("✗ Expected 404 status code!")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Document Management Endpoints Test Suite")
    print("=" * 60)
    print("\nMake sure the API server is running on http://localhost:8000")
    
    try:
        # Test 1: Get statistics
        stats = test_get_stats()
        
        # Test 2: List all documents
        documents = test_list_documents()
        
        # Test 3: Delete non-existent document (should return 404)
        test_delete_nonexistent()
        
        # Test 4: If there are documents, try deleting one
        if documents and documents.get('documents'):
            doc_list = documents['documents']
            if doc_list:
                first_doc_id = doc_list[0]['id']
                print(f"\nFound document to test deletion: {first_doc_id}")
                
                # Delete the document
                test_delete_document(first_doc_id)
                
                # Verify it's gone by listing again
                print("\n=== Verifying deletion ===")
                updated_docs = test_list_documents()
                
                # Check stats again
                updated_stats = test_get_stats()
                
                if stats and updated_stats:
                    print(f"\nStats before deletion: {stats}")
                    print(f"Stats after deletion: {updated_stats}")
        else:
            print("\nNo documents found to test deletion.")
            print("Upload a document first using test_upload.py")
        
        print("\n" + "=" * 60)
        print("Test suite completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Could not connect to server.")
        print("Make sure the API is running: python main.py")


if __name__ == "__main__":
    main()
