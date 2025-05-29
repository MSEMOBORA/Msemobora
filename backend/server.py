from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio

# Import the LLM integration
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Msemobora - Employee Sentiment Analysis", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Get API key from environment
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

# Define Models
class EmployeeFeedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: Optional[str] = None
    feedback_text: str
    department: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sentiment: Optional[str] = None
    confidence_score: Optional[float] = None
    processed: bool = False

class EmployeeFeedbackCreate(BaseModel):
    employee_id: Optional[str] = None
    feedback_text: str
    department: str

class SentimentAnalysis(BaseModel):
    sentiment: str
    confidence_score: float
    reasoning: str

class FilterParams(BaseModel):
    departments: Optional[List[str]] = None
    sentiments: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class DashboardData(BaseModel):
    total_feedback: int
    sentiment_distribution: Dict[str, int]
    sentiment_timeline: List[Dict[str, Any]]
    department_breakdown: Dict[str, Dict[str, int]]
    recent_feedback: List[EmployeeFeedback]

class ActionableInsight(BaseModel):
    priority: str
    category: str
    description: str
    affected_departments: List[str]
    suggested_actions: List[str]

async def analyze_sentiment_with_llm(feedback_text: str) -> SentimentAnalysis:
    """Analyze sentiment using Claude via emergentintegrations"""
    try:
        # Create a new LLM chat instance for each analysis
        chat = LlmChat(
            api_key=ANTHROPIC_API_KEY,
            session_id=f"sentiment_{uuid.uuid4()}",
            system_message="""You are an expert HR sentiment analyst. Analyze employee feedback and categorize it as one of: Positive, Neutral, or Negative.

Provide your response in this exact JSON format:
{
    "sentiment": "Positive|Neutral|Negative",
    "confidence_score": 0.95,
    "reasoning": "Brief explanation of your analysis"
}

Guidelines:
- Positive: Appreciation, satisfaction, motivation, praise, excitement
- Negative: Complaints, frustration, dissatisfaction, concerns, criticism
- Neutral: Factual statements, suggestions without emotion, balanced feedback
- Confidence score should be between 0.0 and 1.0
- Keep reasoning concise but insightful"""
        ).with_model("anthropic", "claude-sonnet-4-20250514")

        # Create user message
        user_message = UserMessage(
            text=f"Analyze this employee feedback for sentiment:\n\n'{feedback_text}'"
        )

        # Get response from LLM
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        import json
        try:
            result = json.loads(response)
            return SentimentAnalysis(
                sentiment=result["sentiment"],
                confidence_score=result["confidence_score"],
                reasoning=result["reasoning"]
            )
        except json.JSONDecodeError:
            # Fallback parsing if response isn't pure JSON
            if "Positive" in response:
                sentiment = "Positive"
            elif "Negative" in response:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
            
            return SentimentAnalysis(
                sentiment=sentiment,
                confidence_score=0.8,
                reasoning="AI analysis based on text content"
            )
            
    except Exception as e:
        logging.error(f"Error in sentiment analysis: {str(e)}")
        # Fallback to simple keyword-based analysis
        positive_words = ["good", "great", "excellent", "happy", "satisfied", "love", "amazing", "wonderful"]
        negative_words = ["bad", "terrible", "hate", "awful", "frustrated", "disappointed", "angry", "upset"]
        
        text_lower = feedback_text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "Positive"
        elif negative_count > positive_count:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
            
        return SentimentAnalysis(
            sentiment=sentiment,
            confidence_score=0.6,
            reasoning="Fallback keyword-based analysis"
        )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Msemobora - AI-Powered Employee Sentiment Analysis Platform"}

@api_router.post("/feedback", response_model=EmployeeFeedback)
async def create_feedback(feedback_data: EmployeeFeedbackCreate):
    """Create new employee feedback and analyze sentiment"""
    try:
        # Analyze sentiment
        sentiment_analysis = await analyze_sentiment_with_llm(feedback_data.feedback_text)
        
        # Create feedback object
        feedback = EmployeeFeedback(
            **feedback_data.model_dump(),
            sentiment=sentiment_analysis.sentiment,
            confidence_score=sentiment_analysis.confidence_score,
            processed=True
        )
        
        # Save to database
        await db.employee_feedback.insert_one(feedback.model_dump())
        
        return feedback
    except Exception as e:
        logging.error(f"Error creating feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")

@api_router.get("/feedback", response_model=List[EmployeeFeedback])
async def get_feedback(
    department: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = 100
):
    """Get employee feedback with optional filtering"""
    try:
        query = {}
        if department:
            query["department"] = department
        if sentiment:
            query["sentiment"] = sentiment
            
        feedback_list = await db.employee_feedback.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
        return [EmployeeFeedback(**feedback) for feedback in feedback_list]
    except Exception as e:
        logging.error(f"Error retrieving feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving feedback: {str(e)}")

@api_router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    departments: Optional[str] = None
):
    """Get dashboard analytics data"""
    try:
        # Build query
        query = {}
        if start_date:
            query["timestamp"] = {"$gte": datetime.fromisoformat(start_date.replace('Z', '+00:00'))}
        if end_date:
            if "timestamp" not in query:
                query["timestamp"] = {}
            query["timestamp"]["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        if departments:
            dept_list = departments.split(',')
            query["department"] = {"$in": dept_list}

        # Get all feedback
        all_feedback = await db.employee_feedback.find(query).to_list(1000)
        
        # Calculate sentiment distribution
        sentiment_dist = {"Positive": 0, "Neutral": 0, "Negative": 0}
        department_breakdown = {}
        
        for feedback in all_feedback:
            # Sentiment distribution
            sentiment = feedback.get("sentiment", "Neutral")
            sentiment_dist[sentiment] = sentiment_dist.get(sentiment, 0) + 1
            
            # Department breakdown
            dept = feedback.get("department", "Unknown")
            if dept not in department_breakdown:
                department_breakdown[dept] = {"Positive": 0, "Neutral": 0, "Negative": 0}
            department_breakdown[dept][sentiment] = department_breakdown[dept].get(sentiment, 0) + 1

        # Generate timeline data (last 7 days)
        from datetime import timedelta
        timeline_data = []
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            day_feedback = [f for f in all_feedback if f["timestamp"].date() == date.date()]
            
            day_sentiment = {"Positive": 0, "Neutral": 0, "Negative": 0}
            for feedback in day_feedback:
                sentiment = feedback.get("sentiment", "Neutral")
                day_sentiment[sentiment] += 1
            
            timeline_data.append({
                "date": date_str,
                "positive": day_sentiment["Positive"],
                "neutral": day_sentiment["Neutral"],
                "negative": day_sentiment["Negative"]
            })
        
        timeline_data.reverse()  # Show oldest to newest

        # Get recent feedback
        recent_feedback = [EmployeeFeedback(**f) for f in all_feedback[:10]]

        return DashboardData(
            total_feedback=len(all_feedback),
            sentiment_distribution=sentiment_dist,
            sentiment_timeline=timeline_data,
            department_breakdown=department_breakdown,
            recent_feedback=recent_feedback
        )
    except Exception as e:
        logging.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")

@api_router.get("/insights", response_model=List[ActionableInsight])
async def get_actionable_insights():
    """Generate actionable insights based on sentiment analysis"""
    try:
        # Get all negative feedback
        negative_feedback = await db.employee_feedback.find({"sentiment": "Negative"}).to_list(100)
        
        insights = []
        
        if negative_feedback:
            # Group by department
            dept_issues = {}
            for feedback in negative_feedback:
                dept = feedback.get("department", "Unknown")
                if dept not in dept_issues:
                    dept_issues[dept] = []
                dept_issues[dept].append(feedback["feedback_text"])
            
            # Generate insights for departments with multiple negative feedback
            for dept, issues in dept_issues.items():
                if len(issues) >= 2:
                    insights.append(ActionableInsight(
                        priority="High",
                        category="Department Morale",
                        description=f"{dept} department shows concerning sentiment patterns with {len(issues)} negative feedback instances",
                        affected_departments=[dept],
                        suggested_actions=[
                            "Schedule team meeting to address concerns",
                            "Conduct one-on-one sessions with team members",
                            "Review workload distribution and processes",
                            "Implement feedback follow-up mechanisms"
                        ]
                    ))
        
        # Add general insights based on overall sentiment
        all_feedback = await db.employee_feedback.find().to_list(1000)
        if all_feedback:
            negative_ratio = len([f for f in all_feedback if f.get("sentiment") == "Negative"]) / len(all_feedback)
            
            if negative_ratio > 0.3:
                insights.append(ActionableInsight(
                    priority="Critical",
                    category="Overall Sentiment",
                    description=f"High negative sentiment ratio ({negative_ratio:.1%}) across organization",
                    affected_departments=list(set([f.get("department", "Unknown") for f in all_feedback])),
                    suggested_actions=[
                        "Conduct organization-wide sentiment survey",
                        "Review management practices and policies",
                        "Implement employee wellness programs",
                        "Establish regular feedback channels"
                    ]
                ))
        
        return insights
    except Exception as e:
        logging.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@api_router.get("/departments")
async def get_departments():
    """Get list of all departments"""
    try:
        departments = await db.employee_feedback.distinct("department")
        return {"departments": departments}
    except Exception as e:
        logging.error(f"Error getting departments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting departments: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)