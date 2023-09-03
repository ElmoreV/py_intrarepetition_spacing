# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 11:20:15 2023

@author: Elmor
"""
import time
import datetime
import os


class EventRecorder:
    # This class records keystrokes, the showing of words and
    # the answers to the questions + timing

    def __init__(self):
        # Create emptry lists, save current time
        self.keystroke_record = []
        self.showing_record = []
        self.question_answer_record = []
        self.experiment_record = []
        self.path = None
        self.date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def set_save_path(self, path):
        self.path = path

    def record_keystroke(self, key):
        # Record the keystroke
        current_timestamp = time.time()
        keystroke = [key, current_timestamp]
        self.keystroke_record.append(keystroke)

    def record_showing(self, word):
        # Record when a new word gets shown
        current_timestamp = time.time()
        event = [word, current_timestamp]
        self.showing_record.append(event)

    def record_question_answer_data(
        self, question, correct_answer, given_answer, time_until_answer
    ):
        # Record that a question is shown, and an answer is given.
        # Also record the correct answer
        current_timestamp = time.time()

        qa_data = [
            current_timestamp,
            question,
            correct_answer,
            given_answer,
            time_until_answer,
        ]
        self.question_answer_record.append(qa_data)

    def record_experiment_details(self, list_of_records):
        """
        Expects a List[List[2]]
        """
        for record in list_of_records:
            if len(record) == 2:
                self.experiment_record.append(record)
            else:
                raise ValueError(
                    "Every experiment record should be at most a key,value pair"
                )

    def save(self):
        if self.path is None:
            prefix = self.date_str
        else:
            prefix = self.path + os.sep + self.date_str
        # Save the keystroke, word showing, and word answering.
        with open(prefix + "_keystroke_record.log", "w") as f:
            for keystroke in self.keystroke_record:
                f.write(str(keystroke[1]) + "," + str(keystroke[0]) + "\n")
        with open(prefix + "_event_record.log", "w") as f:
            for event in self.showing_record:
                f.write(str(event[1]) + "," + str(event[0]) + "\n")
        with open(prefix + "_question_answer.log", "w") as f:
            for qa_data in self.question_answer_record:
                f.write(
                    ",".join([str(qa_data[ii]) for ii in range(len(qa_data))])
                    + "\n"
                )
        with open(prefix + "_experiment.log", "w") as f:
            for line in self.experiment_record:
                f.write(str(line[0]) + "," + str(line[1]) + "\n")
