import sys
import requests
sys.path.append('./package')

from ask_sdk_core.skill_builder import SkillBuilder
sb = SkillBuilder()

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speech_text = "Welcome to Trivia Party! We'll start with 10 questions."

        URL = "https://opentdb.com/api.php?amount=10"
        r = requests.get(url = URL)
        data = r.json()

        speech_text = data["results"][0]["question"]

        sessionAttributes = {}
        sessionAttributes["questions"] = 25

        handler_input.response_builder\
            .speak(speech_text)\
            .set_card(SimpleCard("Hello World", speech_text))\
            .set_should_end_session(False)
        return handler_input.response_builder.response

        
sb.add_request_handler(LaunchRequestHandler())
lambda_handler = sb.lambda_handler()