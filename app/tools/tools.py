import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool
from app.services.api_service import ApiService

# Initialize API service
api_service = ApiService()

class GetBatchesInfoTool(BaseTool):
    """Tool to get comprehensive batch information including sections"""
    name: str = "getBatchesInfo"
    description: str = "Get detailed information about batches including batch names and individual batch section counts. Use this when asked about number of batches, batch names, or batch details. NOT for total section count across all batches."
    
    def _run(self) -> str:
        try:
            result = api_service.get_all_batches()
            batches = result.get("allBatches", [])
            
            if not batches:
                return "No batches found in the system."
            
            total_sections = sum(batch.get("secCount", 0) for batch in batches)
            
            # Format the response nicely
            response = f"📊 **Batch Information**\n\n"
            response += f"**Total Batches:** {len(batches)}\n"
            response += f"**Total Sections:** {total_sections}\n\n"
            response += "**Batch Details:**\n"
            
            for batch in batches:
                response += f"• **{batch.get('name')}**: {batch.get('secCount', 0)} sections\n"
            
            response += f"\n📈 **Summary:** There are {len(batches)} batches with a total of {total_sections} sections."
            
            return response
        except Exception as e:
            return f"Error fetching batch information: {str(e)}"

class GetContestInfoTool(BaseTool):
    """Tool to get contest information without student details"""
    name: str = "getContestInfo"
    description: str = "Get contest information like contest names, questions asked, and general contest details. Use this when asked about contest details (not student performance). Contest details are the same across all batches. No input required."
    
    def _run(self) -> str:
        try:
            # Use batch24-28 since it has contest data
            result = api_service.get_all_contests("batch24-28")
            contests = result.get("allContests", [])
            
            if not contests:
                return "No contests found in the system."
            
            # Get detailed information for each contest
            detailed_contests = []
            for contest_title in contests:
                try:
                    contest_details = api_service.get_contest_details(contest_title)
                    if contest_details.get("contestDetails"):
                        detailed_contests.append(contest_details["contestDetails"])
                    else:
                        # Fallback to just the title if details not available
                        detailed_contests.append({"title": contest_title})
                except Exception as e:
                    # Fallback to just the title if details not available
                    detailed_contests.append({"title": contest_title})
            
            # Format the response nicely
            response = f"🏆 **Contest Information**\n\n"
            response += f"**Total Contests:** {len(detailed_contests)}\n\n"
            response += "**Available Contests:**\n"
            
            for contest in detailed_contests:
                title = contest.get('title', 'Unknown Contest')
                questions_count = len(contest.get('questions', []))
                response += f"• **{title}** ({questions_count} questions)\n"
            
            response += f"\n📈 **Summary:** There are {len(detailed_contests)} contests available in the system."
            
            return response
        except Exception as e:
            return f"Error fetching contest information: {str(e)}"

class GetStudentPerformanceTool(BaseTool):
    """Tool to get student performance with contest history (limited to latest 5 contests)"""
    name: str = "getStudentPerformance"
    description: str = "Get detailed student information including performance in latest 5 contests. Input format: 'batch,username' (e.g., 'batch24-25,john-doe')"
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split(',')
            if len(parts) != 2:
                return "Error: Input format should be 'batch,username' (e.g., 'batch24-25,john-doe')"
            
            batch, username = [s.strip() for s in parts]
            result = api_service.get_student(batch, username)
            student = result.get("student", {})
            
            if not student:
                return f"Student {username} not found in batch {batch}."
            
            # Limit to latest 5 contests
            recent_contests = student.get("recentContests", [])[:5]
            
            student_info = {
                "name": student.get("name"),
                "leetcodeUsername": student.get("leetcodeUsername"),
                "batch": batch,
                "section": student.get("section"),
                "rating": student.get("rating"),
                "totalSolved": student.get("totalSolved"),
                "easySolved": student.get("easySolved"),
                "mediumSolved": student.get("mediumSolved"),
                "hardSolved": student.get("hardSolved"),
                "globalRanking": student.get("globalRanking"),
                "totalParticipants": student.get("totalParticipants"),
                "topPercentage": student.get("topPercentage"),
                "badge": student.get("badge"),
                "recentContests": recent_contests,
                "note": "Only showing latest 5 contests as per system limitation"
            }
            
            return json.dumps(student_info, indent=2)
        except Exception as e:
            return f"Error fetching student performance: {str(e)}"

class FindTopStudentsTool(BaseTool):
    """Tool to find top students with both ranking and problems solved metrics"""
    name: str = "findTopStudents"
    description: str = "Find top students by both rating and total problems solved across all batches or specific batch. Always provides both rankings unless specified otherwise. Input format: 'limit,batch' (e.g., '50,batch24-25' or '10,all')"
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split(',')
            if len(parts) != 2:
                return "Error: Input format should be 'limit,batch' (e.g., '50,batch24-25' or '10,all')"
            
            limit_str, batch = [s.strip() for s in parts]
            limit = int(limit_str) if limit_str else 10
            
            all_students = []
            
            if batch.lower() == 'all':
                # Get students from all batches
                batches_result = api_service.get_all_batches()
                for batch_info in batches_result.get("allBatches", []):
                    try:
                        students_result = api_service.get_students_by_batch(batch_info["name"])
                        for student in students_result.get("students", []):
                            student["batch"] = batch_info["name"]
                            all_students.append(student)
                    except:
                        continue
            else:
                # Get students from specific batch
                students_result = api_service.get_students_by_batch(batch)
                for student in students_result.get("students", []):
                    student["batch"] = batch
                    all_students.append(student)
            
            # Create both rankings
            rating_ranking = sorted(
                [s for s in all_students if s.get("rating")],
                key=lambda x: x.get("rating", 0),
                reverse=True
            )[:limit]
            
            solved_ranking = sorted(
                [s for s in all_students if s.get("totalSolved")],
                key=lambda x: x.get("totalSolved", 0),
                reverse=True
            )[:limit]
            
            # Format results nicely
            rating_text = f"🏆 **Top {limit} Students by Rating:**\n"
            for i, student in enumerate(rating_ranking, 1):
                rating_text += f"{i}. **{student.get('name', 'N/A')}** ({student.get('leetcodeUsername', 'N/A')})\n"
                rating_text += f"   📍 Batch: {student.get('batch', 'N/A')}, Section: {student.get('section', 'N/A')}\n"
                rating_text += f"   ⭐ Rating: {student.get('rating', 0):.2f} | 📚 Problems Solved: {student.get('totalSolved', 0)}\n\n"
            
            solved_text = f"📚 **Top {limit} Students by Problems Solved:**\n"
            for i, student in enumerate(solved_ranking, 1):
                solved_text += f"{i}. **{student.get('name', 'N/A')}** ({student.get('leetcodeUsername', 'N/A')})\n"
                solved_text += f"   📍 Batch: {student.get('batch', 'N/A')}, Section: {student.get('section', 'N/A')}\n"
                solved_text += f"   📚 Problems Solved: {student.get('totalSolved', 0)} | ⭐ Rating: {student.get('rating', 0):.2f}\n\n"
            
            summary = f"📊 **Summary:** Analyzed {len(all_students)} students across all batches.\n\n"
            
            return summary + rating_text + solved_text
            
        except Exception as e:
            return f"Error finding top students: {str(e)}"

class FindTopStudentsBySectionTool(BaseTool):
    """Tool to find top students within a specific section"""
    name: str = "findTopStudentsBySection"
    description: str = "Find top students by both rating and total problems solved within a specific section. Input format: 'limit,batch,section' (e.g., '5,batch24-28,CSE-O' or '10,batch24-28,CSE-A')"
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split(',')
            if len(parts) != 3:
                return "Error: Input format should be 'limit,batch,section' (e.g., '5,batch24-28,CSE-O')"
            
            limit_str, batch, section = [s.strip() for s in parts]
            limit = int(limit_str) if limit_str else 10
            
            # Get students from specific batch
            students_result = api_service.get_students_by_batch(batch)
            students = students_result.get("students", [])
            
            if not students:
                return f"No students found in batch '{batch}'."
            
            # Filter students by section
            section_students = [s for s in students if s.get("section", "").upper() == section.upper()]
            
            if not section_students:
                return f"No students found in section '{section}' of batch '{batch}'."
            
            # Create both rankings for the section
            rating_ranking = sorted(
                [s for s in section_students if s.get("rating")],
                key=lambda x: x.get("rating", 0),
                reverse=True
            )[:limit]
            
            solved_ranking = sorted(
                [s for s in section_students if s.get("totalSolved")],
                key=lambda x: x.get("totalSolved", 0),
                reverse=True
            )[:limit]
            
            # Format results nicely
            response = f"🏆 **Top {limit} Students in {section} (Batch: {batch})**\n\n"
            
            if rating_ranking:
                response += f"⭐ **By Rating:**\n"
                for i, student in enumerate(rating_ranking, 1):
                    response += f"{i}. **{student.get('name', 'N/A')}** ({student.get('leetcodeUsername', 'N/A')})\n"
                    response += f"   ⭐ Rating: {student.get('rating', 0):.2f} | 📚 Problems Solved: {student.get('totalSolved', 0)}\n\n"
            
            if solved_ranking:
                response += f"📚 **By Problems Solved:**\n"
                for i, student in enumerate(solved_ranking, 1):
                    response += f"{i}. **{student.get('name', 'N/A')}** ({student.get('leetcodeUsername', 'N/A')})\n"
                    response += f"   📚 Problems Solved: {student.get('totalSolved', 0)} | ⭐ Rating: {student.get('rating', 0):.2f}\n\n"
            
            response += f"📊 **Summary:** Found {len(section_students)} students in section '{section}' of batch '{batch}'."
            
            return response
            
        except Exception as e:
            return f"Error finding top students in section: {str(e)}"

class GetTotalSectionsTool(BaseTool):
    """Tool to get total sections across all batches"""
    name: str = "getTotalSections"
    description: str = "Get the total number of sections across all batches. Use this when asked about total sections, how many sections, or sections are there."
    
    def _run(self) -> str:
        try:
            result = api_service.get_all_batches()
            batches = result.get("allBatches", [])
            
            if not batches:
                return "No batches found in the system."
            
            total_sections = sum(batch.get("secCount", 0) for batch in batches)
            
            # Format the response nicely
            response = f"📊 **Total Sections: {total_sections}**\n\n"
            response += "**Breakdown by Batch:**\n"
            
            for batch in batches:
                response += f"• **{batch.get('name')}**: {batch.get('secCount', 0)} sections\n"
            
            response += f"\n📈 **Summary:** There are {total_sections} sections across all batches."
            
            return response
        except Exception as e:
            return f"Error calculating total sections: {str(e)}"
    
class GetTotalStudentsTool(BaseTool):
    """Tool to get total student count across all batches"""
    name: str = "getTotalStudents"
    description: str = "Get the total number of students across all batches. Use this when asked about total student count."
    
    def _run(self) -> str:
        try:
            batches_result = api_service.get_all_batches()
            if not batches_result.get("allBatches"):
                return "No batches found in the system."
            
            total_students = 0
            batch_breakdown = []
            
            for batch_info in batches_result.get("allBatches", []):
                try:
                    students_result = api_service.get_students_by_batch(batch_info["name"])
                    student_count = len(students_result.get("students", []))
                    total_students += student_count
                    batch_breakdown.append({
                        "batch": batch_info["name"],
                        "students": student_count
                    })
                except Exception as e:
                    # Skip batches that fail
                    continue
            
            # Format the response nicely
            response = f"📊 **Total Students: {total_students}**\n\n"
            response += "**Breakdown by Batch:**\n"
            
            for batch_info in batch_breakdown:
                response += f"• **{batch_info['batch']}**: {batch_info['students']} students\n"
            
            response += f"\n📈 **Summary:** There are {total_students} students across all batches in the system."
            
            return response
        except Exception as e:
            return f"Error calculating total students: {str(e)}"

class GetStudentsByBatchTool(BaseTool):
    """Tool to get student count and details for a specific batch"""
    name: str = "getStudentsByBatch"
    description: str = "Get the number of students in a specific batch. Input format: 'batch_name' (e.g., 'batch24-28' or 'citarIII')"
    
    def _run(self, input_str: str) -> str:
        try:
            batch_name = input_str.strip()
            # Get students from the specified batch
            students_result = api_service.get_students_by_batch(batch_name)
            students = students_result.get("students", [])
            
            if not students:
                return f"No students found in batch '{batch_name}'."
            
            # Group students by section
            sections = {}
            for student in students:
                section = student.get("section", "Unknown")
                if section not in sections:
                    sections[section] = []
                sections[section].append(student)
            
            # Format the response nicely
            response = f"📊 **Students in {batch_name}**\n\n"
            response += f"**Total Students:** {len(students)}\n\n"
            response += "**Breakdown by Section:**\n"
            
            for section, section_students in sections.items():
                response += f"• **{section}**: {len(section_students)} students\n"
            
            response += f"\n📈 **Summary:** There are {len(students)} students in batch '{batch_name}'."
            
            return response
        except Exception as e:
            return f"Error fetching students for batch '{batch_name}': {str(e)}"

class GetStudentsBySectionTool(BaseTool):
    """Tool to get student count and details for a specific section"""
    name: str = "getStudentsBySection"
    description: str = "Get the number of students in a specific section. Input format: 'batch_name,section_name' (e.g., 'batch24-28,CSE-A' or 'citarIII,A')"
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split(',')
            if len(parts) != 2:
                return "Error: Input format should be 'batch_name,section_name' (e.g., 'batch24-28,CSE-A')"
            
            batch_name, section_name = [s.strip() for s in parts]
            
            # Get students from the specified batch
            students_result = api_service.get_students_by_batch(batch_name)
            students = students_result.get("students", [])
            
            if not students:
                return f"No students found in batch '{batch_name}'."
            
            # Filter students by section
            section_students = [s for s in students if s.get("section", "").upper() == section_name.upper()]
            
            if not section_students:
                return f"No students found in section '{section_name}' of batch '{batch_name}'."
            
            # Format the response nicely
            response = f"📊 **Students in {batch_name} - Section {section_name}**\n\n"
            response += f"**Total Students:** {len(section_students)}\n\n"
            response += "**Student Details:**\n"
            
            for i, student in enumerate(section_students[:10], 1):  # Show first 10 students
                response += f"{i}. **{student.get('name', 'N/A')}** ({student.get('leetcodeUsername', 'N/A')})\n"
                response += f"   ⭐ Rating: {student.get('rating', 0):.2f} | 📚 Problems Solved: {student.get('totalSolved', 0)}\n"
            
            if len(section_students) > 10:
                response += f"\n... and {len(section_students) - 10} more students\n"
            
            response += f"\n📈 **Summary:** There are {len(section_students)} students in section '{section_name}' of batch '{batch_name}'."
            
            return response
        except Exception as e:
            return f"Error fetching students for section: {str(e)}"

class GetContestLeaderboardTool(BaseTool):
    """Tool to get contest leaderboard for a specific contest"""
    name: str = "getContestLeaderboard"
    description: str = "Get contest leaderboard for a specific contest. Input format: 'batch_name,contest_title' (e.g., 'batch24-28,Weekly Contest 460')"
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split(',')
            if len(parts) != 2:
                return "Error: Input format should be 'batch_name,contest_title' (e.g., 'batch24-28,Weekly Contest 460')"
            
            batch_name, contest_title = [s.strip() for s in parts]
            
            # Get contest leaderboard
            leaderboard_result = api_service.get_contest_leaderboard(batch_name, contest_title)
            
            if not leaderboard_result:
                return f"No leaderboard data found for contest '{contest_title}' in batch '{batch_name}'."
            
            participants = leaderboard_result.get("contestStatusLeaderboard", {}).get("participants", [])
            non_participants = leaderboard_result.get("contestStatusLeaderboard", {}).get("nonParticipants", [])
            
            if not participants:
                return f"No participants found for contest '{contest_title}' in batch '{batch_name}'."
            
            # Sort participants by ranking
            participants.sort(key=lambda x: x.get("contestRanking", float('inf')))
            
            # Format the response nicely
            response = f"🏆 **Contest Leaderboard: {contest_title}**\n\n"
            response += f"**Batch:** {batch_name}\n"
            response += f"**Total Participants:** {len(participants)}\n"
            response += f"**Non-Participants:** {len(non_participants)}\n\n"
            response += "**Top 10 Participants:**\n"
            
            for i, participant in enumerate(participants[:10], 1):
                contest_data = participant.get("contest", {})
                name = participant.get('name') or participant.get('leetcodeUsername', 'Unknown Student')
                response += f"{i}. **{name}** ({participant.get('leetcodeUsername', 'N/A')})\n"
                response += f"   📍 Section: {participant.get('section', 'N/A')}\n"
                response += f"   🏅 Rank: {participant.get('contestRanking', 'N/A')}\n"
                response += f"   ⭐ Rating: {participant.get('rating', 0):.2f}\n"
                response += f"   📚 Problems Solved: {contest_data.get('problemsSolved', 0)}/{contest_data.get('totalProblems', 0)}\n"
                response += f"   ⏱️ Finish Time: {contest_data.get('finishTimeInSeconds', 0)}s\n\n"
            
            if len(participants) > 10:
                response += f"... and {len(participants) - 10} more participants\n\n"
            
            # Show highest ranking student
            if participants:
                top_student = participants[0]
                contest_data = top_student.get("contest", {})
                name = top_student.get('name') or top_student.get('leetcodeUsername', 'Unknown Student')
                response += f"🥇 **Highest Ranking Student:**\n"
                response += f"**{name}** ({top_student.get('leetcodeUsername', 'N/A')})\n"
                response += f"📍 Section: {top_student.get('section', 'N/A')}\n"
                response += f"🏅 Rank: {top_student.get('contestRanking', 'N/A')}\n"
                response += f"⭐ Rating: {top_student.get('rating', 0):.2f}\n"
                response += f"📚 Problems Solved: {contest_data.get('problemsSolved', 0)}/{contest_data.get('totalProblems', 0)}\n"
            
            return response
        except Exception as e:
            return f"Error fetching contest leaderboard: {str(e)}"

class MultiCollectionQueryTool(BaseTool):
    """Tool that can handle complex queries requiring multiple collections"""
    name: str = "multiCollectionQuery"
    description: str = "Handle complex queries that require data from multiple collections (batches, students, contests). Input: natural language question about cross-collection data."
    
    def _run(self, question: str) -> str:
        try:
            question_lower = question.lower()
            
            # Handle total sections query
            if "total sections" in question_lower or "sections across all batches" in question_lower:
                return self._get_total_sections()
            
            # Handle contest information query
            elif "contest" in question_lower and ("name" in question_lower or "questions" in question_lower):
                # Contest details are the same across all batches, so no batch specification needed
                return self._get_contest_info()
            
            # Handle student performance with contest limitation
            elif "student" in question_lower and ("performance" in question_lower or "contest" in question_lower):
                # Extract student info from question
                student_info = self._extract_student_from_question(question)
                if not student_info:
                    return "Please specify which student you want information for (format: batch,username)."
                return self._get_student_performance(student_info["batch"], student_info["username"])
            
            # Handle top students query
            elif "top" in question_lower and "student" in question_lower:
                limit, batch = self._extract_top_students_params(question)
                return self._get_top_students(limit, batch)
            
            # Handle section-specific top students query
            elif "top" in question_lower and ("cse-" in question_lower or "section" in question_lower):
                limit, batch = self._extract_top_students_params(question)
                return self._get_top_students(limit, batch)
            
            else:
                return "I can help with:\n1. Total sections across all batches\n2. Contest information\n3. Student performance (latest 5 contests only)\n4. Top students by rating and problems solved\n\nPlease rephrase your question."
                
        except Exception as e:
            return f"Error processing multi-collection query: {str(e)}"
    
    def _get_total_sections(self) -> str:
        """Get total sections across all batches"""
        result = api_service.get_all_batches()
        batches = result.get("allBatches", [])
        total_sections = sum(batch.get("secCount", 0) for batch in batches)
        
        breakdown = []
        for batch in batches:
            breakdown.append(f"• {batch.get('name')}: {batch.get('secCount', 0)} sections")
        
        return f"📊 **Total sections across ALL batches**: {total_sections}\n\n**Breakdown by batch:**\n" + "\n".join(breakdown)
    
    def _get_contest_info(self) -> str:
        """Get contest information (same across all batches)"""
        # Use any batch since contest details are the same across all batches
        batches_result = api_service.get_all_batches()
        if not batches_result.get("allBatches"):
            return "No batches found to fetch contest information."
        
        first_batch = batches_result["allBatches"][0]["name"]
        result = api_service.get_all_contests(first_batch)
        contests = result.get("allContests", [])
        
        if not contests:
            return "No contests found in the system."
        
        contest_list = []
        for contest_title in contests:
            try:
                contest_details = api_service.get_contest_details(contest_title)
                if contest_details.get("contestDetails"):
                    details = contest_details["contestDetails"]
                    questions_count = len(details.get("questions", []))
                    contest_list.append(f"• {details.get('title', contest_title)} ({questions_count} questions)")
                else:
                    contest_list.append(f"• {contest_title}")
            except Exception as e:
                contest_list.append(f"• {contest_title}")
        
        return f"📊 **Available Contests** (same across all batches):\n" + "\n".join(contest_list)
    
    def _get_student_performance(self, batch: str, username: str) -> str:
        """Get student performance with contest limitation"""
        result = api_service.get_student(batch, username)
        student = result.get("student", {})
        
        if not student:
            return f"Student {username} not found in batch {batch}."
        
        recent_contests = student.get("recentContests", [])[:5]
        
        contest_info = []
        for contest in recent_contests:
            contest_info.append(f"• {contest.get('title')}: Rank {contest.get('ranking')}, Solved {contest.get('problemsSolved')}/{contest.get('totalProblems')}")
        
        return f"Student: {student.get('name')}\nRating: {student.get('rating')}\nTotal Solved: {student.get('totalSolved')}\n\nLatest 5 contests:\n" + "\n".join(contest_info)
    
    def _get_top_students(self, limit: int, batch: str) -> str:
        """Get top students by both metrics"""
        all_students = []
        
        if batch.lower() == 'all':
            batches_result = api_service.get_all_batches()
            batch_names = []
            for batch_info in batches_result.get("allBatches", []):
                try:
                    students_result = api_service.get_students_by_batch(batch_info["name"])
                    for student in students_result.get("students", []):
                        student["batch"] = batch_info["name"]
                        all_students.append(student)
                    batch_names.append(batch_info["name"])
                except:
                    continue
            
            scope_info = f"📊 **Data from ALL batches**: {', '.join(batch_names)}"
        else:
            students_result = api_service.get_students_by_batch(batch)
            for student in students_result.get("students", []):
                student["batch"] = batch
                all_students.append(student)
            scope_info = f"📊 **Data from batch**: {batch}"
        
        rating_ranking = sorted(
            [s for s in all_students if s.get("rating")],
            key=lambda x: x.get("rating", 0),
            reverse=True
        )[:limit]
        
        solved_ranking = sorted(
            [s for s in all_students if s.get("totalSolved")],
            key=lambda x: x.get("totalSolved", 0),
            reverse=True
        )[:limit]
        
        rating_results = []
        for i, student in enumerate(rating_ranking, 1):
            batch_info = f" ({student.get('batch')})" if batch.lower() == 'all' else ""
            rating_results.append(f"{i}. {student.get('name')}{batch_info} - Rating: {student.get('rating')}")
        
        solved_results = []
        for i, student in enumerate(solved_ranking, 1):
            batch_info = f" ({student.get('batch')})" if batch.lower() == 'all' else ""
            solved_results.append(f"{i}. {student.get('name')}{batch_info} - Solved: {student.get('totalSolved')}")
        
        return f"{scope_info}\n\nTop {limit} students by rating:\n" + "\n".join(rating_results) + f"\n\nTop {limit} students by problems solved:\n" + "\n".join(solved_results)
    
    def _extract_batch_from_question(self, question: str) -> Optional[str]:
        """Extract batch name from question"""
        import re
        patterns = [
            r'batch\d{2}-\d{2}',
            r'batch\s*\d{2}-\d{2}',
            r'in\s+(\w+)',
            r'from\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1) if len(match.groups()) > 0 else match.group(0)
        
        return None
    
    def _extract_student_from_question(self, question: str) -> Optional[Dict[str, str]]:
        """Extract student information from question"""
        import re
        # Look for patterns like "student john-doe in batch24-25"
        pattern = r'student\s+(\w+)\s+in\s+(\w+)'
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return {"username": match.group(1), "batch": match.group(2)}
        return None
    
    def _extract_top_students_params(self, question: str) -> tuple:
        """Extract parameters for top students query"""
        import re
        
        # Extract limit
        limit_match = re.search(r'(\d+)', question)
        limit = int(limit_match.group(1)) if limit_match else 10
        
        # Extract batch
        batch = self._extract_batch_from_question(question)
        if not batch:
            batch = "all"
        
        return limit, batch

def get_tools():
    """Get all tools"""
    return [
        GetBatchesInfoTool(),
        GetContestInfoTool(),
        GetStudentPerformanceTool(),
        FindTopStudentsTool(),
        FindTopStudentsBySectionTool(),
        GetTotalSectionsTool(),
        GetTotalStudentsTool(),
        GetStudentsByBatchTool(),
        GetStudentsBySectionTool(),
        GetContestLeaderboardTool(),
        MultiCollectionQueryTool()
    ] 