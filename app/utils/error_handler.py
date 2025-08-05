import re
from typing import Dict, Any

class ErrorHandler:
    """Handle errors and provide user-friendly messages"""
    
    @staticmethod
    def format_rate_limit_error(error_message: str) -> Dict[str, Any]:
        """Format rate limit errors with user-friendly messages"""
        
        # Extract quota information from error
        quota_info = {
            "metric": "Unknown",
            "limit": "Unknown",
            "current_usage": "Unknown",
            "reset_time": "Unknown"
        }
        
        # Parse the error message for quota details
        if "quota_metric" in error_message:
            metric_match = re.search(r'quota_metric: "([^"]+)"', error_message)
            if metric_match:
                quota_info["metric"] = metric_match.group(1)
        
        if "quota_value" in error_message:
            value_match = re.search(r'quota_value: (\d+)', error_message)
            if value_match:
                quota_info["limit"] = value_match.group(1)
        
        # Determine error type and provide appropriate response
        if "GenerateRequestsPerDayPerProjectPerModel-FreeTier" in error_message:
            return {
                "error_type": "daily_quota_exceeded",
                "title": "📅 Daily API Limit Reached",
                "message": "You've reached the daily limit for the free tier of Gemini AI.",
                "details": {
                    "limit": "250 requests per day",
                    "reset_time": "Midnight (UTC)",
                    "current_usage": "250+ requests"
                },
                "solutions": [
                    "🕐 **Wait for reset**: The quota resets daily at midnight UTC",
                    "💳 **Upgrade to paid tier**: Get unlimited requests with paid plan",
                    "⚡ **Reduce usage**: Wait a few hours before making more requests",
                    "🔄 **Use cached data**: Some queries can work with cached information"
                ],
                "immediate_actions": [
                    "Try again tomorrow",
                    "Check your API usage at https://ai.google.dev/",
                    "Consider upgrading to paid tier for higher limits"
                ]
            }
        
        elif "GenerateRequestsPerMinutePerProjectPerModel-FreeTier" in error_message:
            return {
                "error_type": "minute_quota_exceeded",
                "title": "⏱️ Rate Limit Exceeded",
                "message": "You're making requests too quickly. Please slow down.",
                "details": {
                    "limit": "10 requests per minute",
                    "reset_time": "Next minute",
                    "current_usage": "10+ requests in current minute"
                },
                "solutions": [
                    "⏳ **Wait 1 minute**: The limit resets every minute",
                    "🐌 **Slow down**: Space out your requests",
                    "📊 **Check usage**: Monitor your API usage",
                    "🔄 **Use cached data**: Some queries work without new API calls"
                ],
                "immediate_actions": [
                    "Wait 60 seconds before trying again",
                    "Reduce the frequency of your requests",
                    "Use the rate limit status endpoint to check current usage"
                ]
            }
        
        else:
            return {
                "error_type": "unknown_quota_error",
                "title": "⚠️ API Quota Issue",
                "message": "There's an issue with the API quota limits.",
                "details": {
                    "error": error_message[:200] + "..." if len(error_message) > 200 else error_message
                },
                "solutions": [
                    "🔄 **Try again later**: Quotas reset periodically",
                    "📞 **Contact support**: If the issue persists",
                    "💳 **Check billing**: Ensure your account is properly configured",
                    "📊 **Monitor usage**: Keep track of your API consumption"
                ],
                "immediate_actions": [
                    "Wait a few minutes and try again",
                    "Check your Google AI Studio dashboard",
                    "Verify your API key configuration"
                ]
            }
    
    @staticmethod
    def format_general_error(error_message: str) -> Dict[str, Any]:
        """Format general errors with user-friendly messages"""
        
        # Common error patterns
        if "timeout" in error_message.lower():
            return {
                "error_type": "timeout",
                "title": "⏰ Request Timeout",
                "message": "The request took too long to complete.",
                "solutions": [
                    "🔄 **Try again**: Sometimes temporary network issues occur",
                    "📡 **Check connection**: Ensure stable internet connection",
                    "⚡ **Simplify query**: Try a simpler question",
                    "🕐 **Wait and retry**: Try again in a few minutes"
                ]
            }
        
        elif "connection" in error_message.lower():
            return {
                "error_type": "connection_error",
                "title": "🌐 Connection Error",
                "message": "Unable to connect to the required services.",
                "solutions": [
                    "🌐 **Check internet**: Ensure you have internet connection",
                    "🔄 **Retry**: Network issues are often temporary",
                    "📡 **Check backend**: Verify backend services are running",
                    "⏰ **Wait**: Try again in a few minutes"
                ]
            }
        
        elif "authentication" in error_message.lower() or "unauthorized" in error_message.lower():
            return {
                "error_type": "auth_error",
                "title": "🔐 Authentication Error",
                "message": "There's an issue with API authentication.",
                "solutions": [
                    "🔑 **Check API key**: Verify your Google API key is correct",
                    "📧 **Verify account**: Ensure your Google account is active",
                    "💳 **Check billing**: Verify billing is set up correctly",
                    "🔄 **Restart service**: Restart the chatbot service"
                ]
            }
        
        else:
            return {
                "error_type": "unknown_error",
                "title": "❌ Unexpected Error",
                "message": "An unexpected error occurred while processing your request.",
                "solutions": [
                    "🔄 **Try again**: Sometimes errors are temporary",
                    "📝 **Simplify**: Try a simpler question",
                    "⏰ **Wait**: Try again in a few minutes",
                    "📞 **Report**: If the issue persists, report it"
                ],
                "details": {
                    "error": error_message[:200] + "..." if len(error_message) > 200 else error_message
                }
            }
    
    @staticmethod
    def create_user_friendly_response(error_info: Dict[str, Any]) -> str:
        """Create a user-friendly error response"""
        
        response = f"## {error_info['title']}\n\n"
        response += f"{error_info['message']}\n\n"
        
        if 'details' in error_info:
            response += "**Details:**\n"
            for key, value in error_info['details'].items():
                response += f"• {key.replace('_', ' ').title()}: {value}\n"
            response += "\n"
        
        response += "**Solutions:**\n"
        for solution in error_info['solutions']:
            response += f"{solution}\n"
        
        if 'immediate_actions' in error_info:
            response += "\n**Immediate Actions:**\n"
            for action in error_info['immediate_actions']:
                response += f"• {action}\n"
        
        response += "\n---\n"
        response += "💡 **Tip**: You can check your current usage with `/api/v1/rate-limit-status`"
        
        return response 