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
            
            # Check if student has any contest data
            if not recent_contests:
                return f"I cannot provide the latest contest details for {username} as there is no recent contest data available for this user in the system.\n\n**Available alternatives you can ask for:**\n1. Get student's overall performance (rating, problems solved)\n2. Get contest information and questions\n3. Get top students by rating and problems solved\n4. Get contest leaderboards for recent contests\n\n**💡 Tip:** Try asking for the student's overall performance instead."
            
            # Format response nicely
            response = f"📊 **Student Performance: {student.get('name', username)}**\n"
            response += f"📍 **Batch:** {batch}, **Section:** {student.get('section', 'N/A')}\n"
            response += f"⭐ **Rating:** {student.get('rating', 'N/A')}\n"
            response += f"📚 **Problems Solved:** {student.get('totalSolved', 0)} (Easy: {student.get('easySolved', 0)}, Medium: {student.get('mediumSolved', 0)}, Hard: {student.get('hardSolved', 0)})\n"
            response += f"🏆 **Global Ranking:** {student.get('globalRanking', 'N/A')}\n"
            response += f"📈 **Top Percentage:** {student.get('topPercentage', 'N/A')}%\n"
            response += f"🎖️ **Badge:** {student.get('badge', 'N/A')}\n\n"
            
            response += f"🏆 **Latest Contest Performance (Last 5 contests):**\n"
            for i, contest in enumerate(recent_contests, 1):
                response += f"{i}. **{contest.get('title', 'Unknown Contest')}**\n"
                response += f"   📅 Start Time: {contest.get('startTime', 'N/A')}\n"
                response += f"   🏅 Ranking: {contest.get('ranking', 'N/A')}\n"
                response += f"   ⭐ Rating: {contest.get('rating', 'N/A')}\n"
                response += f"   ✅ Problems Solved: {contest.get('problemsSolved', 0)}/{contest.get('totalProblems', 0)}\n"
                response += f"   🕒 Finish Time: {contest.get('finishTimeInSeconds', 'N/A')} seconds\n"
                response += f"   📊 Trend: {contest.get('trendDirection', 'N/A')}\n\n"
            
            response += f"**Note:** Only showing latest 5 contests as per system limitation."
            
            return response
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

class GetCrossBatchContestLeaderboardTool(BaseTool):
    """Tool to get contest leaderboard across all batches"""
    name: str = "getCrossBatchContestLeaderboard"
    description: str = "Get contest leaderboard across all batches for a specific contest. Input format: 'contest_title' (e.g., 'Weekly Contest 460')"
    
    def _run(self, input_str: str) -> str:
        try:
            contest_title = input_str.strip()
            
            # Get all batches first
            batches_result = api_service.get_all_batches()
            batches = batches_result.get("allBatches", [])
            
            if not batches:
                return "No batches found in the system."
            
            all_participants = []
            batch_breakdown = {}
            
            # Collect participants from all batches
            for batch in batches:
                try:
                    leaderboard_result = api_service.get_contest_leaderboard(batch["name"], contest_title)
                    participants = leaderboard_result.get("contestStatusLeaderboard", {}).get("participants", [])
                    
                    if participants:
                        # Add batch information to each participant
                        for participant in participants:
                            participant["batch"] = batch["name"]
                            all_participants.append(participant)
                        
                        batch_breakdown[batch["name"]] = len(participants)
                except Exception as e:
                    # Skip batches that fail
                    continue
            
            if not all_participants:
                return f"No participants found for contest '{contest_title}' across all batches."
            
            # Sort all participants by ranking
            all_participants.sort(key=lambda x: x.get("contestRanking", float('inf')))
            
            # Format the response nicely
            response = f"🏆 **Cross-Batch Contest Leaderboard: {contest_title}**\n\n"
            response += f"**Total Participants:** {len(all_participants)}\n"
            response += "**Breakdown by Batch:**\n"
            
            for batch_name, count in batch_breakdown.items():
                response += f"• **{batch_name}**: {count} participants\n"
            
            response += f"\n**Top 15 Participants (All Batches):**\n"
            
            for i, participant in enumerate(all_participants[:15], 1):
                contest_data = participant.get("contest", {})
                name = participant.get('name') or participant.get('leetcodeUsername', 'Unknown Student')
                response += f"{i}. **{name}** ({participant.get('leetcodeUsername', 'N/A')})\n"
                response += f"   📍 Batch: {participant.get('batch', 'N/A')}, Section: {participant.get('section', 'N/A')}\n"
                response += f"   🏅 Rank: {participant.get('contestRanking', 'N/A')}\n"
                response += f"   ⭐ Rating: {participant.get('rating', 0):.2f}\n"
                response += f"   📚 Problems Solved: {contest_data.get('problemsSolved', 0)}/{contest_data.get('totalProblems', 0)}\n"
                response += f"   ⏱️ Finish Time: {contest_data.get('finishTimeInSeconds', 0)}s\n\n"
            
            if len(all_participants) > 15:
                response += f"... and {len(all_participants) - 15} more participants\n\n"
            
            # Show highest ranking student
            if all_participants:
                top_student = all_participants[0]
                contest_data = top_student.get("contest", {})
                name = top_student.get('name') or top_student.get('leetcodeUsername', 'Unknown Student')
                response += f"🥇 **Overall Highest Ranking Student:**\n"
                response += f"**{name}** ({top_student.get('leetcodeUsername', 'N/A')})\n"
                response += f"📍 Batch: {top_student.get('batch', 'N/A')}, Section: {top_student.get('section', 'N/A')}\n"
                response += f"🏅 Rank: {top_student.get('contestRanking', 'N/A')}\n"
                response += f"⭐ Rating: {top_student.get('rating', 0):.2f}\n"
                response += f"📚 Problems Solved: {contest_data.get('problemsSolved', 0)}/{contest_data.get('totalProblems', 0)}\n"
            
            return response
        except Exception as e:
            return f"Error fetching cross-batch contest leaderboard: {str(e)}"

class GetSectionContestLeaderboardTool(BaseTool):
    """Tool to get contest leaderboard for a specific section"""
    name: str = "getSectionContestLeaderboard"
    description: str = "Get contest leaderboard for a specific section within a batch. Input format: 'batch_name,section_name,contest_title' (e.g., 'batch24-28,CSE-A,Weekly Contest 460')"
    
    def _run(self, input_str: str) -> str:
        try:
            parts = input_str.split(',')
            if len(parts) != 3:
                return "Error: Input format should be 'batch_name,section_name,contest_title' (e.g., 'batch24-28,CSE-A,Weekly Contest 460')"
            
            batch_name, section_name, contest_title = [s.strip() for s in parts]
            
            # Get contest leaderboard for the batch
            leaderboard_result = api_service.get_contest_leaderboard(batch_name, contest_title)
            
            if not leaderboard_result:
                return f"No leaderboard data found for contest '{contest_title}' in batch '{batch_name}'."
            
            participants = leaderboard_result.get("contestStatusLeaderboard", {}).get("participants", [])
            
            if not participants:
                return f"No participants found for contest '{contest_title}' in batch '{batch_name}'."
            
            # Filter participants by section
            section_participants = [
                p for p in participants 
                if p.get("section", "").upper() == section_name.upper()
            ]
            
            if not section_participants:
                return f"No participants found in section '{section_name}' for contest '{contest_title}' in batch '{batch_name}'."
            
            # Sort section participants by ranking
            section_participants.sort(key=lambda x: x.get("contestRanking", float('inf')))
            
            # Format the response nicely
            response = f"🏆 **Section Contest Leaderboard: {contest_title}**\n\n"
            response += f"**Batch:** {batch_name}\n"
            response += f"**Section:** {section_name}\n"
            response += f"**Total Participants:** {len(section_participants)}\n\n"
            response += "**All Section Participants:**\n"
            
            for i, participant in enumerate(section_participants, 1):
                contest_data = participant.get("contest", {})
                name = participant.get('name') or participant.get('leetcodeUsername', 'Unknown Student')
                response += f"{i}. **{name}** ({participant.get('leetcodeUsername', 'N/A')})\n"
                response += f"   🏅 Rank: {participant.get('contestRanking', 'N/A')}\n"
                response += f"   ⭐ Rating: {participant.get('rating', 0):.2f}\n"
                response += f"   📚 Problems Solved: {contest_data.get('problemsSolved', 0)}/{contest_data.get('totalProblems', 0)}\n"
                response += f"   ⏱️ Finish Time: {contest_data.get('finishTimeInSeconds', 0)}s\n\n"
            
            # Show highest ranking student in section
            if section_participants:
                top_student = section_participants[0]
                contest_data = top_student.get("contest", {})
                name = top_student.get('name') or top_student.get('leetcodeUsername', 'Unknown Student')
                response += f"🥇 **Top Student in {section_name}:**\n"
                response += f"**{name}** ({top_student.get('leetcodeUsername', 'N/A')})\n"
                response += f"🏅 Rank: {top_student.get('contestRanking', 'N/A')}\n"
                response += f"⭐ Rating: {top_student.get('rating', 0):.2f}\n"
                response += f"📚 Problems Solved: {contest_data.get('problemsSolved', 0)}/{contest_data.get('totalProblems', 0)}\n"
            
            return response
        except Exception as e:
            return f"Error fetching section contest leaderboard: {str(e)}"

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
                # Provide specific alternatives based on the query type
                if "compare" in question_lower or "comparison" in question_lower:
                    if "contest" in question_lower:
                        return "🔍 **Query Analysis:** I cannot directly compare contest performance across batches.\n\n**Available alternatives you can ask for:**\n1. Get contest leaderboard for each batch separately\n2. Get contest information and questions\n3. Get student performance in latest 5 contests\n4. Get top students by rating and problems solved\n\n**💡 Tip:** Try asking for any of these alternatives instead."
                    elif "problems" in question_lower or "solved" in question_lower:
                        return "🔍 **Query Analysis:** I cannot directly compare problem-solving statistics across batches.\n\n**Available alternatives you can ask for:**\n1. Get top students by problems solved for each batch\n2. Get student performance with total problems solved\n3. Get contest leaderboard with problems solved\n4. Get section-wise top students by problems solved\n\n**💡 Tip:** Try asking for any of these alternatives instead."
                    elif "rating" in question_lower:
                        return "🔍 **Query Analysis:** I cannot directly compare rating statistics across batches.\n\n**Available alternatives you can ask for:**\n1. Get top students by rating for each batch\n2. Get student performance with current rating\n3. Get contest leaderboard with ratings\n4. Get section-wise top students by rating\n\n**💡 Tip:** Try asking for any of these alternatives instead."
                    else:
                        return "🔍 **Query Analysis:** I cannot perform direct comparisons across batches.\n\n**Available alternatives you can ask for:**\n1. Get data for individual batches\n2. Get total students across all batches\n3. Get contest information and questions\n4. Get top students by rating and problems solved\n\n**💡 Tip:** Try asking for any of these alternatives instead."
                elif "across" in question_lower or "between" in question_lower:
                                          return "🔍 **Query Analysis:** I cannot provide cross-batch analysis.\n\n**Available alternatives you can ask for:**\n1. Get total students across all batches\n2. Get total sections across all batches\n3. Get contest information and questions\n4. Get top students by rating and problems solved\n\n**💡 Tip:** Try asking for any of these alternatives instead."
                else:
                                          return "🔍 **Query Analysis:** I cannot directly answer your specific query.\n\n**Available alternatives you can ask for:**\n1. Get total students across all batches\n2. Get contest information and questions\n3. Get student performance (latest 5 contests only)\n4. Get top students by rating and problems solved\n5. Get contest leaderboards for specific batches\n6. Get section-specific data\n\n**💡 Tip:** Try asking for any of these alternatives instead."
                
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

class GetAccurateTotalStudentsTool(BaseTool):
    """Tool to get accurate total student count using registration data only"""
    name: str = "getAccurateTotalStudents"
    description: str = "Get accurate total student count across all batches using registration data. Use this when asked about total student count."
    
    def _run(self, input_str: str = "") -> str:
        try:
            batches_result = api_service.get_all_batches()
            if not batches_result.get("allBatches"):
                return "No batches found in the system."
            
            total_students = 0
            batch_breakdown = []
            
            for batch_info in batches_result.get("allBatches", []):
                batch_name = batch_info["name"]
                
                # Get student count from registration data only
                try:
                    students_result = api_service.get_students_by_batch(batch_name)
                    student_count = len(students_result.get("students", []))
                except Exception as e:
                    student_count = 0
                
                total_students += student_count
                batch_breakdown.append({
                    "batch": batch_name,
                    "students": student_count
                })
            
            # Format the response nicely
            response = f"📊 **Total Students: {total_students}**\n\n"
            response += "**Breakdown by Batch:**\n"
            
            for batch_info in batch_breakdown:
                response += f"• **{batch_info['batch']}**: {batch_info['students']} students\n"
            
            response += f"\n📈 **Summary:** There are {total_students} students across all batches in the system."
            
            return response
        except Exception as e:
            return f"Error calculating accurate total students: {str(e)}"

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
        GetCrossBatchContestLeaderboardTool(),
        GetSectionContestLeaderboardTool(),
        MultiCollectionQueryTool(),
        GetAccurateTotalStudentsTool()
    ] 