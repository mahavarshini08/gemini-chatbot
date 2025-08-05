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
        self.cache_file = os.getenv("CACHE_FILE", "data_cache.json")
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        
        # Automatically validate cache on initialization
        self.auto_validate_cache()
    
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
            time_diff = datetime.now() - last_fetch
            return time_diff < self.cache_duration
        except Exception as e:
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
    
    def clear_cache_for_batch(self, batch: str):
        """Clear cache for a specific batch - useful for production debugging"""
        cache_data = self._load_cache()
        if "data" in cache_data and "students" in cache_data["data"]:
            if batch in cache_data["data"]["students"]:
                del cache_data["data"]["students"][batch]
                self._save_cache(cache_data)
                print(f"✅ Cleared cache for batch: {batch}")
            else:
                print(f"ℹ️ No cache found for batch: {batch}")
        else:
            print(f"ℹ️ No student cache found")
    
    def clear_all_cache(self):
        """Clear all cache - useful for production debugging"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                print("✅ Cleared all cache")
            else:
                print("ℹ️ No cache file found")
        except Exception as e:
            print(f"❌ Error clearing cache: {str(e)}")
    
    def get_cache_info(self) -> Dict:
        """Get information about current cache state"""
        cache_data = self._load_cache()
        info = {
            "cache_file": self.cache_file,
            "cache_exists": os.path.exists(self.cache_file),
            "last_fetch_time": cache_data.get("last_fetch_time"),
            "is_valid": self._is_cache_valid(cache_data),
            "cached_batches": []
        }
        
        if "data" in cache_data and "students" in cache_data["data"]:
            for batch, data in cache_data["data"]["students"].items():
                student_count = len(data.get("students", []))
                info["cached_batches"].append({
                    "batch": batch,
                    "student_count": student_count
                })
        
        return info
    
    def auto_validate_cache(self):
        """Automatically validate and fix cache issues in the background"""
        try:
            cache_data = self._load_cache()
            if not self._is_cache_valid(cache_data):
                return  # Cache is expired, will be refreshed on next request
            
            if "data" not in cache_data or "students" not in cache_data["data"]:
                return  # No student cache to validate
            
            known_empty_batches = ['batch22-26']
            problematic_batches = []
            
            for batch, data in cache_data["data"]["students"].items():
                students = data.get('students', [])
                student_count = len(students)
                
                # Check for suspicious cache entries (0 students)
                if student_count == 0 and batch not in known_empty_batches:
                    problematic_batches.append(batch)
                    continue
                
                # Enhanced validation: Check data quality for all students
                if student_count > 0:
                    data_quality_issues = self._validate_student_data_quality(students, batch)
                    if data_quality_issues:
                        problematic_batches.append(batch)
                        print(f"🔄 Data quality issues detected for {batch}: {data_quality_issues}")
            
            # Automatically clear problematic cache entries
            if problematic_batches:
                print(f"🔄 Auto-cache validation: Clearing {len(problematic_batches)} problematic entries")
                for batch in problematic_batches:
                    if batch in cache_data["data"]["students"]:
                        del cache_data["data"]["students"][batch]
                        print(f"  - Cleared cache for {batch}")
                
                self._save_cache(cache_data)
                print(f"✅ Auto-cache validation completed")
                
        except Exception as e:
            print(f"❌ Auto-cache validation error: {str(e)}")
    
    def _validate_student_data_quality(self, students: list, batch: str) -> str:
        """Validate data quality for all student fields"""
        issues = []
        
        for student in students:
            # Check for missing critical fields
            if not student.get('leetcodeUsername'):
                issues.append(f"Missing leetcodeUsername for student {student.get('id', 'unknown')}")
            
            if not student.get('name'):
                issues.append(f"Missing name for student {student.get('id', 'unknown')}")
            
            # Check for suspicious rating values (more realistic range)
            rating = student.get('rating')
            if rating is not None:
                if rating < 0 or rating > 4000:  # More realistic rating range for top performers
                    issues.append(f"Suspicious rating {rating} for {student.get('leetcodeUsername', 'unknown')}")
            
            # Check for suspicious problem counts
            total_solved = student.get('totalSolved', 0)
            easy_solved = student.get('easySolved', 0)
            medium_solved = student.get('mediumSolved', 0)
            hard_solved = student.get('hardSolved', 0)
            
            # Validate problem count consistency
            calculated_total = easy_solved + medium_solved + hard_solved
            if total_solved != calculated_total:
                issues.append(f"Problem count mismatch for {student.get('leetcodeUsername', 'unknown')}: total={total_solved}, sum={calculated_total}")
            
            # Check for unrealistic problem counts (more realistic threshold)
            if total_solved > 3000:  # More realistic for top performers
                issues.append(f"Unrealistic total problems {total_solved} for {student.get('leetcodeUsername', 'unknown')}")
            
            # Check for negative values
            if any(count < 0 for count in [easy_solved, medium_solved, hard_solved, total_solved]):
                issues.append(f"Negative problem counts for {student.get('leetcodeUsername', 'unknown')}")
            
            # Check for suspicious contest participation
            attended_contests = student.get('attendedContestsCount', 0)
            if attended_contests < 0 or attended_contests > 1000:
                issues.append(f"Suspicious contest count {attended_contests} for {student.get('leetcodeUsername', 'unknown')}")
            
            # Check for missing section info
            if not student.get('section'):
                issues.append(f"Missing section for {student.get('leetcodeUsername', 'unknown')}")
            
            # Check for missing roll number
            if not student.get('rollNumber'):
                issues.append(f"Missing roll number for {student.get('leetcodeUsername', 'unknown')}")
        
        return "; ".join(issues) if issues else None
    
    def get_cache_health_status(self) -> Dict:
        """Get detailed cache health status for monitoring"""
        cache_data = self._load_cache()
        known_empty_batches = ['batch22-26']
        
        health_status = {
            "overall_health": "healthy",
            "total_batches": 0,
            "healthy_batches": 0,
            "problematic_batches": [],
            "empty_batches": [],
            "data_quality_issues": [],
            "last_validation": cache_data.get("last_fetch_time")
        }
        
        if "data" in cache_data and "students" in cache_data["data"]:
            for batch, data in cache_data["data"]["students"].items():
                students = data.get('students', [])
                student_count = len(students)
                health_status["total_batches"] += 1
                
                if student_count > 0:
                    # Enhanced validation for data quality
                    data_quality_issues = self._validate_student_data_quality(students, batch)
                    if data_quality_issues:
                        health_status["problematic_batches"].append(batch)
                        health_status["data_quality_issues"].append({
                            "batch": batch,
                            "issues": data_quality_issues,
                            "student_count": student_count
                        })
                    else:
                        health_status["healthy_batches"] += 1
                elif batch in known_empty_batches:
                    health_status["empty_batches"].append(batch)
                else:
                    health_status["problematic_batches"].append(batch)
        
        # Determine overall health
        if health_status["problematic_batches"]:
            health_status["overall_health"] = "needs_attention"
        elif health_status["healthy_batches"] == 0:
            health_status["overall_health"] = "empty"
        
        return health_status
    
    def make_graphql_request(self, query: str, variables: Dict = {}) -> Dict:
        """Make a GraphQL request to the backend"""
        try:
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"},
                timeout=30  # Add timeout to prevent hanging requests
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                raise Exception(f"GraphQL Error: {json.dumps(data['errors'])}")
            
            return data.get("data", {})
        except requests.exceptions.Timeout:
            print(f"API Request Timeout: Request to {self.base_url} timed out")
            raise Exception("API request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            print(f"API Connection Error: Could not connect to {self.base_url}")
            raise Exception("Could not connect to the backend API. Please check if the server is running.")
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
        """Get all students in a specific batch with automated cache management"""
        # Try to get from cache first
        cached_data = self._get_from_cache("students")
        if cached_data and batch in cached_data:
            cached_result = cached_data[batch]
            student_count = len(cached_result.get('students', []))
            
            # If cache has students, use it
            if student_count > 0:
                return cached_result
            
            # If cache has 0 students, check if this is a known empty batch
            known_empty_batches = ['batch22-26']  # Add batches that legitimately have 0 students
            if batch in known_empty_batches:
                return cached_result
            
            # For other batches with 0 students, automatically clear cache and fetch fresh data
            print(f"🔄 Auto-detected stale cache for {batch} (0 students), fetching fresh data...")
            # Automatically clear the problematic cache entry
            if "data" in cached_data and "students" in cached_data["data"]:
                if batch in cached_data["data"]["students"]:
                    del cached_data["data"]["students"][batch]
                    self._save_cache(cached_data)
        
        # Fetch fresh data from API with automatic retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
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
                
                # Validate the fresh result
                student_count = len(result.get('students', []))
                
                # If we got students, cache it and return
                if student_count > 0:
                    cached_data = self._get_from_cache("students") or {}
                    cached_data[batch] = result
                    self._update_cache("students", cached_data)
                    print(f"✅ Successfully fetched {student_count} students for {batch}")
                    return result
                
                # If we got 0 students and it's not a known empty batch, try again
                if student_count == 0 and batch not in ['batch22-26']:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Attempt {attempt + 1}: Got 0 students for {batch}, retrying...")
                        continue
                    else:
                        print(f"⚠️ All attempts failed for {batch}, returning empty result")
                        return result
                
                # For known empty batches, cache the result
                if batch in ['batch22-26']:
                    cached_data = self._get_from_cache("students") or {}
                    cached_data[batch] = result
                    self._update_cache("students", cached_data)
                
                return result
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed for {batch}: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    print(f"❌ All attempts failed for {batch}")
                    # Return cached data as fallback, even if it's empty
                    if cached_data and batch in cached_data:
                        print(f"🔄 Falling back to cached data for {batch}")
                        return cached_data[batch]
                    # Return empty result if no cache available
                    return {"students": []}
        
        return {"students": []}
    
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
        cached_data = self._get_from_cache("contests") or {}
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
        cached_data = self._get_from_cache("contests") or {}
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
        cached_data = self._get_from_cache("contest_details") or {}
        cached_data[contest_title] = result
        self._update_cache("contest_details", cached_data)
        
        return result 