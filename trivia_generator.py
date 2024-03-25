import random


class Trivia_generator:

    def __init__(self):
        # Initial pool of questions and their answers
        self.initial_questions_and_answers = [
            ("2+2 equals 5.", 0)  # Add more questions as desired
        ]
        # Copy the initial pool to a working list that will be modified during the session
        self.available_questions_and_answers = self.initial_questions_and_answers.copy()

    def get_question(self):
        if not self.available_questions_and_answers:
            # Optionally reset the question list if all have been asked, or handle this case differently
            print("All questions have been asked, resetting the list.")
            self.available_questions_and_answers = self.initial_questions_and_answers.copy()

        # Randomly select a question and its answer from the available pool
        question, answer = random.choice(self.available_questions_and_answers)
        # Remove the selected question from the pool to avoid repetition
        self.available_questions_and_answers.remove((question, answer))
        return question, answer