import json
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from app.config import Config

class ApiService:
    """Service for making GraphQL requests to the backend API with caching"""
    
    def __init__(self):
        self.base_url = Config.BACKEND_API_URL
        self.cache_file = "data_cache.json"
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    def _load_cache(self) -> Dict:
        """Load cache data from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {str(e)}")
        return {"last_fetch_time": None, "data": {}}
    
    def _save_cache(self, cache_data: Dict):
        """Save cache data to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {str(e)}")
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """Check if cache is still valid"""
        if not cache_data.get("last_fetch_time"):
            return False
        
        try:
            last_fetch = datetime.fromisoformat(cache_data["last_fetch_time"])
            return datetime.now() - last_fetch < self.cache_duration
        except:
            return False
    
    def _get_from_cache(self, key: str) -> Dict:
        """Get data from cache if valid"""
        cache_data = self._load_cache()
        if self._is_cache_valid(cache_data):
            return cache_data.get("data", {}).get(key, {})
        return {}
    
    def _update_cache(self, key: str, data: Dict):
        """Update cache with new data"""
        cache_data = self._load_cache()
        if "data" not in cache_data:
            cache_data["data"] = {}
        cache_data["data"][key] = data
        cache_data["last_fetch_time"] = datetime.now().isoformat()
        self._save_cache(cache_data)
    
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
        """Get all available batches with caching"""
        # Try to get from cache first
        cached_data = self._get_from_cache("batches")
        if cached_data:
            return cached_data
        
        # If not in cache, fetch from API
        query = """
        query {
            allBatches {
                name
                secCount
            }
        }
        """
        result = self.make_graphql_request(query)
        
        # Update cache
        self._update_cache("batches", result)
        
        return result
    
    def get_students_by_batch(self, batch: str) -> Dict:
        """Get all students in a specific batch with caching"""
        # Try to get from cache first
        cached_data = self._get_from_cache("students")
        if cached_data and batch in cached_data:
            return cached_data[batch]
        
        # If not in cache, fetch from API
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
            }
        }
        """
        result = self.make_graphql_request(query, {"batch": batch})
        
        # Update cache
        cached_data = self._get_from_cache("students")
        cached_data[batch] = result
        self._update_cache("students", cached_data)
        
        return result
    
    def get_student(self, batch: str, username: str) -> Dict:
        """Get detailed information about a specific student with caching"""
        # Try to get from cache first
        cached_data = self._get_from_cache("students")
        if cached_data and batch in cached_data:
            students = cached_data[batch].get("students", [])
            for student in students:
                if student.get("leetcodeUsername") == username:
                    return {"student": student}
        
        # If not in cache, fetch from API
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
    #problem
    def get_contest_leaderboard(self, batch: str, title: str) -> Dict:
        """Get contest leaderboard for a specific contest with caching"""
        # Try to get from cache first
        cached_data = self._get_from_cache("contests")
        cache_key = f"{batch}_{title}"
        if cached_data and cache_key in cached_data:
            return cached_data[cache_key]
        
        # If not in cache, fetch from API
        query = """
        query GetContestLeaderboard($batch: String!, $title: String!) {
            contestStatusLeaderboard(batch: $batch, title: $title) {
                participants {
                    id
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
                    leetcodeUsername
                    section
                    rollNumber
                    rating
                }
            }
        }
        """
        result = self.make_graphql_request(query, {"batch": batch, "title": title})
        
        # Update cache
        cached_data = self._get_from_cache("contests")
        cached_data[cache_key] = result
        self._update_cache("contests", cached_data)
        
        return result
    
    def get_all_contests(self, batch: str) -> Dict:
        """Get all contest titles for a specific batch with caching"""
        # Try to get from cache first
        cached_data = self._get_from_cache("contests")
        cache_key = f"{batch}_all"
        if cached_data and cache_key in cached_data:
            return cached_data[cache_key]
        
        # If not in cache, fetch from API
        query = """
        query GetAllContests($batch: String!) {
            allContests(batch: $batch)
        }
        """
        result = self.make_graphql_request(query, {"batch": batch})
        
        # Update cache
        cached_data = self._get_from_cache("contests")
        cached_data[cache_key] = result
        self._update_cache("contests", cached_data)
        
        return result
    
    def get_contest_details(self, contest_title: str) -> Dict:
        """Get detailed contest information including questions with caching"""
        # Try to get from cache first
        cached_data = self._get_from_cache("contest_details")
        if cached_data and contest_title in cached_data:
            return cached_data[contest_title]
        
        # If not in cache, fetch from API
        query = """
        query GetContestDetails($contestTitle: String!) {
            contestDetails(contestTitle: $contestTitle) {
                title
                questions {
                    id
                    title
                    title_slug
                    difficulty
                    category_slug
                    credit
                    question_id
                }
            }
        }
        """
        result = self.make_graphql_request(query, {"contestTitle": contest_title})
        
        # Update cache
        cached_data = self._get_from_cache("contest_details")
        cached_data[contest_title] = result
        self._update_cache("contest_details", cached_data)
        
        return result 