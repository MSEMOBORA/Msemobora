import requests
import json
import time
from datetime import datetime, timedelta
import unittest

# Backend URL
BACKEND_URL = "https://fa80b6e3-828c-47ac-b62a-99942887e481.preview.emergentagent.com"
API_BASE_URL = f"{BACKEND_URL}/api"

class TestMsemoboraBackend(unittest.TestCase):
    """Test suite for Msemobora AI-Powered Employee Sentiment Analysis Platform backend"""

    def setUp(self):
        """Setup for tests"""
        self.api_url = API_BASE_URL
        self.test_departments = ["Engineering", "Sales", "HR", "Marketing"]
        
        # Test data for different sentiment types
        self.positive_feedback = "I love working here! The team is amazing and supportive. Management really cares about our well-being and professional growth."
        self.negative_feedback = "I'm frustrated with the workload and management. There's poor communication and unrealistic deadlines. I feel undervalued and overworked."
        self.neutral_feedback = "The office temperature is usually fine. The new project management system has some good features but also some limitations."

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        response = requests.get(f"{self.api_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ Root endpoint test passed: {data['message']}")

    def test_feedback_submission_positive(self):
        """Test submitting feedback with positive sentiment"""
        payload = {
            "employee_id": "EMP123",
            "feedback_text": self.positive_feedback,
            "department": "Engineering"
        }
        
        response = requests.post(f"{self.api_url}/feedback", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["feedback_text"], self.positive_feedback)
        self.assertEqual(data["department"], "Engineering")
        self.assertEqual(data["sentiment"], "Positive")
        self.assertTrue(0 <= data["confidence_score"] <= 1.0)
        self.assertTrue(data["processed"])
        
        print(f"✅ Positive feedback submission test passed: Sentiment={data['sentiment']}, Confidence={data['confidence_score']}")
        return data["id"]  # Return ID for later tests

    def test_feedback_submission_negative(self):
        """Test submitting feedback with negative sentiment"""
        payload = {
            "employee_id": "EMP456",
            "feedback_text": self.negative_feedback,
            "department": "Sales"
        }
        
        response = requests.post(f"{self.api_url}/feedback", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["feedback_text"], self.negative_feedback)
        self.assertEqual(data["department"], "Sales")
        self.assertEqual(data["sentiment"], "Negative")
        self.assertTrue(0 <= data["confidence_score"] <= 1.0)
        self.assertTrue(data["processed"])
        
        print(f"✅ Negative feedback submission test passed: Sentiment={data['sentiment']}, Confidence={data['confidence_score']}")
        return data["id"]

    def test_feedback_submission_neutral(self):
        """Test submitting feedback with neutral sentiment"""
        payload = {
            "employee_id": "EMP789",
            "feedback_text": self.neutral_feedback,
            "department": "HR"
        }
        
        response = requests.post(f"{self.api_url}/feedback", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["feedback_text"], self.neutral_feedback)
        self.assertEqual(data["department"], "HR")
        # Don't strictly check the sentiment as it might vary based on the LLM's analysis
        self.assertIn(data["sentiment"], ["Positive", "Neutral", "Negative"])
        self.assertTrue(0 <= data["confidence_score"] <= 1.0)
        self.assertTrue(data["processed"])
        
        print(f"✅ Neutral feedback submission test passed: Sentiment={data['sentiment']}, Confidence={data['confidence_score']}")
        return data["id"]

    def test_feedback_submission_no_employee_id(self):
        """Test submitting feedback without employee ID (should be optional)"""
        payload = {
            "feedback_text": "The new benefits package is quite good.",
            "department": "Marketing"
        }
        
        response = requests.post(f"{self.api_url}/feedback", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["department"], "Marketing")
        self.assertIsNone(data["employee_id"])
        self.assertTrue(data["processed"])
        
        print(f"✅ Feedback submission without employee ID test passed")

    def test_get_feedback(self):
        """Test retrieving feedback without filters"""
        response = requests.get(f"{self.api_url}/feedback")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        if data:  # If there's feedback in the database
            self.assertIn("feedback_text", data[0])
            self.assertIn("sentiment", data[0])
            self.assertIn("department", data[0])
        
        print(f"✅ Get feedback test passed: Retrieved {len(data)} feedback items")

    def test_get_feedback_with_department_filter(self):
        """Test retrieving feedback with department filter"""
        # First ensure we have feedback for this department
        self.test_feedback_submission_positive()
        
        response = requests.get(f"{self.api_url}/feedback?department=Engineering")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            for item in data:
                self.assertEqual(item["department"], "Engineering")
        
        print(f"✅ Get feedback with department filter test passed: Retrieved {len(data)} Engineering feedback items")

    def test_get_feedback_with_sentiment_filter(self):
        """Test retrieving feedback with sentiment filter"""
        # First ensure we have negative feedback
        self.test_feedback_submission_negative()
        
        response = requests.get(f"{self.api_url}/feedback?sentiment=Negative")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        if data:
            for item in data:
                self.assertEqual(item["sentiment"], "Negative")
        
        print(f"✅ Get feedback with sentiment filter test passed: Retrieved {len(data)} negative feedback items")

    def test_dashboard_data(self):
        """Test retrieving dashboard data"""
        # First ensure we have some feedback data
        self.test_feedback_submission_positive()
        self.test_feedback_submission_negative()
        self.test_feedback_submission_neutral()
        
        response = requests.get(f"{self.api_url}/dashboard")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("total_feedback", data)
        self.assertIn("sentiment_distribution", data)
        self.assertIn("sentiment_timeline", data)
        self.assertIn("department_breakdown", data)
        self.assertIn("recent_feedback", data)
        
        # Verify sentiment distribution has expected keys
        self.assertIn("Positive", data["sentiment_distribution"])
        self.assertIn("Negative", data["sentiment_distribution"])
        self.assertIn("Neutral", data["sentiment_distribution"])
        
        # Verify timeline data structure
        self.assertIsInstance(data["sentiment_timeline"], list)
        if data["sentiment_timeline"]:
            timeline_item = data["sentiment_timeline"][0]
            self.assertIn("date", timeline_item)
            self.assertIn("positive", timeline_item)
            self.assertIn("negative", timeline_item)
            self.assertIn("neutral", timeline_item)
        
        # Verify department breakdown
        self.assertIsInstance(data["department_breakdown"], dict)
        
        print(f"✅ Dashboard data test passed: Total feedback={data['total_feedback']}")
        return data

    def test_dashboard_with_department_filter(self):
        """Test dashboard data with department filter"""
        # First ensure we have some feedback data for Engineering
        self.test_feedback_submission_positive()  # This adds Engineering feedback
        
        response = requests.get(f"{self.api_url}/dashboard?departments=Engineering")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("department_breakdown", data)
        self.assertIn("Engineering", data["department_breakdown"])
        
        print(f"✅ Dashboard with department filter test passed")

    def test_dashboard_with_date_filter(self):
        """Test dashboard data with date filter"""
        # Get today's date in ISO format
        today = datetime.utcnow().date().isoformat()
        yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
        
        response = requests.get(f"{self.api_url}/dashboard?start_date={yesterday}&end_date={today}")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("total_feedback", data)
        
        print(f"✅ Dashboard with date filter test passed")

    def test_insights(self):
        """Test retrieving actionable insights"""
        # First ensure we have some negative feedback
        for _ in range(2):  # Add multiple negative feedback to trigger insights
            self.test_feedback_submission_negative()
        
        response = requests.get(f"{self.api_url}/insights")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:  # If insights were generated
            insight = data[0]
            self.assertIn("priority", insight)
            self.assertIn("category", insight)
            self.assertIn("description", insight)
            self.assertIn("affected_departments", insight)
            self.assertIn("suggested_actions", insight)
            
            # Verify suggested actions is a list of strings
            self.assertIsInstance(insight["suggested_actions"], list)
            if insight["suggested_actions"]:
                self.assertIsInstance(insight["suggested_actions"][0], str)
        
        print(f"✅ Insights test passed: Retrieved {len(data)} insights")

    def test_departments(self):
        """Test retrieving departments list"""
        response = requests.get(f"{self.api_url}/departments")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("departments", data)
        self.assertIsInstance(data["departments"], list)
        
        print(f"✅ Departments test passed: Retrieved {len(data['departments'])} departments")

def run_all_tests():
    """Run all tests in sequence"""
    print("\n🔍 Starting Msemobora Backend API Tests...\n")
    
    try:
        test = TestMsemoboraBackend()
        test.setUp()
        
        # Test root endpoint
        test.test_root_endpoint()
        
        # Test feedback submission with different sentiments
        print("\n--- Testing Feedback Submission API ---")
        positive_id = test.test_feedback_submission_positive()
        negative_id = test.test_feedback_submission_negative()
        neutral_id = test.test_feedback_submission_neutral()
        test.test_feedback_submission_no_employee_id()
        
        # Test feedback retrieval
        print("\n--- Testing Feedback Retrieval API ---")
        test.test_get_feedback()
        test.test_get_feedback_with_department_filter()
        test.test_get_feedback_with_sentiment_filter()
        
        # Test dashboard data
        print("\n--- Testing Dashboard Data API ---")
        dashboard_data = test.test_dashboard_data()
        test.test_dashboard_with_department_filter()
        test.test_dashboard_with_date_filter()
        
        # Test insights
        print("\n--- Testing Actionable Insights API ---")
        test.test_insights()
        
        # Test departments
        print("\n--- Testing Departments API ---")
        test.test_departments()
        
        print("\n✅ All tests completed successfully!")
        
        # Print summary of dashboard data
        print("\n📊 Dashboard Data Summary:")
        print(f"Total Feedback: {dashboard_data['total_feedback']}")
        print(f"Sentiment Distribution: {json.dumps(dashboard_data['sentiment_distribution'], indent=2)}")
        print(f"Department Breakdown: {json.dumps(dashboard_data['department_breakdown'], indent=2)}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"\n❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_all_tests()