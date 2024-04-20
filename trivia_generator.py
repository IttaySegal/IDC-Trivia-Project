import random


class TriviaGenerator:
    """
   A singleton class designed to provide a consistent set of trivia questions and answers
   throughout an application's lifecycle. This class ensures that the same pool of trivia
   questions is shared across all instances, preventing duplicate questions during a session.
   """

    _instance = None
    # singleton
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        # Initial pool of questions and their answers
        self.questions_and_answers = [
            ("Cats can make over 100 different sounds, while dogs can only make about 10.", 1),
            ("A group of flamingos is called a 'flamboyance'.", 1),
            ("Bananas grow on trees.", 0),  # They grow on large herb plants.
            ("Venus is the hottest planet in our solar system.", 1),
            ("A duck's quack doesn't echo, and no one knows why.", 0),  # Myth; a duck's quack does echo.
            ("Humans and dinosaurs coexisted at the same point in history.", 0),
            ("You can sneeze in your sleep.", 0),
            ("An octopus has three hearts.", 1),
            ("The Great Wall of China is visible from space.", 0),  # Not visible to the naked eye from space.
            ("A group of crows is called a 'murder'.", 1),
            ("Cats can bark.", 0),
            ("Ducks have three eyelids.", 1),
            ("Bananas grow upside down.", 1),
            ("A group of flamingos is called a 'flamboyance'.", 1),
            ("Humans can't breathe and swallow at the same time.", 1),
            ("Penguins can fly if they really try.", 0),
            ("A snail can sleep for three years.", 1),
            ("Venus is the hottest planet in our solar system.", 1),
            ("Some turtles can breathe through their butts.", 1),
            ("The moon is closer to Earth than Mars is.", 1),
            ("A cow-bison hybrid is called a 'Beefalo'.", 1),
            ("Sharks are immune to all known diseases.", 0),
            ("You can sneeze in your sleep.", 0),
            ("Octopuses have three hearts.", 1),
            ("The Great Wall of China is visible from space.", 0),
            ("Goldfish only have a memory of three seconds.", 0),
            ("The Atlantic Ocean is the warmest ocean on Earth.", 0),
            ("A group of unicorns is called a 'blessing'.", 1),
            ("Rainbows can only form in the morning.", 0),
            ("Chocolate can be lethal to dogs.", 1)

        ]
        # Copy the initial pool to a working list that will be modified during the session
        self.available_questions_and_answers = self.questions_and_answers.copy()

    def get_question(self):
        if not self.available_questions_and_answers:
            # Optionally reset the question list if all have been asked, or handle this case differently
            print("All questions have been asked, resetting the list.")
            self.available_questions_and_answers = self.questions_and_answers.copy()

        # Randomly select a question and its answer from the available pool
        question, answer = random.choice(self.available_questions_and_answers)
        # Remove the selected question from the pool to avoid repetition
        self.available_questions_and_answers.remove((question, answer))
        return question, answer

