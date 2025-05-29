import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [insights, setInsights] = useState([]);
  const [feedbackData, setFeedbackData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newFeedback, setNewFeedback] = useState({
    employee_id: '',
    feedback_text: '',
    department: 'Engineering'
  });
  const [filters, setFilters] = useState({
    department: '',
    sentiment: '',
    start_date: '',
    end_date: ''
  });

  // Department options
  const departments = ['Engineering', 'Sales', 'HR', 'Marketing', 'Finance', 'Operations', 'Customer Support'];
  const sentiments = ['Positive', 'Neutral', 'Negative'];

  useEffect(() => {
    fetchDashboardData();
    fetchInsights();
    fetchFeedbackData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchInsights = async () => {
    try {
      const response = await axios.get(`${API}/insights`);
      setInsights(response.data);
    } catch (error) {
      console.error('Error fetching insights:', error);
    }
  };

  const fetchFeedbackData = async () => {
    try {
      setLoading(true);
      let url = `${API}/feedback?limit=50`;
      if (filters.department) url += `&department=${filters.department}`;
      if (filters.sentiment) url += `&sentiment=${filters.sentiment}`;
      
      const response = await axios.get(url);
      setFeedbackData(response.data);
    } catch (error) {
      console.error('Error fetching feedback data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/feedback`, newFeedback);
      setNewFeedback({ employee_id: '', feedback_text: '', department: 'Engineering' });
      // Refresh data
      fetchDashboardData();
      fetchFeedbackData();
      fetchInsights();
      alert('Feedback submitted successfully!');
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Error submitting feedback. Please try again.');
    }
  };

  const applyFilters = () => {
    fetchFeedbackData();
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'Positive': return 'text-green-600 bg-green-100';
      case 'Negative': return 'text-red-600 bg-red-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  const getSentimentIcon = (sentiment) => {
    switch (sentiment) {
      case 'Positive': return '😊';
      case 'Negative': return '😞';
      default: return '😐';
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Msemobora...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">M</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Msemobora</h1>
                <p className="text-sm text-gray-500">AI-Powered Employee Sentiment Analysis</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {dashboardData ? dashboardData.total_feedback : 0} Total Feedback
                </p>
                <p className="text-xs text-gray-500">Analyzed by AI</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: '📊' },
              { id: 'detailed', name: 'Detailed Analysis', icon: '🔍' },
              { id: 'insights', name: 'Actionable Insights', icon: '💡' },
              { id: 'submit', name: 'Submit Feedback', icon: '✍️' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && dashboardData && (
          <div className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">Total Feedback</p>
                    <p className="text-3xl font-bold text-gray-900">{dashboardData.total_feedback}</p>
                  </div>
                  <div className="text-4xl">📝</div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">Positive</p>
                    <p className="text-3xl font-bold text-green-600">{dashboardData.sentiment_distribution.Positive || 0}</p>
                  </div>
                  <div className="text-4xl">😊</div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">Neutral</p>
                    <p className="text-3xl font-bold text-blue-600">{dashboardData.sentiment_distribution.Neutral || 0}</p>
                  </div>
                  <div className="text-4xl">😐</div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">Negative</p>
                    <p className="text-3xl font-bold text-red-600">{dashboardData.sentiment_distribution.Negative || 0}</p>
                  </div>
                  <div className="text-4xl">😞</div>
                </div>
              </div>
            </div>

            {/* Sentiment Distribution Chart */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Distribution</h3>
              <div className="space-y-4">
                {Object.entries(dashboardData.sentiment_distribution).map(([sentiment, count]) => {
                  const percentage = dashboardData.total_feedback > 0 ? (count / dashboardData.total_feedback * 100).toFixed(1) : 0;
                  return (
                    <div key={sentiment} className="flex items-center space-x-4">
                      <div className="w-20 text-sm font-medium">{sentiment}</div>
                      <div className="flex-1 bg-gray-200 rounded-full h-4">
                        <div
                          className={`h-4 rounded-full ${
                            sentiment === 'Positive' ? 'bg-green-500' :
                            sentiment === 'Negative' ? 'bg-red-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                      <div className="w-16 text-sm text-gray-600">{count} ({percentage}%)</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Department Breakdown */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Department Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(dashboardData.department_breakdown).map(([dept, sentiments]) => {
                  const total = Object.values(sentiments).reduce((a, b) => a + b, 0);
                  return (
                    <div key={dept} className="border rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">{dept}</h4>
                      <div className="space-y-2">
                        {Object.entries(sentiments).map(([sentiment, count]) => (
                          <div key={sentiment} className="flex justify-between text-sm">
                            <span className={getSentimentColor(sentiment) + ' px-2 py-1 rounded'}>
                              {getSentimentIcon(sentiment)} {sentiment}
                            </span>
                            <span className="font-medium">{count}</span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-2 pt-2 border-t text-sm font-medium">
                        Total: {total}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'detailed' && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <select
                  value={filters.department}
                  onChange={(e) => setFilters({...filters, department: e.target.value})}
                  className="border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="">All Departments</option>
                  {departments.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
                <select
                  value={filters.sentiment}
                  onChange={(e) => setFilters({...filters, sentiment: e.target.value})}
                  className="border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="">All Sentiments</option>
                  {sentiments.map(sentiment => (
                    <option key={sentiment} value={sentiment}>{sentiment}</option>
                  ))}
                </select>
                <button
                  onClick={applyFilters}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Apply Filters
                </button>
              </div>
            </div>

            {/* Feedback Data Table */}
            <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-semibold text-gray-900">Employee Feedback Data</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Employee ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Department
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Feedback
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sentiment
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Confidence
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {feedbackData.map((feedback) => (
                      <tr key={feedback.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {feedback.employee_id || 'Anonymous'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {feedback.department}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 max-w-md">
                          <div className="truncate" title={feedback.feedback_text}>
                            {feedback.feedback_text}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded ${getSentimentColor(feedback.sentiment)}`}>
                            {getSentimentIcon(feedback.sentiment)} {feedback.sentiment}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {feedback.confidence_score ? (feedback.confidence_score * 100).toFixed(1) + '%' : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {new Date(feedback.timestamp).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI-Generated Actionable Insights</h3>
              <p className="text-gray-600 mb-6">
                Based on sentiment analysis, here are key insights and recommended actions to improve employee satisfaction.
              </p>
              
              {insights.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🎉</div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Great News!</h4>
                  <p className="text-gray-600">No critical issues detected. Employee sentiment appears healthy across the organization.</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {insights.map((insight, index) => (
                    <div key={index} className="border rounded-lg p-6">
                      <div className="flex items-start space-x-4">
                        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                          insight.priority === 'Critical' ? 'bg-red-100 text-red-800' :
                          insight.priority === 'High' ? 'bg-orange-100 text-orange-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {insight.priority} Priority
                        </div>
                        <div className="flex-1">
                          <h4 className="text-lg font-semibold text-gray-900 mb-2">{insight.category}</h4>
                          <p className="text-gray-700 mb-4">{insight.description}</p>
                          
                          <div className="mb-4">
                            <h5 className="font-medium text-gray-900 mb-2">Affected Departments:</h5>
                            <div className="flex flex-wrap gap-2">
                              {insight.affected_departments.map(dept => (
                                <span key={dept} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                                  {dept}
                                </span>
                              ))}
                            </div>
                          </div>
                          
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">Suggested Actions:</h5>
                            <ul className="list-disc list-inside space-y-1 text-gray-700">
                              {insight.suggested_actions.map((action, actionIndex) => (
                                <li key={actionIndex}>{action}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'submit' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Submit Employee Feedback</h3>
              <p className="text-gray-600 mb-6">
                Help us understand your workplace experience. Your feedback will be analyzed using AI to generate insights.
              </p>
              
              <form onSubmit={handleSubmitFeedback} className="space-y-6">
                <div>
                  <label htmlFor="employee_id" className="block text-sm font-medium text-gray-700 mb-2">
                    Employee ID (Optional)
                  </label>
                  <input
                    type="text"
                    id="employee_id"
                    value={newFeedback.employee_id}
                    onChange={(e) => setNewFeedback({...newFeedback, employee_id: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., EMP001 (leave blank for anonymous)"
                  />
                </div>
                
                <div>
                  <label htmlFor="department" className="block text-sm font-medium text-gray-700 mb-2">
                    Department *
                  </label>
                  <select
                    id="department"
                    value={newFeedback.department}
                    onChange={(e) => setNewFeedback({...newFeedback, department: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    {departments.map(dept => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label htmlFor="feedback_text" className="block text-sm font-medium text-gray-700 mb-2">
                    Your Feedback *
                  </label>
                  <textarea
                    id="feedback_text"
                    value={newFeedback.feedback_text}
                    onChange={(e) => setNewFeedback({...newFeedback, feedback_text: e.target.value})}
                    rows={6}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Share your thoughts, experiences, suggestions, or concerns..."
                    required
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                >
                  Submit Feedback for AI Analysis
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;