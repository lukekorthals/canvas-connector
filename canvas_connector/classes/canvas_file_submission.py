from canvasapi.requester import Requester
import os
import re
import requests
from requests import Response
import shutil


class CanvasFileSubmission:
    
    def __init__(self, 
                 requester: Requester, 
                 user_id: int, 
                 assignment_id: int, 
                 attempt: int, 
                 question_id: int, 
                 attachment_id: int, 
                 path_template: str = "submissions/user-{user_id}/assignment-{assignment_id}/use-{user_id}_ass-{assignment_id}_try-{attempt}_que-{question_id}_att-{attachment_id}{file_extension}") -> None:
        self.requester = requester
        self.user_id = user_id
        self.assignment_id = assignment_id
        self.attempt = attempt
        self.question_id = question_id
        self.attachment_id = attachment_id
        self.path_template = path_template
        self.file_extension = None
    
    def request_file(self) -> Response:
        # Get file
        file_url = self.requester.request("GET", f"files/{self.attachment_id}").json()["url"]
        response = requests.get(file_url, stream=True)

        # Retain file extension
        self.file_extension = "." + re.compile(r".*filename=\"(.*)\"").match(response.headers["Content-Disposition"]).group(1).split(".")[-1]

        # Return
        return response

    def assemble_out_path(self) -> str:
        return self.path_template.format(**self.__dict__)

    def download(self):
        """Downloads the file from canvas."""
        # Get file
        response = self.request_file()

        # Assemble filename
        out_path = self.assemble_out_path()

        # Create directories if necessary
        if "/" in out_path:
            folder_path = "/".join(out_path.split("/")[:-1])
            os.makedirs(folder_path, exist_ok=True)
        # Save file
        with open(out_path, "wb") as file:
            shutil.copyfileobj(response.raw, file)
        del response
