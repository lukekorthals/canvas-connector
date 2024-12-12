from canvasapi.canvas_object import CanvasObject
from canvasapi.submission import Submission
from typing import List


from .canvas_file_submission import CanvasFileSubmission


class SubmissionDataEntry(CanvasObject):
    def __init__(self, requester, attributes):
        super(SubmissionDataEntry, self).__init__(requester, attributes)


class SubmissionHistoryEntry(CanvasObject):
    def __init__(self, requester, attributes):
        self.submission_data = []
        self.cached_due_date_date = None
        super(SubmissionHistoryEntry, self).__init__(requester, attributes)
        self.assemble_submission_data()

    def assemble_submission_data(self):
        new_submission_data = []
        for i in range(len(self.submission_data)):
            new_submission_data.append(SubmissionDataEntry(requester=self._requester, attributes=self.submission_data[i]))
        self.__setattr__("submission_data", new_submission_data)


class SubmissionWithHistory(Submission):
    def __init__(self, requester, attributes):
        self.submission_history = []
        super(SubmissionWithHistory, self).__init__(requester, attributes)
        self.assemble_submission_history()
    
    def assemble_submission_history(self):
        new_submission_history = []
        for i in range(len(self.submission_history)):
            new_submission_history.append(SubmissionHistoryEntry(requester=self._requester, attributes=self.submission_history[i]))
        self.__setattr__("submission_history", new_submission_history)
    
    def return_all_file_submissions(self, path_template: str = None) -> List[CanvasFileSubmission]:
        output = []
        for history_entry in self.submission_history:
            for data_entry in history_entry.submission_data:
                if not hasattr(data_entry, "attachment_ids") or not data_entry.attachment_ids:
                    continue
                for attachment_id in data_entry.attachment_ids:
                    if path_template is not None:
                        cfs = CanvasFileSubmission(
                            self._requester,
                            self.user_id,
                            self.assignment_id,
                            history_entry.attempt,
                            history_entry.submitted_at_date,
                            history_entry.cached_due_date_date,
                            data_entry.question_id,
                            attachment_id,
                            path_template
                        )
                    else:
                        cfs = CanvasFileSubmission(
                            self._requester,
                            self.user_id,
                            self.assignment_id,
                            history_entry.attempt,
                            history_entry.submitted_at_date,
                            history_entry.cached_due_date_date,
                            data_entry.question_id,
                            attachment_id
                        )
                    output.append(cfs)
        return output