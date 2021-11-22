import sys
import requests
from requests.sessions import session
from random import shuffle
sys.path.append('./package')

from ask_sdk_core.skill_builder import SkillBuilder
sb = SkillBuilder()

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.attributes_manager import AttributesManager
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

SKILL_NAME = "Trivia Party"
NUMBER_OF_QUESTIONS = 5

def getGameQuestions(category_number, number_questions):
    URL = f"https://opentdb.com/api.php?amount={number_questions}&category={category_number}"
    r = requests.get(url = URL)
    data = r.json()

    return data["results"]

def getCategoryId(category_string):
    if category_string == "general":
        return 9
    elif category_string == "books"
        return 10
    elif category_string == "film"
        return 11
    elif category_string == "music"
        return 12
    elif category_string == "television" or category_string == "TV"
        return 14
    elif category_string == "video games"
        return 15
    elif category_string == "science"
        return 17
    elif category_string == "math"
        return 19
    elif category_string == "history"
        return 23
    elif category_string == "geography"
        return 22
    elif category_string == "animal" or category_string == "animals":
        return 27
    else
        return -1


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = f"Welcome to {SKILL_NAME}! This game can be played with one to four players. I will ask each of you {NUMBER_OF_QUESTIONS} questions, try to get as many right as you can. Just respond with the number of your answer. If you need me to repeat anything, say, repeat. Ready? Let\'s begin. What is the first player's name? "
        reprompt_text = "What is the first player's name? "

        session_attributes = {
            'speech_text': reprompt_text,
            'reprompt_text': reprompt_text,
            'game_state': "PLAYERS",        
            'wants_to_stop': False
        }

        handler_input.attributes_manager.session_attributes = session_attributes

        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

class NameIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("NameIntent")(handler_input)\
            and handler_input.attributes_manager.session_attributes["game_state"] == "PLAYERS"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        if "players" in session_attributes:
            num_players = len(session_attributes["players"])
        else:
            session_attributes["players"] = []
            num_players = 0

        player_name = handler_input.request_envelope.request.intent.slots["FirstName"].value
        speech_text = f"Got it, {player_name}, you're in. What is the next player's name? "
        reprompt_text = "What is the next player's name? "
        session_attributes["players"].append(player_name)
        num_players += 1

        if num_players == 1:
            speech_text = f"Got it, {player_name}, you're in. What is the next player's name? When all players are entered, say, \"no more players.\""
        elif num_players == 4:
            speech_text = f"Got it, {player_name}, you're in. You've reached the maximum number of 4 players. Which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
            reprompt_text = "Which category would you like to play? You can also play general trivia. "
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
                .ask(session_attributes["reprompt_text"])\
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
        return is_intent_name("AnswerIntent")(handler_input)\
            and handler_input.attributes_manager.session_attributes["game_state"] == "STARTED"

    def handle(self, handler_input):
        return

class PlayersDoneIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("PlayersDone")(handler_input)\
            and handler_input.attributes_manager.session_attributes["game_state"] == "PLAYERS"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        speech_text = ""
        if len(session_attributes["players"]) == 1:
            speech_text = f"Okay, we'll play with 1 player. Next, which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
        else:
            speech_text = f"Okay, we'll play with {len(session_attributes['players'])} players. Next, which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
        reprompt_text = "Which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
        
        session_attributes["game_state"] = "CATEGORY"
        session_attributes["speech_text"] = speech_text
        session_attributes["reprompt_text"] = reprompt_text

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
            and handler_input.attributes_manager.session_attributes["game_state"] == "CATEGORY"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes

        # Get category ID from string in the intent's slot
        category_string = handler_input.request_envelope.request.intent.slots["Category"].value
        category_id = getCategoryId(category_string)
        if category_id < 0:
            speech_text = "Sorry, something went wrong. Please choose a valid category. "
            reprompt_text = "Which category would you like to play? You ccan also play general trivia. "
            handler_input.response_builder\
                .speak(speech_text)\
                .ask(reprompt_text)\
                .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
                .set_should_end_session(False)
            return handler_input.response_builder.response
            
        # Save questions and current index to session attributes
        session_attrributes['game_questions'] = getGameQuestions(category_id, NUMBER_OF_QUESTIONS*len(session_attributes["players"])
        session_attributes['current_question_index'] = 0

        speech_text = f"Okay, we'll play {category_string} trivia. Let's begin the game! Question {1}. {session_attrributes['game_questions'][0]["question"]} "
        reprompt_text = f"{session_attrributes['game_questions'][0]["question"]} "

        possible_answers = session_attrributes['game_questions'][0]["incorrect_answers"].append(session_attrributes['game_questions'][0]["correct_answer"])
        shuffled_answers = shuffle(possible_answers)
        correct_index = shuffled_answers.index(session_attrributes['game_questions'][0]["correct_answer"])

        for answer in shuffled_answers:
            reprompt_text += f"{shuffled_answers.index(answer)}. {answer} "
        speech_text += reprompt_text
        
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, reprompt_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(NameIntentHandler())
sb.add_request_handler(AnswerIntentHandler())
sb.add_request_handler(PlayersDoneIntentHandler())
lambda_handler = sb.lambda_handler()