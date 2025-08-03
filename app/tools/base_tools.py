import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from langchain.tools import BaseTool
from app.services.api_service import ApiService

# Initialize API service
api_service = ApiService()

class GetAllBatchesTool(BaseTool):
    """Tool to get all available batches"""
    name: str = "getAllBatches"
    description: str = "Get all available batches in the system"
    
    def _run(self) -> str:
        try:
            result = api_service.get_all_batches()
            return json.dumps(result.get("allBatches", []), indent=2)
        except Exception as e:
            return f"Error fetching batches: {str(e)}"

class GetStudentsByBatchTool(BaseTool):
    """Tool to get all students in a specific batch"""
    name: str = "getStudentsByBatch"
    description: str = "Get all students in a specific batch with their LeetCode statistics"
    
    def _run(self, batch: str) -> str:
        try:
            result = api_service.get_students_by_batch(batch)
            return json.dumps(result.get("students", []), indent=2)
        except Exception as e:
            return f"Error fetching students for batch {batch}: {str(e)}"

class GetStudentTool(BaseTool):
    """Tool to get detailed information about a specific student"""
    name: str = "getStudent"
    description: str = "Get detailed information about a specific student by their LeetCode username"
    
    def _run(self, input_str: str) -> str:
        try:
            batch, username = [s.strip() for s in input_str.split(',', 1)]
            result = api_service.get_student(batch, username)
            return json.dumps(result.get("student", {}), indent=2)
        except Exception as e:
            return f"Error fetching student: {str(e)}"

class GetContestLeaderboardTool(BaseTool):
    """Tool to get contest leaderboard"""
    name: str = "getContestLeaderboard"
    description: str = "Get contest leaderboard showing participants and non-participants for a specific contest"
    
    def _run(self, input_str: str) -> str:
        try:
            batch, title = [s.strip() for s in input_str.split(',', 1)]
            result = api_service.get_contest_leaderboard(batch, title)
            return json.dumps(result.get("contestStatusLeaderboard", {}), indent=2)
        except Exception as e:
            return f"Error fetching contest leaderboard: {str(e)}"

class GetAllContestsTool(BaseTool):
    """Tool to get all contests for a batch"""
    name: str = "getAllContests"
    description: str = "Get all contest titles available for a specific batch"
    
    def _run(self, batch: str) -> str:
        try:
            result = api_service.get_all_contests(batch)
            return json.dumps(result.get("allContests", []), indent=2)
        except Exception as e:
            return f"Error fetching contests for batch {batch}: {str(e)}"

class CompareSectionsTool(BaseTool):
    """Tool to compare two sections within a batch"""
    name: str = "compareSections"
    description: str = "Compare two sections within a batch by various metrics (rating, solved problems, etc.)"
    
    def _run(self, input_str: str) -> str:
        try:
            batch, section1, section2, metric = [s.strip() for s in input_str.split(',')]
            result = api_service.get_students_by_batch(batch)
            students = result.get("students", [])
            
            sec1_students = [s for s in students if s.get("section") == section1]
            sec2_students = [s for s in students if s.get("section") == section2]
            
            comparison = {}
            
            if metric == "rating":
                sec1_avg = sum(s.get("rating", 0) for s in sec1_students) / len(sec1_students) if sec1_students else 0
                sec2_avg = sum(s.get("rating", 0) for s in sec2_students) / len(sec2_students) if sec2_students else 0
                comparison = {
                    section1: {"averageRating": sec1_avg, "studentCount": len(sec1_students)},
                    section2: {"averageRating": sec2_avg, "studentCount": len(sec2_students)},
                    "difference": sec1_avg - sec2_avg
                }
            elif metric == "solved":
                sec1_avg = sum(s.get("totalSolved", 0) for s in sec1_students) / len(sec1_students) if sec1_students else 0
                sec2_avg = sum(s.get("totalSolved", 0) for s in sec2_students) / len(sec2_students) if sec2_students else 0
                comparison = {
                    section1: {"averageSolved": sec1_avg, "studentCount": len(sec1_students)},
                    section2: {"averageSolved": sec2_avg, "studentCount": len(sec2_students)},
                    "difference": sec1_avg - sec2_avg
                }
            
            return json.dumps(comparison, indent=2)
        except Exception as e:
            return f"Error comparing sections: {str(e)}"

class FindTopStudentsTool(BaseTool):
    """Tool to find top students across all batches"""
    name: str = "findTopStudents"
    description: str = "Find top students across all batches by rating, solved problems, or contest performance"
    
    def _run(self, input_str: str) -> str:
        try:
            metric, limit = input_str.split(',')
            metric = metric.strip()
            limit = int(limit.strip()) if limit.strip() else 10
            
            batches_result = api_service.get_all_batches()
            all_students = []
            
            for batch in batches_result.get("allBatches", []):
                students_result = api_service.get_students_by_batch(batch["name"])
                for student in students_result.get("students", []):
                    student["batch"] = batch["name"]
                    all_students.append(student)
            
            sorted_students = []
            if metric == "rating":
                sorted_students = sorted(
                    [s for s in all_students if s.get("rating")],
                    key=lambda x: x.get("rating", 0),
                    reverse=True
                )[:limit]
            elif metric == "solved":
                sorted_students = sorted(
                    [s for s in all_students if s.get("totalSolved")],
                    key=lambda x: x.get("totalSolved", 0),
                    reverse=True
                )[:limit]
            
            return json.dumps(sorted_students, indent=2)
        except Exception as e:
            return f"Error finding top students: {str(e)}"

class FindInactiveStudentsTool(BaseTool):
    """Tool to find inactive students"""
    name: str = "findInactiveStudents"
    description: str = "Find students who have not participated in recent contests or have low activity"
    
    def _run(self, input_str: str) -> str:
        try:
            batch, days = input_str.split(',')
            batch = batch.strip()
            days = int(days.strip()) if days.strip() else 7
            
            result = api_service.get_students_by_batch(batch)
            students = result.get("students", [])
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            inactive_students = []
            for student in students:
                has_recent_activity = False
                for contest in student.get("recentContests", []):
                    contest_date = datetime.fromtimestamp(contest.get("startTime", 0))
                    if contest_date > cutoff_date and contest.get("attended") is not False:
                        has_recent_activity = True
                        break
                
                if not has_recent_activity:
                    inactive_students.append(student)
            
            return json.dumps(inactive_students, indent=2)
        except Exception as e:
            return f"Error finding inactive students: {str(e)}"

# List of all available tools
def get_all_tools():
    """Get all available tools"""
    return [
        GetAllBatchesTool(),
        GetStudentsByBatchTool(),
        GetStudentTool(),
        GetContestLeaderboardTool(),
        GetAllContestsTool(),
        CompareSectionsTool(),
        FindTopStudentsTool(),
        FindInactiveStudentsTool(),
    ] 