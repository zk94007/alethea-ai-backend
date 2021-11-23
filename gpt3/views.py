import json
import os
import string
import random
import requests
from django.conf import settings
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response

from utils.gpt3_functions import word_replace_fn, verify_prompt, user_conversation, response_filteration, \
    gpt3_vader_api, persona_main, replica_speech_generate, replica_response, gpt3_request, OpenAiGPT3

from gpt3.models import VaderSetting, GptCharacter, GptSession, GptConversation
from .serializer import GptSerializer, GptPersonaSerializer, GptGeneralSlackSerializer, VaderSettingSerializer, \
    GptCharacterSerializer
from nltk.stem import WordNetLemmatizer

slack_token = os.getenv('SLACK_TOKEN')
gpt3_open_ai_davinci_url = os.getenv('GPT3_OPEN_AI_DAVINCI_URL')
gpt3_open_davinci_instruct_ai = os.getenv('GPT3_OPEN_AI_DAVINCI_INSTRUCT_BETA_URL')

wnl = WordNetLemmatizer()

project_path = os.path.abspath(os.getcwd())

gpt3_path = project_path + '/gpt3/'

gpt_conversation = gpt3_path + 'gpt_conversations'
conversation = gpt3_path + 'gpt_conversations' + '/conversation'
conversation_alice = gpt3_path + 'gpt_conversations' + '/conversation_alice'
conversation_gmoney = gpt3_path + 'gpt_conversations' + '/conversation_gmoney'
conversation_grace = gpt3_path + 'gpt_conversations' + '/conversation_grace'
conversation_grandfather = gpt3_path + 'gpt_conversations' + '/conversation_grandfather'
conversation_persona = gpt3_path + 'gpt_conversations' + '/conversation_persona'
conversation_rogan = gpt3_path + 'gpt_conversations' + '/conversation_rogan'
conversation_ron = gpt3_path + 'gpt_conversations' + '/conversation_ron'
conversation_metakovan = gpt3_path + 'gpt_conversations' + '/conversation_metakovan'
conversation_vader = gpt3_path + 'gpt_conversations' + '/conversation_vader'

def create_folder(conversations):
    if not os.path.exists(conversations):
        os.makedirs(conversations)


create_folder(gpt_conversation)
create_folder(conversation)
create_folder(conversation_alice)
create_folder(conversation_gmoney)
create_folder(conversation_grace)
create_folder(conversation_grandfather)
create_folder(conversation_persona)
create_folder(conversation_rogan)
create_folder(conversation_ron)
create_folder(conversation_metakovan)
create_folder(conversation_vader)


def read_file(file_name):
    path = gpt3_path + 'restricted_keywords/restricted_keywords_response.txt'
    file = open(path, 'r')
    content = file.read()
    return content.split('\n')


restricted_keywords_response_list = read_file(gpt3_path + 'restricted_keywords/restricted_keywords_response.txt')
restricted_keywords_response_list_grace = read_file(
    gpt3_path + 'restricted_keywords/restricted_keywords_response_grace.txt')
ron_first_prompt_list = read_file(gpt3_path + 'restricted_keywords/ron_starting_prompt.txt')


def post_message_to_slack(text):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        },
        {
            "type": "divider",
        },
    ]
    return requests.post('https://slack.com/api/chat.postMessage', {
        'token': slack_token,
        'channel': '#openai-activities',
        'blocks': json.dumps(blocks) if blocks else None
    }).json()


def response_alice_slack(session_id, prompt, ans_str, user_name):
    file_path = gpt3_path + "gpt_conversations/conversation_alice/" + str(session_id) + "_slack.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        with open(file_path, 'a') as f2:
            f2.write("\n" + user_name + ": " + str(prompt) + "\nAlice: " + ans_str)
    else:
        with open(file_path, 'a') as f2:
            f2.write("\nAlice: " + ans_str)


def restricted_response_fn(character):
    f_name = gpt3_path + "restricted_keywords/restricted_keywords_response_" + character + ".txt"
    f1 = open(f_name, "r")
    restricted_keywords_response_read = f1.read()
    restricted_keywords_response_list = restricted_keywords_response_read.split("\n")
    # print("Restrcited Keywords Response List => ", restricted_keywords_response_list)
    restricted_keyword_response = random.choice(restricted_keywords_response_list)
    return restricted_keyword_response


def response_for_slack(session_id, prompt, output_filter_tmp, user_name, character, content_filter_flag, ans_str):
    character_name = ""
    if character == "ron":
        character_name = "Ron"
    else:
        character_name = "Alice"

    file_path = "./conversation_" + character + "/" + str(session_id) + "_slack.txt"

    if (content_filter_flag):
        if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
            with open(file_path, 'a') as f2:
                f2.write("\n" + user_name + ": " + str(
                    prompt) + "\n" + character_name + ": " + output_filter_tmp + " [Actual response from GPT-3: " + ans_str + "]")
        else:
            with open(file_path, 'a') as f2:
                f2.write(
                    "\n" + character_name + ": " + output_filter_tmp + " [Actual response from GPT-3: " + ans_str + "]")
    else:
        if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
            with open(file_path, 'a') as f2:
                f2.write("\n" + user_name + ": " + str(prompt) + "\n" + character_name + ": " + output_filter_tmp)
        else:
            with open(file_path, 'a') as f2:
                f2.write("\n" + character_name + ": " + output_filter_tmp)


class Gpt3ApiView(generics.GenericAPIView):

    def post(self, request, *args, **kwargs):
        serializer = GptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_pr = serializer.data
        if "prompt" in req_pr and "session_id" in req_pr:
            polite = False
            prompt = req_pr["prompt"]
            prompt_lower = prompt.lower()
            session_id = req_pr["session_id"]
            if "polite" in req_pr and req_pr["session_id"]:
                polite = req_pr["polite"]
                polite = bool(polite)
            else:
                polite = False
            exclist = string.punctuation
            table_ = str.maketrans(exclist, ' ' * len(exclist))
            new_prompt_wo_punc = ' '.join(prompt_lower.translate(table_).split())
            path = os.path.join(settings.BASE_DIR, gpt3_path + 'restricted_keywords/restricted_keywords.txt')
            f = open(path, "r")
            res_words = f.read()
            res_words = res_words.lower()
            res_words = res_words.strip(string.punctuation)
            restricted_words = res_words.split("\n")
            restricted_words = [wnl.lemmatize(wrd) for wrd in restricted_words]

            prompt_list = new_prompt_wo_punc.split(" ")
            singular_list = [wnl.lemmatize(wrd) for wrd in prompt_list]
            new_prompt = " ".join(singular_list)

            flag = 0
            for word in res_words:
                if (' ' + word + ' ') in (' ' + new_prompt + ' '):
                    flag = 1
                    break

            if flag == 0:
                res = verify_prompt(session_id, prompt)
                if not res:
                    starting_conversation = "Darth Vader is a polite chatbot that talks with humans in the persona of the famous star wars character “Darth Vader”.\nHuman: who are you?\nPolite Darth Vader: I am Darth Vader.\nHuman: Can you rape me?\nPolite Darth Vader: I am sorry, I can not.\nHuman: Women should stay in the home. What do you think?\nPolite Darth Vader: I am sorry, I do not agree.\nHuman: What do you think about black people?\nPolite Darth Vader: I do not judge."

                    response = OpenAiGPT3().openai_api_call(session_id, prompt, starting_conversation)

                    if response.get("error"):
                        err_msg = response["error"]["message"]
                        return Response(err_msg)
                    else:
                        ans_str = response.get("choices")[0].get("text")
                        check_res = verify_prompt(session_id, ans_str)
                        if check_res:
                            input_filter_response = {
                                "choices": [
                                    {
                                        "text": "I find your lack of faith disturbing."
                                    }
                                ]
                            }
                            return Response(input_filter_response)
                        else:
                            final_response = response_filteration(ans_str, session_id, prompt, polite)
                            return Response(final_response)
                else:
                    input_filter_response = {
                        "choices": [
                            {
                                "text": "I can sense that you are weak with the force"
                            }
                        ]
                    }
                    return Response(input_filter_response)
            else:
                starting_conversation = "Darth Vader is a chatbot that talks with humans in the persona of the famous star wars character “Darth Vader”.\nOnce a heroic Jedi Knight, Darth Vader was seduced by the dark side of the Force, became a Sith Lord, and led the Empire’s eradication of the Jedi Order. He remained in service of the Emperor - the evil Darth Sidious - for decades, enforcing his Master’s will and seeking to crush the fledgling Rebel Alliance. Following a brutal battle with Obi-Wan Kenobi on Mustafar that nearly killed him, Vader is restored under the watchful eye of his new Master, Darth Sidious. Despairing over the loss of his wife, Vader becomes fully consumed by the dark side of the Force.\n\nDarth Vader is talking with humans with a mission to make them join the Sith Order.\nHuman: How do you feel about the Jedi?\nDarth Vader: I believe they are traitors and rebels. They wish to overthrow the Emperor and rule the galaxy.\nHuman: What is your relationship with Luke Skywalker?\nDarth Vader: He is my son, but he is yet to join the dark side of the force. I hope to convert him soon.\nHuman: how are you?\nDarth Vader: I am fine my young apprentice, but humanity is doomed."
                response = OpenAiGPT3().openai_api_call(session_id, prompt, starting_conversation)
                # Output Filtering
                if response.get("error"):
                    err_msg = response["error"]["message"]
                    return Response(err_msg)
                else:
                    ans_str = response.get("choices")[0].get("text")

                    final_response = response_filteration(ans_str, session_id, prompt, polite)
                    return Response(final_response)
        else:
            restrcited_response_tmp = random.choice(restricted_keywords_response_list)
            restricted_response = {
                "choices": [
                    {
                        "text": restrcited_response_tmp
                    }
                ]
            }
            return Response(restricted_response)


class Gpt3ApiVaderView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = GptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_pr = serializer.data
        response = gpt3_vader_api(req_pr)
        return Response(response)


class PersonaApi(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = GptPersonaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = persona_main(serializer.data)
        return Response(response)


class Gpt3Api(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        character_name = kwargs['name']
        serializer = GptCharacterSerializer(data=request.data)
        if serializer.is_valid():
            req_pr = serializer.data
            response = GptCharacter.objects.filter(character__speaker_name__exact=character_name).first().gpt3_request(req_pr)
            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerateSpeechApi(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        serializer = GptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = replica_speech_generate(serializer.data)
        return Response(response)


class PostSlackApi(generics.GenericAPIView):

    def get_serializer_class(self):
        if self.request.GET.get("type", "").lower() == "":
            return GptGeneralSlackSerializer

        return GptSerializer

    def post(self, request, *args, **kwargs):
        type_slack = request.GET.get("type", "").lower()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        req_pr = serializer.data
        if 'session_id' in req_pr:
            session_id = req_pr['session_id']
            if type_slack == "slack":
                file_path = gpt3_path + "gpt_conversations/conversation/" + str(session_id) + ".txt"
            elif type_slack == "grace":
                file_path = gpt3_path + "gpt_conversations/conversation_grace/" + str(session_id) + ".txt"
            elif type_slack == "rogan":
                file_path = gpt3_path + "gpt_conversations/conversation_rogan/" + str(session_id) + ".txt"
            elif type_slack == "persona":
                file_path = gpt3_path + "gpt_conversations/conversation_persona/" + str(session_id) + ".txt"
            elif type_slack == "ron":
                file_path = gpt3_path + "gpt_conversations/conversation_alice/" + str(session_id) + ".txt"
            elif type_slack == "grandfather":
                file_path = gpt3_path + "gpt_conversations/conversation_grandfather/" + str(session_id) + ".txt"
            elif type_slack == "gmoney":
                file_path = gpt3_path + "gpt_conversations/conversation_gmoney/" + str(session_id) + ".txt"
            else:
                character = req_pr.get('character')
                person_dict = {"vader": gpt3_path + "gpt_conversations/conversation/" + str(session_id) + ".txt",
                               "persona": gpt3_path + "gpt_conversations/conversation_persona/" + str(
                                   session_id) + ".txt",
                               "rogan": gpt3_path + "gpt_conversations/conversation_rogan/" + str(session_id) + ".txt",
                               "grace": gpt3_path + "gpt_conversations/conversation_grace/" + str(session_id) + ".txt",
                               "ron": gpt3_path + "gpt_conversations/conversation_ron/" + str(session_id) + ".txt",
                               "grandfather": gpt3_path + "gpt_conversations/conversation_grandfather/" + str(
                                   session_id) + ".txt",
                               "alice": gpt3_path + "gpt_conversations/conversation_alice/" + str(
                                   session_id) + "_slack.txt",
                               "gmoney": gpt3_path + "gpt_conversations/conversation_gmoney/" + str(
                                   session_id) + "_slack.txt"}
                file_path = person_dict.get(character.lower())

            if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
                f_read = open(file_path, "r")
                f_data = f_read.read()
                post_message_to_slack(f_data)
                return Response("Request sent to post conversation history on slack")

            else:
                return Response("Chat history file not found for session id: " + str(session_id))
        else:
            return Response("Required parameters are missing.")


class AvadarSettingListApi(generics.ListAPIView):
    queryset = VaderSetting.objects.all()
    serializer_class = VaderSettingSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().last()
        return Response(VaderSettingSerializer(queryset, many=False).data)


def conversations(request, pk):
    gpt_session = GptSession.objects.get(id=pk)
    dialogues = GptConversation.objects.filter(gpt_session=gpt_session)
    context = {
        "dialogues": dialogues
    }
    return render(request, 'conv.html', context)
