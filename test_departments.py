import requests

# Backend URL
BACKEND_URL = "https://fa80b6e3-828c-47ac-b62a-99942887e481.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

def test_departments():
    """Test retrieving departments list"""
    response = requests.get(f"{API_BASE_URL}/departments")
    print(f"Status code: {response.status_code}")
    
    data = response.json()
    print(f"Response data: {data}")
    
    if "departments" in data:
        print(f"Departments: {data['departments']}")
        print(f"Number of departments: {len(data['departments'])}")
    else:
        print("No departments key in response")

if __name__ == "__main__":
    test_departments()