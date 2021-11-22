import sys
import requests
from requests.sessions import session
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

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = f"Welcome to {SKILL_NAME}! This game can be played with one to four players. I will ask each of you {NUMBER_OF_QUESTIONS} questions, try to get as many right as you can. Just respond with the number of your answer. If you need me to repeat anything, say, repeat. Ready? Let\'s begin. "
        reprompt_text = "What is the first player's name? "

        URL = "https://opentdb.com/api.php?amount=10"
        r = requests.get(url = URL)
        data = r.json()

        speech_text = data["results"][0]["question"]

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

class NameRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("NameIntent")\
            and handler_input.attributes_manager.session_attributes["game_state"] == "PLAYERS"

    def handle(self, handler_input):
        session_attributes = handler_input.attributes_manager.session_attributes
        if "players" in session_attributes:
            num_players = len(session_attributes["players"])
        else:
            session_attributes["players"] = []
            num_players = 0

        player_name = handler_input.request_envelope.request.intent.slots["FirstName"].value
        reprompt_text = "What is the next player's name? "
        if num_players == 0:
            reprompt_text = "What is the next player's name?  Whenever all players are in, say, \"No more players\"."

        elif num_players == 3:
            session_attributes["players"].append(player_name)
            speech_text = f"Got it, {player_name}, you're in. You've reached the maximum number of 4 players. Which category would you like to play? If you'd like a list of the categories, say, \"list categories\". You can also play general trivia. "
            reprompt_text = "Which category would you like to play? You can also play general trivia. "
            session_attributes["game_state"] = "CATEGORY"
            handler_input.response_builder\
                .speak(speech_text)\
                .ask(reprompt_text)\
                .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
                .set_should_end_session(False)
            return handler_input.response_builder.response

        elif num_players == 4:
            speech_text = "Sorry, something went wrong. Please try again. "
            handler_input.response_builder\
                .speak(speech_text)\
                .ask(session_attributes["reprompt_text"])\
                .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
                .set_should_end_session(False)
            return handler_input.response_builder.response
        
        else:
            session_attributes["players"].append(player_name)
            speech_text = f"Got it, {player_name}, you're in. "
        
        handler_input.response_builder\
            .speak(speech_text)\
            .ask(reprompt_text)\
            .set_card(SimpleCard(SKILL_NAME, speech_text+reprompt_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(NameRequestHandler())
lambda_handler = sb.lambda_handler()