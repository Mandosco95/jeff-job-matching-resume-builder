import requests
import json
from typing import Dict, List, Any, Optional

class APIClient:
    """Client for interacting with the demo API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the API client with the base URL"""
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        
    def get_data(self, category: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get data from the API, optionally filtered by category"""
        params = {}
        if category:
            params["category"] = category
        if limit:
            params["limit"] = limit
            
        response = requests.get(f"{self.base_url}/api/data", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def get_categories(self) -> List[str]:
        """Get available categories from the API"""
        response = requests.get(f"{self.base_url}/api/categories")
        
        if response.status_code == 200:
            return response.json()["categories"]
        else:
            response.raise_for_status()
    
    def predict(self, input_value: float, category: str) -> Dict[str, Any]:
        """Make a prediction using the API"""
        payload = {
            "input_value": input_value,
            "category": category
        }
        
        response = requests.post(
            f"{self.base_url}/api/predict",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def customize_documents(self, job_description: str, user_id: str) -> dict:
        """
        Send request to customize CV and Cover Letter based on job description
        """
        try:
            response = requests.post(
                f"{self.base_url}/customize-documents",
                json={
                    "job_description": job_description,
                    "user_id": user_id
                },
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to customize documents: {str(e)}") 