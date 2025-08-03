import json
import requests
from typing import Dict, Any
from app.config import Config

class ApiService:
    """Service for making GraphQL requests to the backend API"""
    
    def __init__(self):
        self.base_url = Config.BACKEND_API_URL
    
    def make_graphql_request(self, query: str, variables: Dict = {}) -> Dict:
        """Make a GraphQL request to the backend"""
        try:
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                raise Exception(f"GraphQL Error: {json.dumps(data['errors'])}")
            
            return data.get("data", {})
        except Exception as e:
            print(f"API Request Error: {str(e)}")
            raise e
    
    def get_all_batches(self) -> Dict:
        """Get all available batches"""
        query = """
        query {
            allBatches {
                name
                secCount
            }
        }
        """
        return self.make_graphql_request(query)
    
    def get_students_by_batch(self, batch: str) -> Dict:
        """Get all students in a specific batch"""
        query = """
        query GetStudents($batch: String!) {
            students(batch: $batch) {
                id
                name
                leetcodeUsername
                section
                rollNumber
                totalSolved
                easySolved
                mediumSolved
                hardSolved
                attendedContestsCount
                rating
                globalRanking
                totalParticipants
                topPercentage
                badge
                lastUpdatedAt
                recentContests {
                    title
                    startTime
                    ranking
                    rating
                    attended
                    problemsSolved
                    totalProblems
                    trendDirection
                    finishTimeInSeconds
                }
                latestContests {
                    title
                    data {
                        title
                        startTime
                        ranking
                        rating
                        attended
                        problemsSolved
                        totalProblems
                        trendDirection
                        finishTimeInSeconds
                    }
                }
            }
        }
        """
        return self.make_graphql_request(query, {"batch": batch})
    
    def get_student(self, batch: str, username: str) -> Dict:
        """Get detailed information about a specific student"""
        query = """
        query GetStudent($batch: String!, $username: String!) {
            student(batch: $batch, username: $username) {
                id
                name
                leetcodeUsername
                section
                rollNumber
                totalSolved
                easySolved
                mediumSolved
                hardSolved
                attendedContestsCount
                rating
                globalRanking
                totalParticipants
                topPercentage
                badge
                lastUpdatedAt
                recentContests {
                    title
                    startTime
                    ranking
                    rating
                    attended
                    problemsSolved
                    totalProblems
                    trendDirection
                    finishTimeInSeconds
                }
                latestContests {
                    title
                    data {
                        title
                        startTime
                        ranking
                        rating
                        attended
                        problemsSolved
                        totalProblems
                        trendDirection
                        finishTimeInSeconds
                    }
                }
            }
        }
        """
        return self.make_graphql_request(query, {"batch": batch, "username": username})
    
    def get_contest_leaderboard(self, batch: str, title: str) -> Dict:
        """Get contest leaderboard for a specific contest"""
        query = """
        query GetContestLeaderboard($batch: String!, $title: String!) {
            contestStatusLeaderboard(batch: $batch, title: $title) {
                participants {
                    id
                    name
                    leetcodeUsername
                    section
                    rollNumber
                    rating
                    contestRanking
                    contest {
                        title
                        startTime
                        ranking
                        rating
                        attended
                        problemsSolved
                        totalProblems
                        trendDirection
                        finishTimeInSeconds
                    }
                }
                nonParticipants {
                    id
                    name
                    leetcodeUsername
                    section
                    rollNumber
                    rating
                }
            }
        }
        """
        return self.make_graphql_request(query, {"batch": batch, "title": title})
    
    def get_all_contests(self, batch: str) -> Dict:
        """Get all contest titles for a specific batch"""
        query = """
        query GetAllContests($batch: String!) {
            allContests(batch: $batch)
        }
        """
        return self.make_graphql_request(query, {"batch": batch}) 