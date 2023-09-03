# -*- coding: utf-8 -*-
"""
Created on Sat Jul 15 20:49:35 2023

@author: Elmor
"""
import csv
import time
import pygame
import glob
import copy
import numpy as np
from pygame_setup_easy import PyGameLoop

# from experimental_policy import QuestionPolicy

# from history_analysis_tools import pythonify_qar_history
from event_recorder import EventRecorder
import pandas as pd

MIN_SHOW_TIME_ALLOW_KEYPRESS = 0.5  # seconds, to prevent accidental doubletaps
RECORD_EVENTS = True
SAVE_RESPONSES = True
WORDS_PER_BLOCK = 15
INTERVAL_BETWEEN_BLOCK = 5  # seconds
REPETITIONS_PER_BLOCK = 2  # x times total
WAITING_TIME_AFTER_LAST_REPETITION = 10 * 60  # seconds (10 minutes here)
SHOW_CORRECT_ANSWER_AFTER_CORRECT_RESPONSE = False
REMOVE_SHOWING_CORRECT_ANSWER_AFTER = 3  # seconds

# DONE: Add experiment record,
# DONE: Change screen to different color when waiting
# TODO: push to git
# NO TODO: make distributions even (should not do, it works. Randomness is weird)


class NewLoop(PyGameLoop):
    def read_in_city_data(self):
        # Read in the cities, remove large cities (I will know them) and
        #
        df = pd.read_csv("us_cities.csv")
        # print(len(df))

        # print(df.groupby("STATE_CODE").size().sort_values())
        df2 = pd.read_csv("us-cities-top-1k.csv")
        df2_large = df2[df2["Population"] > 100_000]

        df_small = df[~df.CITY.isin(df2_large.City)]
        # print(len(df_small))
        df_small.drop_duplicates("CITY")

        # print(df_small.groupby("STATE_CODE").size().sort_values())
        # Still top 3: PA, NY, TX
        df_small_top3 = df_small.query(
            "STATE_CODE=='PA' or STATE_CODE=='NY' or STATE_CODE =='TX'"
        )
        self.city_statecode = list(df_small_top3[["CITY", "STATE_CODE"]].values)
        # [['New York City','NY'],
        #    [......],]

    def setup(self):
        # Load data
        self.read_in_city_data()

        # Initialize
        if RECORD_EVENTS:
            self.event_recorder = EventRecorder()
            self.event_recorder.set_save_path("logs")
            self.event_recorder.record_experiment_details(
                [
                    ["status_change", "program_start"],
                    ["time_of_start", time.time()],
                    ["words_per_word_block", WORDS_PER_BLOCK],
                    ["interval_between_block", INTERVAL_BETWEEN_BLOCK],
                    [
                        "waiting_time_after_last_repetition",
                        WAITING_TIME_AFTER_LAST_REPETITION,
                    ],
                    [
                        "show_correct_answer_after_correct_response",
                        SHOW_CORRECT_ANSWER_AFTER_CORRECT_RESPONSE,
                    ],
                    [
                        "remove_showing_correct_answer_after",
                        REMOVE_SHOWING_CORRECT_ANSWER_AFTER,
                    ],
                ]
            )

        self.shown_question_answer_pair = self.city_statecode[0]
        self.new_keystroke = False
        self.answer_keystroke = None
        self.time_of_last_response = None
        self.keystroke_answer_dict = {"z": "PA", "x": "NY", "c": "TX"}

        # Load in question-answer-response data
        qar_history = []

        history_files = glob.glob("logs/*_question_answer.log")
        for history_file in history_files:
            with open(history_file, "r") as f:  # , encoding="utf-8-sig"
                qar_history.extend(list(csv.reader(f)))
        self.prev_session_history = copy.deepcopy(qar_history)
        # Show first word
        # self.question_picker = QuestionPolicy()
        # self.question_picker.add_question_answer_response_history(qar_history)
        # self.question_picker.add_question_answer_pairs(self.city_statecode)
        self.question_index = 0
        self.block_indices = []
        self.pick_next_word()

        # Set feedback markers (red/green box + correct answer if wrong)
        self.correct_answer = None  # Was last answer correct?
        self.correction_to_show = None
        self.x = 450
        self.y = 300

    def handle_event(self, event):
        # If a keyboard letter is pressed
        if (
            event.type == pygame.KEYDOWN
            and len(event.unicode)
            and event.unicode[0].isalpha()
        ):
            # If in the same turn, the answer isn't given
            # and a valid keystroke is given
            if self.answer_keystroke is None and (
                event.unicode.lower() in ["z", "x", "c"]
            ):
                # z = der
                # x = das
                # y = die
                # prevent accidental doubletaps
                if (
                    time.time() - self.word_shown_timestamp
                    > MIN_SHOW_TIME_ALLOW_KEYPRESS
                ):
                    self.answer_keystroke = event.unicode.lower()
                    if RECORD_EVENTS:
                        self.event_recorder.record_keystroke(event.unicode)
                    self.new_keystroke = True

    def pick_word_block(self):
        seen_words = []
        for qar in self.prev_session_history:
            if qar[1] not in seen_words:
                seen_words.append(qar[1])
        print("Already seen")
        print(seen_words)
        unseen_indices = [
            ii
            for ii, qa_pair in enumerate(self.city_statecode)
            if not qa_pair[0] in seen_words
        ]
        sub_indices = np.random.choice(
            len(unseen_indices), size=WORDS_PER_BLOCK, replace=False
        )
        # It should be interesting to see the words being distributed evenly.
        # I just need to take a 1/3 chance for every group.
        # if I know more than that, I can use some prediction

        self.block_indices = np.array(unseen_indices)[sub_indices]
        self.current_block_repetition = 0
        self.halt_block_until = None

    def pick_next_word(self):
        # Pick new question-answer and record the showing

        # Select a block of words
        if len(self.block_indices) == 0:
            self.pick_word_block()

        # If we're not allowed to see a word, do not show a word
        if not self.halt_block_until is None:
            if time.time() - self.halt_block_until < 0:
                self.question_index = None
                return

        # Analyze this sesions history:
        # 1. Get the last question asked
        # 2. Get the number of times every word has been asked
        # 3. Get the timestamps of the end of the last block repetition

        # Get number of times asked
        # + last seen
        block_words = {
            self.city_statecode[ii][0]: {
                "num_seen": 0,
                "last_seen_index": None,
                "last_seen_timestamp": None,
            }
            for ii in self.block_indices
        }
        for ii, qar in enumerate(self.event_recorder.question_answer_record):
            if qar[1] in block_words:
                block_words[qar[1]]["num_seen"] += 1
                block_words[qar[1]]["last_seen_index"] = ii
                block_words[qar[1]]["last_seen_timestamp"] = qar[0]
        # print(block_words)

        # + last question
        last_question = None
        if len(self.event_recorder.question_answer_record) > 0:
            last_question = self.event_recorder.question_answer_record[-1][1]

        # Check if we do not repeat the last word

        # if block length ==1: show same word, after interval has been surpassed
        if len(self.block_indices) == 1:
            self.valid_indices = copy.deepcopy(self.block_indices)
        # if block length >1: show words, such that the last word is not shown again
        else:
            self.valid_indices = [
                ii
                for ii in self.block_indices
                if not self.city_statecode[ii][0] == last_question
            ]

        # for ii in self.valid_indices:
        #     print(self.city_statecode[ii][0])
        #     print(block_words[self.city_statecode[ii][0]]["num_seen"])
        #     print(self.current_block_repetition)
        # Allow only words to be shown if they weren't this repetition
        self.valid_indices = [
            ii
            for ii in self.valid_indices
            if block_words[self.city_statecode[ii][0]]["num_seen"]
            <= self.current_block_repetition
        ]

        # print("Block indices:")
        # for ii in self.block_indices:
        #     print(self.city_statecode[ii])
        # print()
        # print("Valid indices:")
        # for ii in self.valid_indices:
        #     print(self.city_statecode[ii])
        # print()
        # Take a random word from the leftover words
        if len(self.valid_indices) > 0:
            self.question_index = np.random.choice(self.valid_indices, 1)[0]
            # print([self.city_statecode[ii] for ii in self.block_indices])
        else:
            print("Incrementing block repetition count")
            # There are no words left, start second block
            self.question_index = None
            self.current_block_repetition += 1
            if self.current_block_repetition < REPETITIONS_PER_BLOCK:
                self.halt_block_until = time.time() + INTERVAL_BETWEEN_BLOCK
            elif self.current_block_repetition == REPETITIONS_PER_BLOCK:
                self.halt_block_until = (
                    time.time() + WAITING_TIME_AFTER_LAST_REPETITION
                )
                print(
                    "Done with repetitions, now waiting for experimental check"
                )
            else:
                self.halt_block_until = time.time() + 24 * 3600 * 60  # one day
                print("No words will be shown from now on")
                self.event_recorder.record_experiment_details(
                    [
                        ["status_change", "experiment_done"],
                        ["time_of_done", time.time()],
                    ]
                )
        self.word_shown_timestamp = time.time()

        # self.question_xpicker.add_question_answer_response_history(
        #     self.event_recorder.question_answer_record
        # )
        # index = self.question_picker.choose_new_question_answer_pair()
        # self.question_index = index

        if self.question_index is None:
            pass
            # show no word
        else:
            self.event_recorder.record_showing(
                self.city_statecode[self.question_index][0]
            )
        #     self.word_shown_timestamp = time.time()

    def update(self):
        """
        Check if answer is correct or not
            Record response in Recorder
            Pick next word
        Reset
        Save recording
        """

        if (
            not self.answer_keystroke is None
            and not self.question_index is None
        ):
            # Find out if the answer is correct, and if not,
            # what it should have been
            for key, val in self.keystroke_answer_dict.items():
                if self.answer_keystroke == key:  # e.g. "z"
                    if (
                        self.city_statecode[self.question_index][1] == val
                    ):  # e.g. "der"
                        self.correct_answer = True
                        if SHOW_CORRECT_ANSWER_AFTER_CORRECT_RESPONSE:
                            self.correction_to_show = (
                                self.city_statecode[self.question_index][1]
                                + " "
                                + self.city_statecode[self.question_index][0]
                            )
                        else:
                            self.correction_to_show = None
                    else:
                        self.correct_answer = False
                        self.correction_to_show = (
                            self.city_statecode[self.question_index][1]
                            + " "
                            + self.city_statecode[self.question_index][0]
                        )
                    self.time_of_last_response = time.time()
                    # And record the data and the time it has been shown already
                    time_until_answer = time.time() - self.word_shown_timestamp
                    if RECORD_EVENTS:
                        self.event_recorder.record_question_answer_data(
                            self.city_statecode[self.question_index][0],
                            self.city_statecode[self.question_index][1],
                            val,
                            time_until_answer,
                        )
            # Pick the next word
            if (
                self.answer_keystroke
                in ["z", "x", "c"]
                # and not self.question_index is 0
            ):
                self.pick_next_word()
        # IF no word was availabe
        # elif (
        #     self.answer_keystroke in ["z", "x", "c"]
        #     and self.question_index is None
        # ):
        #     self.pick_next_word()
        #     self.correction_to_show = None
        # The keystroke has been handled. Reset the keystroke data.
        self.new_keystroke = False
        self.answer_keystroke = None

        if SAVE_RESPONSES and RECORD_EVENTS:
            # Save any events that happened.
            self.event_recorder.save()

        if (
            not self.time_of_last_response is None
            and time.time()
            > self.time_of_last_response + REMOVE_SHOWING_CORRECT_ANSWER_AFTER
        ):
            self.correction_to_show = None
        if self.question_index is None:
            self.pick_next_word()

    def draw(self):
        """
        1. Draw correctness of last answer
        2. Draw question
        3. Draw instruction legend
        """
        white_color = (255, 255, 255)
        gray_color = (125, 125, 125)
        font_size = 50
        if self.question_index is None:
            self.screenSurface.fill((0, 125, 225))

        # Show correctness of last answer (and correct word if wrong)
        if not self.correct_answer is None:
            if self.correct_answer:
                pygame.draw.rect(
                    self.screenSurface,
                    color=(0, 255, 0),
                    rect=[150, 100, 120, 120],
                )
                self.draw_text(
                    self.correction_to_show,
                    210,
                    250,
                    color=white_color,
                    font_size=font_size,
                )

            else:
                pygame.draw.rect(
                    self.screenSurface,
                    color=(255, 0, 0),
                    rect=[150, 100, 120, 120],
                )
                self.draw_text(
                    self.correction_to_show,
                    210,
                    250,
                    color=white_color,
                    font_size=font_size,
                )
        # Keyboard legend dimensions
        instruction_x = 250
        instruction_y = 500
        instruction_y_spacing = 40

        if not self.question_index is None:
            # Show question

            self.current_shown_word = self.city_statecode[self.question_index][
                0
            ]
            self.draw_text(
                self.current_shown_word,
                self.x,
                self.y,
                color=white_color,
                font_size=font_size,
            )
            # Show keyboard legend
            for ii, (key, val) in enumerate(self.keystroke_answer_dict.items()):
                self.draw_text(
                    "%s = %s" % (key, val),
                    instruction_x,
                    instruction_y + ii * instruction_y_spacing,
                    color=white_color,
                    font_size=font_size,
                )
            # self.draw_text(
            #     "x = NY",
            #     instruction_x,
            #     instruction_y + instruction_y_spacing,
            #     color=white_color,
            #     font_size=font_size,
            # )
            # self.draw_text(
            #     "c = TX",
            #     instruction_x,
            #     instruction_y + 2 * +instruction_y_spacing,
            #     color=white_color,
            #     font_size=font_size,
            # )

        else:
            self.draw_text(
                "No word available",
                self.x,
                self.y,
                color=gray_color,
                font_size=font_size,
            )
            for ii, (key, val) in enumerate(self.keystroke_answer_dict.items()):
                self.draw_text(
                    "%s = %s" % (key, val),
                    instruction_x,
                    instruction_y + ii * instruction_y_spacing,
                    color=gray_color,
                    font_size=font_size,
                )
            # self.draw_text(
            #     "z = PA",
            #     instruction_x,
            #     instruction_y,
            #     color=gray_color,
            #     font_size=font_size,
            # )
            # self.draw_text(
            #     "x = NY",
            #     instruction_x,
            #     instruction_y + instruction_y_spacing,
            #     color=gray_color,
            #     font_size=font_size,
            # )
            # self.draw_text(
            #     "c = TX",
            #     instruction_x,
            #     instruction_y + 2 * +instruction_y_spacing,
            #     color=gray_color,
            #     font_size=font_size,
            # )

    def cleanup(self):
        """
        Save recorder
        """
        self.event_recorder.record_experiment_details(
            [["status_change", "program_quit"], ["time_of_quit", time.time()]]
        )

        if SAVE_RESPONSES and RECORD_EVENTS:
            self.event_recorder.save()


if __name__ == "__main__":
    loop = NewLoop()
    loop.loop()
