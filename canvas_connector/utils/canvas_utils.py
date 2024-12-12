# Package imports
from bs4 import BeautifulSoup
from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.requester import Requester
from canvasapi.quiz import Quiz, QuizSubmission
import os
import pandas as pd
import requests
import time
from typing import List

# Relative imports
from ..classes.canvas_file_submission import CanvasFileSubmission
from ..classes.extended_canvas_objects import SubmissionWithHistory


def get_canvas_record_by_id(canvas_object, id: int):
    for obj in canvas_object:
        if obj.id == id:
            return obj
    return None
def get_id_name_df(canvas_object) -> pd.DataFrame:
    """Returns a DataFrame with ids and names (or titles) from a Canvas object."""
    data = []
    for obj in canvas_object:
        row = {"id": obj.id}
        if hasattr(obj, "name"):
            row["name"] = obj.name
        elif hasattr(obj, "title"):
            row["title"] = obj.title
        data.append(row)
    return pd.DataFrame(data)

def get_courses_df(canvas: Canvas) -> pd.DataFrame:
    """Returns a DataFrame with course ids, names, and creation dates."""
    courses = canvas.get_courses()
    course_data = []
    for course in courses:
        course_data.append({
            "course_id": course.id,
            "course_name": course.name,
            "course_created_at": course.created_at,
        })
    return pd.DataFrame(course_data)
    

def get_users_df(course: Course, enrollment_type: list = None) -> pd.DataFrame:
    """Returns a DataFrame with user ids, names, and emails."""
    users = course.get_users(enrollment_type=enrollment_type)
    user_data = []
    for user in users:
        user_data.append({
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email
        })
    return pd.DataFrame(user_data)

def get_students_df(course: Course) -> pd.DataFrame:
    """Returns a DataFrame with student ids, names, and emails."""
    students = get_users_df(course, ["student"])
    students["user_role"] = "student"
    return students

def get_teachers_df(course: Course) -> pd.DataFrame:
    """Returns a DataFrame with teacher ids, names, and emails."""
    teachers = get_users_df(course, ["teacher"])
    teachers["user_role"] = "teacher"
    return teachers

def get_students_and_teachers_df(course: Course) -> pd.DataFrame:
    """Returns a DataFrame with student and teacher ids, names, and emails."""
    students = get_students_df(course)
    teachers = get_teachers_df(course)
    return pd.concat([students, teachers])

def get_course_quizzes_df(course: Course) -> pd.DataFrame:
    """Returns a DataFrame with course id, quiz ids and titles from a course."""
    quizzes = course.get_quizzes()
    quizzes = get_id_name_df(quizzes)
    quizzes["course_id"] = course.id
    return quizzes

def get_submissions_df(quiz: Quiz) -> pd.DataFrame:
    """Returns a DataFrame with quiz submissions from a quiz."""
    submissions = quiz.get_submissions()
    data = []
    for submission in submissions:
        row = {
            "quizSubmission_id": submission.id,
            "quiz_id": submission.quiz_id,
            "user_id": submission.user_id,
            "submission_id": submission.submission_id
        }
        data.append(row)
    return pd.DataFrame(data)

def get_submission_questions_df(submission: QuizSubmission) -> pd.DataFrame:
    """Returns a DataFrame with questions from a quiz submission."""
    questions = submission.get_submission_questions()
    data = []
    for question in questions:
        row = {
            "quizSubmissionQuestion_id": question.id,
            "quiz_id": question.quiz_id,
            "quizSubmission_id": question.quiz_submission_id,            
            "name": question.question_name,
        }
        data.append(row)
    return pd.DataFrame(data)

def get_all_pages_from_canvas_as_json(requester: Requester, url: str, timeout: int = 60) -> list:
    """Requests all pages from canvas and returns them as a list."""
    output = []
    links = {"next": url}
    start = time.time()
    while "next" in links:
        result = requester.request("GET", url)
        output += result.json()
        links = result.links
        if time.time()-start > timeout:
            print(f"Timeout ({timeout} seconds) reached!")
            break
    return output

def assemble_submissions_with_history(requester: Requester, submissions: list) -> List[SubmissionWithHistory]:
    return [SubmissionWithHistory(requester, submission) for submission in submissions]

def assemble_canvas_file_submissions(submissions: List[SubmissionWithHistory]) -> List[CanvasFileSubmission]:
    canvas_file_submissions = []
    for submission in submissions:
        canvas_file_submissions  += submission.return_all_file_submissions()
    return canvas_file_submissions

def whitelist_submissions(submissions: List[SubmissionWithHistory], user_id_whitelist: List[int]) -> List[SubmissionWithHistory]:
    return [submission for submission in submissions if submission.user_id in user_id_whitelist]

def blacklist_submissions(submissions: List[SubmissionWithHistory], user_id_blacklist: List[int]) -> List[SubmissionWithHistory]:
    return [submission for submission in submissions if submission.user_id not in user_id_blacklist]

def donwload_assignment_submissions(requester: Requester, course_id: int, assignment_id: int, user_id_blacklist: List[int] = None, user_id_whitelist: List[int] = None):
    # Get all submissions
    request_url = f"courses/{course_id}/assignments/{assignment_id}/submissions?include[]=submission_history&per_page=100"
    submissions = get_all_pages_from_canvas_as_json(requester, request_url)

    # Initialize convenience classes
    submissions = assemble_submissions_with_history(requester, submissions)

    # White and blacklist
    if user_id_whitelist is not None:
        submissions = whitelist_submissions(submissions, user_id_whitelist)
    elif user_id_blacklist is not None: 
        submissions = blacklist_submissions(submissions, user_id_blacklist)
    
    # Download files
    submissions = assemble_canvas_file_submissions(submissions)
    for submission in submissions:
        submission.download()
        
def upload_file_to_canvas(requester: Requester, file_path: str, canvas_folder_id: int):
    """Uploads a file to canvas"""
    # Request upload url
    file_name = file_path.split("/")[-1]
    file_size = os.stat(file_path).st_size
    post_data = {
        "name": file_name,
        "size": file_size,
        "parent_folder_id": canvas_folder_id
    }
    post_file_request = requester.request("POST", f"users/self/files", data=post_data)

    # Upload file
    upload_url = post_file_request.json()["upload_url"]
    upload_data = post_file_request.json()["upload_params"]
    return requests.post(upload_url, data=upload_data, files={"file": open(file_path, "rb")})