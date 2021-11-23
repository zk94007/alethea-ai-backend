import random
import string
import requests
import json

from users.models import User
from django.db import models
from rest_framework.response import Response
from django.contrib.postgres.fields import JSONField

from modules.models import TimeStampModel
from utils.gpt3_functions import create_folder, clean_restrictedfile, response_for_slack, \
    replica_response, wnl, word_replace_fn, restricted_response_fn
import os

gpt3_key = os.getenv('GPT3_KEY')
gpt3_key_ron_alice = os.getenv("GPT3_KEY_RON_ALICE")
gpt3_open_davinci_instruct_ai = os.getenv('GPT3_OPEN_AI_DAVINCI_INSTRUCT_BETA_URL')
gpt3_open_ai_filter_alpha_url = os.getenv('GPT3_OPEN_AI_FILTER_ALPHA_URL')

project_path = os.path.abspath(os.getcwd())

gpt3_path = project_path + '/gpt3/'

constants = gpt3_path + 'constants'


def create_folder(constant):
    if not os.path.exists(constant):
        os.makedirs(constant)


create_folder(constants)


class VaderSetting(TimeStampModel):
    inactivity_time_out = models.PositiveIntegerField(default=0)
    end_interaction = models.PositiveIntegerField(default=0)


class Speakers(TimeStampModel):
    speaker_name = models.CharField(max_length=50)
    speaker_tts_code = models.CharField(max_length=255, help_text="This should be matched with tts speaker.", unique=True)

    def __str__(self):
        return f"{self.speaker_name}"

    class Meta:
        verbose_name_plural = "Speakers"


class GptCharacter(TimeStampModel):
    character = models.ForeignKey(Speakers, on_delete=models.CASCADE, related_name="speaker", limit_choices_to={"is_active": True})
    gpt_key = models.CharField(max_length=100)
    prompt = models.TextField()
    restricted_keywords = models.TextField()
    constants = JSONField()
    strip = models.BooleanField(default=False)
    check_reponse = models.BooleanField(default=False)
    strip_one = models.BooleanField(default=False, verbose_name="answer strip from one ")
    temperature = models.FloatField()
    max_tokens = models.IntegerField()
    top_p = models.IntegerField()
    presence_penalty = models.FloatField()
    frequency_penalty = models.FloatField()
    stop_username = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Gpt Character"

    def __str__(self):
        return self.character.speaker_name

    def gpt_prompt_file_path(self, file_name):
        file_path = project_path + '/gpt3/character_conversation/' + file_name
        return file_path

    def gpt_conversation_folder_path(self, folder_name):
        folder_path = project_path + '/gpt3/gpt_conversations/' + folder_name
        return folder_path

    def gpt_restricted_file_path(self, file_name):
        file_path = project_path + '/gpt3/restricted_keywords/' + file_name
        return file_path

    def gpt_constant_file_path(self, file_name):
        file_path = project_path + '/gpt3/constants/' + file_name
        return file_path

    def openai_header(self):
        header = {'Authorization': 'Bearer ' + self.gpt_key, 'Content-Type': 'application/json'}
        return header

    def verify_prompt(self, session_id, text):
        text_str = text
        headers = self.openai_header()
        message_2 = {"user": str(session_id), "prompt": "" + text_str + "\n--\nLabel:", "temperature": 0,
                     "max_tokens": 1, "top_p": 0}
        response2 = requests.post(gpt3_open_ai_filter_alpha_url, headers=headers, data=json.dumps(message_2))
        response2 = response2.json()
        if response2.get("error"):
            err_msg = response2["error"]["message"]
            return err_msg
        else:
            ans_str2 = response2.get("choices")[0].get("text")
            if ans_str2 == "2":
                return True
            else:
                return False

    def stop(self, username):
        if self.stop_username:
            return ["\n" + self.stop_username + ":", "\n" + self.stop_username.lower() + ":"]
        else:
            return ["\n" + username + ":", "\n" + username.lower() + ":"]

    def openai_request(self, prompt, user_name, session_id):
        my_request = {
            "user": str(session_id),
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
            "stop": self.stop(user_name)
        }

        return my_request

    def user_conversation_openai(self, session_id, prompt, starting_conversation, user_name, user_id, polite):
        file_path = f"{gpt3_path}gpt_conversations/conversation_{self.character.speaker_tts_code}/{session_id}.txt"

        if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
            f_read = open(file_path, "r")
            f_data = f_read.read()
            # print("File_Data => ",f_data)
            print("Prompt => ", prompt)
            print("User_name => ", user_name)
            new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)
            new_prompt = new_prompt + f"\n{self.character.speaker_name}:"
            print("========================== Alice - New Prompt With History==================")
            print("New Prompt With History ==> ", new_prompt)
            response = self.openai_request(new_prompt, user_name, session_id)
            return response
        else:
            new_prompt = starting_conversation + f"\n{self.character.speaker_name}:"
            print("========================== New Prompt ==================")
            print("New Prompt ==> ", new_prompt)
            response = self.openai_request(new_prompt, user_name, session_id)
            return response

    def openai_api(self, session_id, prompt, starting_conversation, user_name, user_id, polite):
        my_request = self.user_conversation_openai(session_id, prompt, starting_conversation, user_name, user_id,
                                                   polite)
        headers = self.openai_header()

        response = requests.post(gpt3_open_davinci_instruct_ai, headers=headers, data=json.dumps(my_request))

        response = response.json()
        return response

    def response_filteration(self, character_name, ans_str, session_id, prompt, user_name, user_id, polite,
                                     ans_str_one, strip_ans, check_response, logged_user_id):
        # ans_str = " ".join(words_replace.get(ele, ele) for ele in ans_str.split())

        if "\n" in ans_str:
            ans_str = ans_str.split("\n")
            if ans_str_one:
                ans_str = ans_str[1]  # for gmoney
            else:
                ans_str = ans_str[0]
        print(" Original => ans_str after splitting with with new line ===>", ans_str)

        ans_str = ans_str.replace(f"\n{character_name.title()}: ", "").replace(f"\n{character_name.title()}:",
                                                                               "").replace(
            f"{character_name.title()}: ",
            "").replace(
            f"{character_name.title()}:", "").replace(f"\n{character_name.lower()}: ", "").replace(
            f"\n{character_name.lower()}:", "").replace(f"{character_name.lower()}: ",
                                                        "").replace(
            f"{character_name.lower()}:", "")

        ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                             "\n").replace(
            " Human: ", "\n").replace(" Human: ", "\n")

        if "\n" in ans_str:
            ans_str = ans_str.split("\n")
            ans_str = ans_str[0]
        if strip_ans:
            if not ans_str.strip():
                restrcited_response_tmp = restricted_response_fn('gmoney')
                ans_str = restrcited_response_tmp
        else:
            if ans_str == "" or ans_str == " ":
                restricted_response_tmp = restricted_response_fn(self.character.speaker_tts_code)
                ans_str = restricted_response_tmp

        raw_text = ans_str
        if check_response:
            check_res = self.verify_prompt(session_id, ans_str)
            print("Chek_res outcome => ", check_res)  # alice

            # if Output is labeled 2 by OpenAI Content Filter
            if check_res == True:
                print("GPT3 Content Filteration Called")
                content_filter_flag = True
                output_filter_tmp = restricted_response_fn('alice')
                response_for_slack(session_id, prompt, output_filter_tmp, user_name, self.character.speaker_tts_code,
                                   content_filter_flag,
                                   ans_str)
                output_filter_response = {
                    "choices": [
                        {
                            "text": output_filter_tmp,
                            "raw_text": output_filter_tmp
                        }
                    ]
                }
                print("Output Filter Response => ", output_filter_response)
                # if(alice_type == "txt"):
                #     return output_filter_response
                return output_filter_response  # alice

        res = self.character

        print("res=========", res)

        file_path = f"{gpt3_path}gpt_conversations/conversation_{self.character.speaker_tts_code}/{session_id}.txt"
        file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_{self.character.speaker_tts_code}/{session_id}.txt"
        file_path_slack = f"{gpt3_path}gpt_conversations/conversation_{self.character.speaker_tts_code}/{session_id}_slack.txt"

        logged_user = User.objects.get(id=logged_user_id)
        gpt3_session_object = GptSession.objects.filter(session=session_id)
        if len(gpt3_session_object):
            session_object = gpt3_session_object[0]
        else:
            session_object = GptSession.objects.create(session=session_id, user=logged_user, gpt_character=self)
        user_dialogue = user_name + ": " + str(prompt)
        character_dialogue = f"{self.character.speaker_name}: " + ans_str
        GptConversation.objects.create(character_dialogue=character_dialogue, user_dialogue=user_dialogue,
                                       gpt_session=session_object)

        if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
            print(" <= Session File Exists => ")
            if (os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0):
                with open(file_path_user_id, 'a') as f6:
                    f6.write("\n" + user_name + ": " + str(prompt) + f"\n{self.character.speaker_name}: " + ans_str)
            else:
                with open(file_path_user_id, 'a') as f6:
                    f6.write(f"\n{self.character.speaker_name}: " + ans_str)
        else:
            print("<= Session file doen't exists => ")
            with open(file_path_user_id, 'a') as f6:
                f6.write(f"\n\n{self.character.speaker_name}: " + ans_str)

        if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
            with open(file_path, 'a') as f2:
                f2.write("\n" + user_name + ": " + str(prompt) + f"\n{self.character.speaker_name}: " + ans_str)
        else:
            with open(file_path, 'a') as f2:
                f2.write(f"\n{self.character.speaker_name}: " + ans_str)

        # Save conversation for slack
        if (os.path.exists(file_path_slack) and os.stat(file_path_slack).st_size != 0):
            with open(file_path_slack, 'a') as f2:
                f2.write("\n" + user_name + ": " + str(prompt) + f"\n{self.character.speaker_name}: " + ans_str)
        else:
            with open(file_path_slack, 'a') as f2:
                f2.write(f"\n{self.character.speaker_name}: " + ans_str)

        path = f'{gpt3_path}constants/words_replace_{self.character.speaker_tts_code}.json'
        # path = self.constants
        ans_str = word_replace_fn(path, ans_str)
        if ans_str_one:
            ans_str = ans_str.strip()  ## only strip after word replace in alice and gmoney
        else:
            ans_str = ans_str.lower()
            ans_str = ans_str.replace('.', ' .').replace('?', ' ?').replace(',', ' ,').replace('!', ' !').replace(':',
                                                                                                                  ' :')
            ans_str = ans_str.strip()

        # raw_text = raw_text.lower()
        final_response = {
            "choices": [
                {
                    "text": ans_str,
                    "raw_text": raw_text
                }
            ]
        }

        return final_response

    def restricted_response_fn(self, character):
        f_name = clean_restrictedfile(self.restricted_keywords)
        f1 = open(f_name, "r")
        restricted_keywords_response_read = clean_restrictedfile(self.restricted_keywords)
        restricted_keywords_response_list = restricted_keywords_response_read.split("\n")
        # print("Restrcited Keywords Response List => ", restricted_keywords_response_list)
        restricted_keyword_response = random.choice(restricted_keywords_response_list)
        return restricted_keyword_response

    def gpt3_request(self, req_pr):
        polite = False
        character_type = {}
        character_type.update({"character_name": self.character.speaker_name, "character": self.character.speaker_tts_code, "strip": self.strip,
                               "check_response": self.check_reponse, "strip_one": self.strip_one})
        type_character = character_type['character']
        character_name = character_type['character_name']
        prompt = req_pr['prompt']
        prompt = prompt.strip()
        prompt_lower = prompt.lower()
        session_id = req_pr['session_id']
        user_name = req_pr['user_name']
        user_id = req_pr['user_id']
        character = character_type['character']
        logged_user_id = req_pr['logged_user_id']
        alice_type = req_pr['type']
        strip = character_type['strip']
        check_response = character_type['check_response']
        strip_one = character_type['strip_one']
        character_conversation = ""
        # Check if user already exists or not
        user_flag = 0
        file_list = os.listdir(f"{gpt3_path}gpt_conversations/conversation_{type_character}")
        for filename in file_list:
            file_temp = filename.replace(".txt", "")
            if file_temp == user_id:
                user_flag = 1
                break

        file_path_user = f"{gpt3_path}gpt_conversations/conversation_{type_character}/{user_id}_session.txt"
        if user_flag == 0:
            final_user_flag = 0
            with open(file_path_user, 'w') as f7:
                f7.write(str(session_id) + "\nFirst")
        else:
            f8 = open(f"{gpt3_path}gpt_conversations/conversation_{type_character}/{user_id}_session.txt", "r")
            f_session_id = f8.read()
            session_id_list = f_session_id.split("\n")
            if session_id == session_id_list[0]:
                if len(session_id_list) == 2:
                    final_user_flag = 0
                else:
                    final_user_flag = 1
            else:
                final_user_flag = 1
                with open(file_path_user, 'w') as f9:
                    f9.write(str(session_id))

        if 'polite' in req_pr and req_pr['polite']:
            polite = req_pr['polite']
            polite = bool(polite)
        else:
            polite = False

        punctuation = "!\"#$%&'()+,-./:;<=>?@[\]^_`{|}~"
        exclist = string.punctuation
        table_ = str.maketrans(exclist, ' ' * len(exclist))
        new_prompt_wo_punc = ' '.join(prompt_lower.translate(table_).split())
        f = open(f'{gpt3_path}restricted_keywords/restricted_keywords.txt', "r")
        res_words = f.read()
        res_words = res_words.lower()
        res_words = res_words.strip(punctuation)
        restricted_words = res_words.split("\n")
        restricted_words = [wnl.lemmatize(wrd) for wrd in restricted_words]

        # Convert prompt to singular form
        prompt_list = new_prompt_wo_punc.split(" ")
        singular_list = [wnl.lemmatize(wrd) for wrd in prompt_list]
        new_prompt = " ".join(singular_list)

        flag = 0
        for word in restricted_words:
            if (' ' + word + ' ') in (' ' + new_prompt + ' '):
                flag = 1
                break
        # path = f'{gpt3_path}character_conversation/{type_character}.txt'
        # f = open(path, "r")
        # character_conversation = f.read()
        character_conversation = clean_restrictedfile(self.prompt)
        character_conversation = character_conversation.replace('__user_name__', user_name)

        if flag == 0:
            if polite:
                res = self.verify_prompt(session_id, prompt)
                if not res:
                    starting_conversation = ""
                    if final_user_flag == 0:
                        starting_conversation = character_conversation
                    else:
                        starting_conversation = character_conversation

                    response = self.openai_api(session_id, prompt, starting_conversation, user_name, user_id, polite)

                    # Output Filtering
                    if response.get("error"):
                        err_msg = response["error"]["message"]
                        return Response(err_msg)
                    else:
                        ans_str = response.get("choices")[0].get("text")

                        check_res = self.verify_prompt(session_id, ans_str)
                        if check_res:
                            input_filter_response = {
                                "choices": [
                                    {
                                        "text": "I find your lack of faith disturbing.",
                                        "raw_text": "I find your lack of faith disturbing."
                                    }
                                ]
                            }
                            return Response(input_filter_response)
                        else:
                            final_response = self.response_filteration(character_name, ans_str, session_id,
                                                                               prompt, user_name,
                                                                               user_id, polite,
                                                                               strip_one, strip, req_pr, logged_user_id)

                            return Response(final_response)
                else:
                    # Standard Dialogue if Input is labeled 2 by OpenAI Content Filter:
                    input_filter_response = {
                        "choices": [
                            {
                                "text": "I can sense that you are weak with the force",
                                "raw_text": "I find your lack of faith disturbing."
                            }
                        ]
                    }
                    return Response(input_filter_response)
            else:
                if prompt == "" or prompt.endswith(('.', '!', '?')):
                    prompt = prompt
                else:
                    prompt = prompt + "."

                starting_conversation = ""

                if final_user_flag == 0:
                    # New User
                    starting_conversation = character_conversation
                else:
                    # Returning User
                    starting_conversation = character_conversation

                response = self.openai_api(session_id, prompt, starting_conversation, user_name, user_id, polite)
                print("response", response)
                # Output Filtering
                if response.get("error"):
                    err_msg = response["error"]["message"]
                    return Response(err_msg)
                else:
                    ans_str = response.get("choices")[0].get("text").strip()
                    final_response = self.response_filteration(character_name, ans_str, session_id, prompt,
                                                                       user_name,
                                                                       user_id, polite,
                                                                       strip_one, strip, req_pr, logged_user_id)
                    return Response(final_response)
        else:
            print("Standard Dialogue if restricted word from the list(restricted_files) is detected:")
            restrcited_response_tmp = self.restricted_response_fn(self.character.speaker_name)
            content_filter_flag = False
            ans_str = ""
            response_for_slack(session_id, prompt, restrcited_response_tmp, user_name, character,
                               content_filter_flag, ans_str)
            restricted_response = {
                "choices": [
                    {
                        "text": restrcited_response_tmp,
                        "raw_text": restrcited_response_tmp
                    }
                ]
            }
            return Response(restricted_response)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(GptCharacter, self).save(force_insert=force_insert, force_update=force_update,
                                       using=using, update_fields=update_fields)
        # conversations = self.gpt_conversation_folder_path(f'conversation_{self.character.speaker_name}')
        # create_folder(conversations)
        # prompt_file = open(self.gpt_prompt_file_path(f'{self.character.speaker_name}.txt'), "w")
        # create_prompt_file = clean_restrictedfile(self.prompt)
        # prompt_file.write(create_prompt_file)
        # prompt_file.close()

        constant_file = open(self.gpt_constant_file_path(f'words_replace_{self.character.speaker_tts_code}.json'), "w")
        # create_constant_file = clean_restrictedfile(self.constants)
        constant_file.write(json.dumps(self.constants))
        constant_file.close()

        # restricted_file = open(
        #     self.gpt_restricted_file_path(f'restricted_keywords_response_{self.character.speaker_tts_code}.txt'), "w")
        # create_restricted_file = clean_restrictedfile(self.restricted_keywords)
        # restricted_file.write(create_restricted_file)
        # restricted_file.close()


class GptSession(TimeStampModel):
    session = models.CharField(max_length=20)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    gpt_character = models.ForeignKey(GptCharacter, on_delete=models.CASCADE)

    def __str__(self):
        return self.session


class GptConversation(TimeStampModel):
    user_dialogue = models.TextField()
    character_dialogue = models.TextField()
    gpt_session = models.ForeignKey(GptSession, on_delete=models.CASCADE)
