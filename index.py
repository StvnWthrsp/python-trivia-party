import sys
import requests
from requests.sessions import session
from random import shuffle
sys.path.append('./package')

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.attributes_manager import AttributesManager
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

from ask_sdk_core.skill_builder import SkillBuilder
sb = SkillBuilder()

SKILL_NAME = "Trivia Party"
NUMBER_OF_QUESTIONS = 5
CATEGORIES = {
    'general': 9,
    'books': 10,
    'film': 11,
    'music': 12,
    'television': 14,
    'video games': 15,
    'science': 17,
    'math': 19,
    'history': 23,
    'geography': 22,
    'animal': 27
}

# --------------------
# Helper Functions
# --------------------
def getGameQuestions(category_number, number_questions):
    URL = f"https://opentdb.com/api.php?amount={number_questions}&category={category_number}&type=multiple"
    r = requests.get(url = URL)
    data = r.json()

    return data["results"]

def getCategoryId(category_string):
    # if category_string == "general":
    #     return 9
    # elif category_string == "books":
    #     return 10
    # elif category_string == "film":
    #     return 11
    # elif category_string == "music":
    #     return 12
    # elif category_string == "television" or category_string == "TV":
    #     return 14
    # elif category_string == "video games":
    #     return 15
    # elif category_string == "science":
    #     return 17
    # elif category_string == "math":
    #     return 19
    # elif category_string == "history":
    #     return 23
    # elif category_string == "geography":
    #     return 22
    # elif category_string == "animal" or category_string == "animals":
    #     return 27
    # else:
    #     return -1
    category_id = CATEGORIES.get(category_string)
    return category_id

def readQuestionAndShuffledAnswers(handler_input):
    session_attributes = handler_input.attributes_manager.session_attributes
    player_index = session_attributes['current_player_index']
    question_index = session_attributes['current_question_index']
    speech_text = f"{session_attributes['players'][player_index]}, it's your turn. Question {question_index + 1}.\n"
    reprompt_text = f"{session_attributes['game_questions'][question_index]['question']} "

    possible_answers = session_attributes['game_questions'][question_index]['incorrect_answers']
    possible_answers.append(session_attributes['game_questions'][question_index]['correct_answer'])
    shuffle(possible_answers)
    correct_index = possible_answers.index(session_attributes['game_questions'][question_index]['correct_answer'])
    session_attributes['correct_index'] = correct_index

    for answer in possible_answers:
        reprompt_text += f"{possible_answers.index(answer)+1}. {answer}.\n "
    speech_text += reprompt_text
    return speech_text

# --------------------
# Request Handlers (not Intents)
# --------------------
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = f"Welcome to {SKILL_NAME}! This game can be played with one to four players. I will ask each of you {NUMBER_OF_QUESTIONS} questions, try to get as many right as you can. Just respond with the number of your answer. If you need me to repeat anything, say, repeat. Ready? Let\'s begin. What is the first player's name? "
        reprompt_text = "What is the first player's name? "

        session_attributes = {
            'speech_text': speech_text,
            'reprompt_text': reprompt_text,
            'game_state': "PLAYERS"
        }

        handler_input.attributes_manager.session_attributes = session_attributes

        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        print(f"Session ended with reason: {handler_input.request_envelope.request.reason}")
        return handler_input.response_builder.response

# --------------------
# Custom Intents
# --------------------
class NameIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("NameIntent")(handler_input)\
            and handler_input.attributes_manager.session_attributes['game_state'] == "PLAYERS"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        if "players" in session_attributes:
            num_players = len(session_attributes['players'])
        else:
            session_attributes['players'] = []
            num_players = 0

        player_name = handler_input.request_envelope.request.intent.slots['FirstName'].value
        speech_text = f"Got it, {player_name}, you're in. What is the next player's name? "
        reprompt_text = "What is the next player's name? "
        session_attributes['speech_text'] = speech_text
        session_attributes['reprompt_text'] = reprompt_text
        session_attributes['players'].append(player_name)
        num_players += 1

        if num_players == 1:
            speech_text = f"Got it, {player_name}, you're in. What is the next player's name? When all players are entered, say, \"no more players.\""
            session_attributes['speech_text'] = speech_text
        elif num_players == 4:
            speech_text = f"Got it, {player_name}, you're in. You've reached the maximum number of 4 players. Which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
            reprompt_text = "Which category would you like to play? You can also play general trivia. "
            session_attributes['speech_text'] = speech_text
            session_attributes['reprompt_text'] = reprompt_text
            session_attributes["game_state"] = "CATEGORY"
            handler_input.response_builder\
                .speak(speech_text)\
                .ask(reprompt_text)\
                .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
                .set_should_end_session(False)
            return handler_input.response_builder.response

        elif num_players > 4:
            speech_text = "Sorry, something went wrong. Please try again. "
            handler_input.response_builder\
                .speak(speech_text)\
                .ask(session_attributes['reprompt_text'])\
                .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
                .set_should_end_session(False)
            return handler_input.response_builder.response

        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class AnswerIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ( is_intent_name("AnswerIntent")(handler_input) or is_intent_name("DontKnowIntent")(handler_input) )\
            and handler_input.attributes_manager.session_attributes['game_state'] == "STARTED"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        player_index = session_attributes['current_player_index']
        question_index = session_attributes['current_question_index']
        correct_index = session_attributes['correct_index']

        player_guess = None

        if is_intent_name("AnswerIntent")(handler_input):
            player_guess = handler_input.request_envelope.request.intent.slots['Answer'].value

        # Check if player answered correctly, iterate score if so.
        if is_intent_name("DontKnowIntent")(handler_input):
            speech_text = f"The correct answer is {session_attributes['game_questions'][question_index]['correct_answer']}. "
        elif int(player_guess) == (correct_index + 1):
            session_attributes['scores'][player_index] += 1
            speech_text = f"That answer is correct! "
        else:
            speech_text = f"That answer is wrong. The correct answer is {session_attributes['game_questions'][question_index]['correct_answer']}. "

        # Check if we need to go back to the first player
        if player_index == (len(session_attributes['players']) - 1):
            player_index = 0
        else:
            player_index += 1

        # Check end-of-game conditions
        if question_index == (len(session_attributes['game_questions']) - 1):
            winner_index = 0
            winning_score = 0
            for index, score in enumerate(session_attributes['scores']):
                if score > winning_score:
                    winning_score = score
                    winner_index = index
            speech_text += f"The game is now over. The winner is {session_attributes['players'][winner_index]}! Thanks for playing. If you'd like to play again, say, \"open Trivia Party\". "

            handler_input.response_builder\
                .speak(speech_text)\
                .set_card(SimpleCard(SKILL_NAME, speech_text))\
                .set_should_end_session(True)
            return handler_input.response_builder.response
        
        # If game is not over, continue to ask questions
        session_attributes['current_player_index'] = player_index
        session_attributes['current_question_index'] += 1
        speech_text += readQuestionAndShuffledAnswers(handler_input)
        reprompt_text = f"What is your answer? You can also ask me to repeat the question. "
        session_attributes['speech_text'] = speech_text
        session_attributes['reprompt_text'] = reprompt_text
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class PlayersDoneIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("PlayersDone")(handler_input)\
            and handler_input.attributes_manager.session_attributes['game_state'] == "PLAYERS"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        speech_text = ""
        if len(session_attributes['players']) == 1:
            speech_text = f"Okay, we'll play with 1 player. Next, which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
        else:
            speech_text = f"Okay, we'll play with {len(session_attributes['players'])} players. Next, which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
        reprompt_text = "Which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
        session_attributes['speech_text'] = speech_text
        session_attributes['reprompt_text'] = reprompt_text
        
        session_attributes['game_state'] = "CATEGORY"

        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class CategoryIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("CategoryIntent")(handler_input)\
            and handler_input.attributes_manager.session_attributes['game_state'] == "CATEGORY"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes

        # Get category ID from string in the intent's slot
        category_string = handler_input.request_envelope.request.intent.slots['Category'].value
        category_id = getCategoryId(category_string)
        if category_id < 0:
            speech_text = "Sorry, something went wrong. Please choose a valid category. "
            reprompt_text = "Which category would you like to play? You can also play general trivia. "
            session_attributes['reprompt_text'] = reprompt_text
            handler_input.response_builder\
                .speak(speech_text)\
                .ask(reprompt_text)\
                .set_card(SimpleCard(SKILL_NAME, reprompt_text))\
                .set_should_end_session(False)
            return handler_input.response_builder.response
            
        # Save questions and current index to session attributes
        session_attributes['game_questions'] = getGameQuestions(category_id, NUMBER_OF_QUESTIONS*len(session_attributes['players']))
        session_attributes['current_question_index'] = 0
        session_attributes['current_player_index'] = 0
        session_attributes['scores'] = [0, 0, 0, 0]
        session_attributes['game_state'] = "STARTED"

        speech_text = f"Okay, we'll play {category_string} trivia. Let's begin the game! "
        speech_text += readQuestionAndShuffledAnswers(handler_input)
        reprompt_text = f"What is your answer? You can also ask me to repeat the question. "
        session_attributes['speech_text'] = speech_text
        session_attributes['reprompt_text'] = reprompt_text
        
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class GetCategoriesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("GetCategoriesIntent")(handler_input)\
            and handler_input.attributes_manager.session_attributes['game_state'] == "CATEGORY"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        speech_text = f"The available categories are:\n"
        for category in CATEGORIES:
            speech_text += f"{category}\n"
        reprompt_text = "Which category would you like to play? "
        session_attributes['speech_text'] = speech_text
        session_attributes['reprompt_text'] = reprompt_text
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class WhoseTurnIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("WhoseTurnIntent")(handler_input)\
            and handler_input.attributes_manager.session_attributes['game_state'] == "STARTED"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        player_index = session_attributes['current_player_index']
        player_name = session_attributes['players'][player_index]

        speech_text = f"It is currently {player_name}'s turn. "
        speech_text += session_attributes['speech_text']
        reprompt_text = session_attributes['reprompt_text']
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response
# --------------------
# Built-In Intents
# --------------------
class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        reprompt_text = session_attributes['reprompt_text']
        speech_text = f"'I will ask you {NUMBER_OF_QUESTIONS} multiple choice questions. Respond with the number of the answer. For example, say one, two, three, or four. To start a new game at any time, say, new game. If you need to hear something again, say, repeat. "
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, reprompt_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        reprompt_text = session_attributes['reprompt_text']
        speech_text = f"Sorry, I didn't understand that. {reprompt_text}"
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, reprompt_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class RepeatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.RepeatIntent")(handler_input)

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        reprompt_text = session_attributes['reprompt_text']
        speech_text = session_attributes['speech_text']
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes

        # If player wants to stop, end the game.
        if session_attributes['game_state'] == "WANTS_TO_STOP":
            speech_text = "Thank you for playing Trivia Party. If you'd like to play again, say, open \"Trivia Party\". "
            handler_input.response_builder\
                .speak(speech_text)\
                .set_card(SimpleCard(SKILL_NAME, speech_text))\
                .set_should_end_session(True)
            return handler_input.response_builder.response
        
        # Otherwise, "Yes" is not a valid response. Respond similar to a RepeatIntent.
        reprompt_text = session_attributes['reprompt_text']
        speech_text = session_attributes['speech_text']
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes

        # If player wants to stop, change game state back to "STARTED" and repeat the message from prior to StopIntent/CancelIntent
        if session_attributes['game_state'] == "WANTS_TO_STOP":
            session_attributes['game_state'] = "STARTED"
        
        # Otherwise, "No" is not a valid response. Respond similar to a RepeatIntent.
        reprompt_text = session_attributes['reprompt_text']
        speech_text = session_attributes['speech_text']
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class StopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        speech_text = "Would you like to quit playing? "
        reprompt_text = speech_text
        session_attributes['game_state'] = "WANTS_TO_STOP"
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class CancelIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.CancelIntent")(handler_input)

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        speech_text = "Would you like to quit playing? "
        reprompt_text = speech_text
        session_attributes['game_state'] = "WANTS_TO_STOP"
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class UnhandledIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return True

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        reprompt_text = session_attributes['reprompt_text']
        speech_text = f"Sorry, I didn't understand that. {reprompt_text}"
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, reprompt_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(NameIntentHandler())
sb.add_request_handler(AnswerIntentHandler())
sb.add_request_handler(PlayersDoneIntentHandler())
sb.add_request_handler(CategoryIntentHandler())
sb.add_request_handler(GetCategoriesIntentHandler())
sb.add_request_handler(WhoseTurnIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(StopIntentHandler())
sb.add_request_handler(CancelIntentHandler())
sb.add_request_handler(UnhandledIntentHandler())
lambda_handler = sb.lambda_handler()