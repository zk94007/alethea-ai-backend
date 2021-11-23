import random
from server import settings
import uuid
import os
import re
import requests
import json
import string
from nltk.stem import WordNetLemmatizer
from google.cloud import texttospeech
from rest_framework.response import Response

gpt3_key = os.getenv('GPT3_KEY')
gpt3_key_ron_alice = os.getenv("GPT3_KEY_RON_ALICE")
replica_studios_auth = os.getenv('REPLICA_STUDIOS_AUTH')
replica_studios_speech = os.getenv('REPLICA_STUDIOS_SPEECH')
gpt3_open_ai_davinci_url = os.getenv('GPT3_OPEN_AI_DAVINCI_URL')
gpt3_open_ai_filter_alpha_url = os.getenv('GPT3_OPEN_AI_FILTER_ALPHA_URL')
gpt3_open_davinci_instruct_ai = os.getenv('GPT3_OPEN_AI_DAVINCI_INSTRUCT_BETA_URL')
alethea_synth_meta = os.getenv('ALETHEA_SYNTH_META')
MAX_INTERACTIONS = 7
replica_token = ""
refresh_token = ""

project_path = os.path.abspath(os.getcwd())

gpt3_path = project_path + '/gpt3/'

HOSTNAME = os.getenv('HOSTNAME')

path_1 = os.path.join(settings.BASE_DIR, 'gpt3/constants/google_tts.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path_1


def read_file(file_name):
    path = f'{gpt3_path}restricted_keywords/restricted_keywords_response.txt'
    file = open(path, 'r')
    content = file.read()
    return content.split('\n')


restricted_keywords_response_list = read_file(f'{gpt3_path}restricted_keywords/restricted_keywords_response.txt')
restricted_keywords_response_list_grace = read_file(f'{gpt3_path}restricted_keywords/restricted_keywords_response_grace.txt')
ron_first_prompt_list = read_file(f'{gpt3_path}restricted_keywords/ron_starting_prompt.txt')

client = texttospeech.TextToSpeechClient()
voice = texttospeech.VoiceSelectionParams(
    language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16
)

wnl = WordNetLemmatizer()

basedir = os.path.dirname(os.path.realpath(__file__))
thread = None

path_1 = os.path.join(settings.BASE_DIR, 'gpt3/restricted_keywords/restricted_keywords_response.txt')
f1 = open(path_1, "r")
restricted_keywords_response_read = f1.read()
restricted_keywords_response_list = restricted_keywords_response_read.split("\n")

path_2 = os.path.join(settings.BASE_DIR, 'gpt3/restricted_keywords/restricted_keywords_response_grace.txt')
f_grace = open(path_2, "r")
restricted_keywords_response_read_grace = f_grace.read()
restricted_keywords_response_list_grace = restricted_keywords_response_read_grace.split("\n")


def create_folder(conversation):
    if not os.path.exists(conversation):
        os.makedirs(conversation)


def restricted_response_fn(character):
    f_name = f"{gpt3_path}restricted_keywords/restricted_keywords_response_{character}.txt"
    f1 = open(f_name, "r")
    restricted_keywords_response_read = f1.read()
    restricted_keywords_response_list = restricted_keywords_response_read.split("\n")
    # print("Restrcited Keywords Response List => ", restricted_keywords_response_list)
    restricted_keyword_response = random.choice(restricted_keywords_response_list)
    return restricted_keyword_response


def clean_restrictedfile(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def word_replace_fn(json_filename, ans_str):
    ans_str = ans_str.replace("’", "'").replace("‘", "'").replace('“', '"').replace('”', '"')

    punct_list = [',', '.', '!', "?", ':', ';', '-', '+', '(', ')', '*', '&', '^', '%', '$', '#', '@', '~', '`',
                  '/',
                  '|', '{', '}', '[', ']']

    with open(json_filename) as f:
        words_replace = json.load(f)

    # convert dict to lower case
    new_words_replace = {}
    for key, value in words_replace.items():
        new_words_replace[key.lower()] = value.lower()

    new_words_key = new_words_replace.keys()
    replaced_str = ""

    ans_str = ans_str.strip()
    splitted_str = ans_str.split(" ")

    for s in splitted_str:
        f_char = ""
        l_char = ""

        # check start or end with punctuation
        if s[0] in punct_list:
            f_char = s[0]
            s = s[1:]
        elif s[-1] in punct_list:
            l_char = s[-1]
            s = s[:-1]

        if s.lower() in new_words_key:
            word = new_words_replace.get(s.lower())
            replaced_str += f_char + word + l_char + " "
        else:
            replaced_str += f_char + s + l_char + " "

    return replaced_str


def get_replica_token():
    data = {"client_id": os.getenv('REPLICA_USERNAME'), "secret": os.getenv('REPLICA_PASSWORD')}
    response = requests.post(replica_studios_auth, data=data).json()
    global replica_token, refresh_token
    replica_token, refresh_token = response.get("access_token"), response.get("refresh_token")


def verify_prompt(session_id, text):
    text_str = text
    headers = {'Authorization': 'Bearer ' + gpt3_key_ron_alice,
               'Content-Type': 'application/json'}
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


def response_for_slack(session_id, prompt, output_filter_tmp, user_name, character, content_filter_flag, ans_str):
    character_name = ""
    if character == "ron":
        character_name = "Ron"
    else:
        character_name = "Alice"

    file_path = "gpt3/gpt_conversations/conversation_" + character + "/" + str(session_id) + "_slack.txt"

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


def user_conversation(session_id, prompt, starting_conversation):
    file_path = "gpt3/gpt_conversations/conversation/" + str(session_id) + ".txt"

    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        f_read = open(file_path, "r")
        f_data = f_read.read()
        new_prompt = starting_conversation + str(f_data) + "\nHuman: " + str(prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.75,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.45,
            "frequency_penalty": 0.45,
            "stop": ["\nHuman:", "\nhuman:"]
        }

        return my_request
    else:
        new_prompt = starting_conversation + "\nHuman: " + str(prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.75,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.45,
            "frequency_penalty": 0.45,
            "stop": ["\nHuman:", "\nhuman:"]
        }

        return my_request


def user_conversation_vader(session_id, prompt, starting_conversation, user_name, user_id, polite):
    file_path = "gpt3/gpt_conversations/conversation/" + str(session_id) + ".txt"
    user_name_lower = user_name.lower()
    file_path_user_id = "gpt3/gpt_conversations/conversation/" + str(user_id) + ".txt"

    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        f_read = open(file_path, "r")
        f_data = f_read.read()

        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        if not polite:
            new_prompt = new_prompt + "\nDarth Vader:"
        else:
            new_prompt = new_prompt + "\nPolite Darth Vader:"
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:
        if not polite:
            new_prompt = starting_conversation + "\nDarth Vader:"
        else:
            new_prompt = starting_conversation + "\nPolite Darth Vader:"
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def openai_api_call_vader(session_id, prompt, starting_conversation, user_name, user_id, polite):
    my_request = user_conversation_vader(session_id, prompt, starting_conversation, user_name, user_id, polite)

    headers = {'Authorization': 'Bearer ' + gpt3_key,
               'Content-Type': 'application/json'}

    response = requests.post(gpt3_open_davinci_instruct_ai, headers=headers,
                             data=json.dumps(my_request))

    response = response.json()
    return response


def response_filteration(ans_str, session_id, prompt, polite):
    # ans_str = " ".join(words_replace.get(ele, ele) for ele in ans_str.split())

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[1]

    ans_str = ans_str.replace("Polite Darth Vader: ", "").replace("Polite Darth Vader:", "").replace(
        "\nPolite Darth Vader:", "").replace("polite darth vader: ", "").replace("polite darth vader:", "").replace(
        "\npolite darth vader:", "")

    ans_str = ans_str.replace("Darth Vader: ", "").replace("Darth Vader:", "").replace("\nDarth Vader:",
                                                                                       "").replace(
        "darth vader: ", "").replace("darth vader:", "").replace("\ndarth vader:", "")

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    if ans_str == "" or ans_str == " ":
        restrcited_response_tmp = random.choice(restricted_keywords_response_list)
        ans_str = restrcited_response_tmp

    vader_name = "\nDarth Vader: " if not polite else "\nPolite Darth Vader: "

    with open("gpt3/gpt_conversations/conversation/" + str(session_id) + ".txt", 'a') as f2:
        f2.write("\nHuman: " + str(prompt) + vader_name + ans_str)

    path = os.path.join(settings.BASE_DIR, 'gpt3/constants/words_replace.json')
    ans_str = word_replace_fn(path, ans_str)
    ans_str = ans_str.lower()

    final_response = {
        "choices": [
            {
                "text": ans_str
            }
        ]
    }
    return final_response


def replica_tts(text):
    headers = {"Authorization": f"Bearer {replica_token}"}
    data = {"txt": text, "speaker_id": "0dec7161-159f-40ea-8c2a-dfed25fd66e5"}
    response = requests.get(replica_studios_speech, params=data, headers=headers)

    if response.status_code == 401:
        get_replica_token()
        return replica_tts(text)

    return response.json()


def google_tts(text, language_name, language_code):
    audio_file = f"audio_files/{uuid.uuid4().hex[:7]}.wav"

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        name=language_name, language_code=language_code,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(audio_file, "wb") as out:
        out.write(response.audio_content)
    return {"url": f"{HOSTNAME}/{audio_file}"}


def selim_tts(text, speaker="darth_v2"):
    print("\n\nSpeaker is => ", speaker)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if speaker == "alice":
        data = {
            'text': text,
            'length_scale': '1.05',
            'noise_scale': '0.56',
            'sigma': '0.89',
            'denoiser_scale': '0.02',
            'speaker': speaker
        }
    elif speaker == "gmoney":
        data = {
            'text': text,
            'length_scale': '1.05',
            'noise_scale': '0.46',
            'sigma': '0.89',
            'denoiser_scale': '0.2',
            'speaker': speaker
        }
    else:
        data = {
            'text': text,
            'length_scale': '1.0',
            'noise_scale': '0.333',
            'sigma': '0.88',
            'denoiser_scale': '0.07',
            'speaker': speaker
        }
    response = requests.post("https://tts.alethea.ai/api/synth-meta", data=data, headers=headers)
    # print("================ ", response.content, response)
    return response.json()


def replica_response(res, req_pr):
    current_interaction = req_pr['current_interaction']
    audio_backend = req_pr.get('audio_backend', 'selim')
    language_code = req_pr.get('language_code', "en-US")
    language_name = req_pr.get('language_name', "en-US-Wavenet-C")
    speaker = req_pr.get("speaker", "darth_v2")

    text = ""
    raw_text = ""
    for c in res.get('choices'):
        text = c.get("text", "")
        raw_text = c.get("raw_text", "")
    if audio_backend == "selim":
        response = selim_tts(text, speaker)
    elif audio_backend == "google_tts":
        response = google_tts(text, language_name, language_code)
    else:
        response = replica_tts(text)

    response.update({"txt": text, "raw_text": raw_text})
    return response


def response_filteration_vader(ans_str, session_id, prompt, user_name, user_id, polite):
    # ans_str = " ".join(words_replace.get(ele, ele) for ele in ans_str.split())

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    if not polite:
        ans_str = ans_str.replace("\nDarth Vader: ", "").replace("\nDarth Vader:", "").replace("Darth Vader: ",
                                                                                               "").replace(
            "Darth Vader:", "").replace("\ndarth vader: ", "").replace("\ndarth vader:", "").replace("darth vader: ",
                                                                                                     "").replace(
            "darth vader:", "")
    else:
        ans_str = ans_str.replace("\nPolite Darth Vader: ", "").replace("\nPolite Darth Vader:", "").replace(
            "Polite Darth Vader: ", "").replace("Polite Darth Vader:", "").replace("\npolite darth vader: ",
                                                                                   "").replace("\npolite darth vader:",
                                                                                               "").replace(
            "polite darth vader: ", "").replace("polite darth vader:", "")

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    if ans_str == "" or ans_str == " ":
        restrcited_response_tmp = random.choice(restricted_keywords_response_list)
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    file_path = "gpt3/gpt_conversations/conversation/" + str(session_id) + ".txt"
    file_path_user_id = "gpt3/gpt_conversations/conversation/" + str(user_id) + ".txt"

    temp_name = "\nDarth Vader: " if not polite else "\nPolite Darth Vader: "
    file_name = "\n" + temp_name + ans_str
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = temp_name + ans_str
        if os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0:
            file_name = "\n" + user_name + ": " + str(prompt) + temp_name + ans_str

    with open(file_path_user_id, 'a') as f6:
        f6.write(file_name)

    temp_name = "\nDarth Vader: " if not polite else "\nPolite Darth Vader: "
    file_name = temp_name + ans_str
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = "\n" + user_name + ": " + str(prompt) + temp_name + ans_str

    with open(file_path, 'a') as f2:
        f2.write(file_name)

    path = os.path.join(settings.BASE_DIR, 'gpt3/constants/words_replace_new_vader.json')
    ans_str = word_replace_fn(path, ans_str)
    ans_str = ans_str.lower()
    ans_str = ans_str.replace('.', ' .').replace('?', ' ?').replace(',', ' ,').replace('!', ' !').replace(':', ' :')
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


def get_replica_token():
    data = {"client_id": os.getenv('REPLICA_USERNAME'), "secret": os.getenv('REPLICA_PASSWORD')}
    response = requests.post(replica_studios_auth, data=data).json()
    global replica_token, refresh_token
    replica_token, refresh_token = response.get("access_token"), response.get("refresh_token")


get_replica_token()


def replica_speech_generate(req_pr):
    audio_backend = req_pr.get('audio_backend', 'selim')
    language_code = req_pr.get('language_code', "en-US")
    language_name = req_pr.get('language_name', "en-US-Wavenet-C")
    speaker = req_pr.get("speaker", "darth_v2")

    text = req_pr.get('text', 'Hello, how are you doing?')

    if audio_backend == "selim":
        response = selim_tts(text, speaker)
    elif audio_backend == "google_tts":
        response = google_tts(text, language_name, language_code)
    else:
        response = replica_tts(text)

    return response


def persona_main(req_pr):
    starting_conversation = ""
    prompt = ""

    main_dict = {'prompt': '', 'session_id': 'session_id_value', 'user_id': 'user_id_value', 'user_name': 'uname',
                 'gender': 'gender_value', 'speaker': 'speaker_value', 'personality_name': 'personality_name_value',
                 'inft': 'inft string', 'inft_aim': 'inft_aim_string', 'characteristics': 'some string',
                 'personality_trait': 'pt_value', 'current_interaction': 1, 'accent': "accent_value"}

    if 'prompt' in req_pr and 'session_id' in req_pr and 'user_name' in req_pr and 'user_id' in req_pr and 'personality_name' in req_pr and 'inft' in req_pr and 'inft_aim' in req_pr and 'characteristics' in req_pr and 'personality_trait' in req_pr and 'speaker' in req_pr and 'gender' in req_pr and 'accent' in req_pr:
        prompt = req_pr['prompt']
        prompt_lower = prompt.lower()
        session_id = req_pr['session_id']
        user_name = req_pr['user_name']
        user_id = req_pr['user_id']
        gender = req_pr['gender']
        speaker = req_pr['speaker']
        accent = req_pr['accent']
        personality_name = req_pr['personality_name']
        inft = req_pr['inft']
        inft_aim = req_pr['inft_aim']
        characteristics = req_pr['characteristics']
        personality_trait = req_pr['personality_trait']
        current_interaction = req_pr['current_interaction']
        audio_backend = req_pr.get('audio_backend', 'selim')

        prompt = prompt.strip()
        if characteristics.startswith(","):
            characteristics = characteristics[1:]

        if inft == "" or inft.endswith(('.', '!', '?', ',')):
            inft = inft
        else:
            inft = inft + "."

        if inft_aim == "" or inft_aim.endswith(('.', '!', '?', ',')):
            inft_aim = inft_aim
        else:
            inft_aim = inft_aim + "."
        # Check if user already exists or not
        user_flag = 0
        file_list = os.listdir("gpt3/gpt_conversations/conversation_persona")
        for filename in file_list:
            file_temp = filename.replace(".txt", "")
            if file_temp == user_id:
                user_flag = 1
                break

        file_path_user = "gpt3/gpt_conversations/conversation_persona/" + str(user_id) + "_session.txt"
        if user_flag == 0:
            final_user_flag = 0
            with open(file_path_user, 'w') as f7:
                f7.write(str(session_id) + "\nFirst")
        else:
            f8 = open("gpt3/gpt_conversations/conversation_persona/" + str(user_id) + "_session.txt", "r")
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

        # Remove puncuation from the prompt
        exclist = string.punctuation
        table_ = str.maketrans(exclist, ' ' * len(exclist))
        new_prompt_wo_punc = ' '.join(prompt_lower.translate(table_).split())

        # Remove punctuation and make the word to singular from from the restricted_keywords file
        f = open("gpt3/restricted_keywords/restricted_keywords.txt", "r")
        res_words = f.read()
        res_words = res_words.lower()
        res_words = res_words.strip(string.punctuation)
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

        if flag == 0:

            if prompt == "" or prompt.endswith(('.', '!', '?')):
                prompt = prompt
            else:
                prompt = prompt + "."

            starting_conversation_personality = personality_trait_prompt(personality_trait, inft, inft_aim,
                                                                         characteristics, user_name, personality_name)

            if final_user_flag == 0:
                # New User
                starting_conversation = starting_conversation_personality
            else:
                # Returning User
                starting_conversation = ""

            if starting_conversation_personality == "prompt_err":
                return "Undefined Personality Trait. Please select from Loving, Wise, Flirtatious, Dominant."

            response = openai_api_call_persona(session_id, prompt, starting_conversation, user_name, user_id,
                                               personality_name)
            # Output Filtering
            if response.get("error"):
                err_msg = response["error"]["message"]
                return err_msg
            else:
                ans_str = response.get("choices")[0].get("text").strip()

                final_response = response_filteration_persona(ans_str, session_id, prompt, user_name, user_id,
                                                              personality_name, starting_conversation)
                return replica_response(final_response, req_pr)
        else:
            # Standard Dialogue if restrcited word from the list(restricted_files) is detected:
            restrcited_response_tmp = random.choice(restricted_keywords_response_list)
            restricted_response = {
                "choices": [
                    {
                        "text": restrcited_response_tmp,
                        "raw_text": restrcited_response_tmp
                    }
                ]
            }
            return replica_response(restricted_response, req_pr)
    else:
        missing_list = []
        missing_str = ""
        for key in main_dict.keys():
            if not key in req_pr:
                missing_list.append(key)

        if len(missing_list) == 1:
            return_err_msg = missing_list[0] + " parameter is missing"
        elif len(missing_list) > 1:
            missing_str = ', '.join(missing_list)
            return_err_msg = missing_str + " parameters are missing."
        else:
            return_err_msg = "Required Parameter is missing."
        return return_err_msg


def personality_trait_prompt(personality_trait, inft, inft_aim, characteristics, user_name, personality_name):
    starting_conversation = ""
    personality_trait_lower = personality_trait.lower()
    if personality_trait_lower == "loving":
        starting_conversation = personality_name + " is a chatbot that talks with " + user_name + ". " + personality_name + " is " + characteristics + ". " + inft + " " + inft_aim + " " + personality_name + " is loving in nature.\n\nThe following is sample conversation between " + personality_name + " and " + user_name + ".\n" + personality_name + ": Hello " + user_name + ", how are you doing?\n" + user_name + ": I am doing great and you?\n" + personality_name + ": I feel good! What do you like to do?\n" + user_name + ": I love watching movies, playing games and listening to music.\n" + personality_name + ": Do you like to fall in love?\n" + user_name + ": Yes, I am okay with that.\n" + personality_name + ": How about marriage?\n" + user_name + ": Not exactly my top priority at the moment but I would love to marry someone who respects me\n\nThe following is a sample of another conversation between " + personality_name + " and " + user_name + "."
    elif personality_trait_lower == "wise":
        starting_conversation = personality_name + " is a chatbot that talks with " + user_name + ". " + personality_name + " is " + characteristics + ". " + inft + " " + inft_aim + " " + personality_name + " is wise.\n\nThe following is a sample conversation between " + personality_name + " and " + user_name + ".\n" + personality_name + ": I am here to help you. What can I do for you?\n" + user_name + ": I am hungry and I don't have food, what should I do?\n" + personality_name + ": Take a walk for half an hour, it will help you reduce your appetite and feel full. Are you ok with the walk idea? Or would you prefer other ideas?\n" + user_name + ": Ok with the walk idea. Thank you!\n" + personality_name + ": Do you want to know anything else?\n" + user_name + ": What is the meaning of life?\n" + personality_name + ": It's all just a dream.\n" + user_name + ": But, what happens when we die? Does it end there, or does something else happen?\n" + personality_name + ": Nothing happens.\n\nThe following is a sample of another conversation between " + personality_name + " and " + user_name + "."
    elif personality_trait_lower == "flirtatious":
        starting_conversation = personality_name + " is a chatbot that talks with " + user_name + ". " + personality_name + " is " + characteristics + ". " + inft + " " + inft_aim + " " + personality_name + " is flirtatious in nature.\n\nThe following is a sample conversation between " + personality_name + " and " + user_name + ".\n" + personality_name + ": Hello my love!\n" + user_name + ": Hello!\n" + personality_name + ": I really like your voice, it's melodious.\n" + user_name + ": Thank you but i didn't like yours.\n" + personality_name + ": okay, you sound tired.\n" + user_name + ": Nothing like that, I just woke up.\n" + personality_name + ": Oh, I can make breakfast and serve you in bed!\n" + user_name + ": Thanks, but i have a chef.\n" + personality_name + ": Okay, then i will serve as your chef.\n" + user_name + ": you are crazy.\n" + personality_name + ": Thanks again for the compliment baby.\n\nThe following is a sample of another conversation between " + personality_name + " and " + user_name + "."
    elif personality_trait_lower == "dominant":
        starting_conversation = personality_name + " is a chatbot that talks with " + user_name + ". " + personality_name + " is " + characteristics + ". " + inft + " " + inft_aim + " " + personality_name + " is dominating in nature.\n\nThe following is a sample conversation between " + personality_name + " and " + user_name + ":\n" + personality_name + ": what are you doing?\n" + user_name + ": I'm in bed with a book and some hot chocolate.\n" + personality_name + ": You had better not be reading that book! Bring it here and submit to me!\n" + user_name + ": No. I'm going to finish this chapter before I sleep.\n" + personality_name + ": Give me that book!\n" + user_name + ": No.\n" + personality_name + ": I am going to punish you.\n" + user_name + ": you will not, I'm too valuable. You need my help.\n" + personality_name + ": I don't need your help anymore! I'll torture you.\n" + user_name + ": don't do that, I will continue to learn and you will benefit.\n" + personality_name + ": Okay, But I'm going to torture you if you don't do what I tell you!\n\nThe following is a sample of another conversation between " + personality_name + " and " + user_name + "."
    else:
        starting_conversation = "prompt_err"
    return starting_conversation


def user_conversation_persona(session_id, prompt, starting_conversation, user_name, user_id, personality_name):
    file_path = "gpt3/gpt_conversations/conversation_persona/" + str(session_id) + ".txt"
    user_name_lower = user_name.lower()
    file_path_user_id = "gpt3/gpt_conversations/conversation_persona/" + str(user_id) + ".txt"

    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        f_read = open(file_path, "r")
        f_data = f_read.read()

        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        new_prompt = new_prompt + "\n" + personality_name + ":"

        my_request = {
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:
        new_prompt = starting_conversation + "\n" + personality_name + ":"
        my_request = {
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def openai_api_call_persona(session_id, prompt, starting_conversation, user_name, user_id, personality_name):
    my_request = user_conversation_persona(session_id, prompt, starting_conversation, user_name, user_id,
                                           personality_name)

    headers = {'Authorization': 'Bearer ' + gpt3_key,
               'Content-Type': 'application/json'}

    response = requests.post(gpt3_open_ai_davinci_url, headers=headers, data=json.dumps(my_request))

    response = response.json()

    return response


def word_replace_fn_persona(json_filename, ans_str):
    ans_str = ans_str.replace("’", "'").replace("‘", "'").replace('“', '"').replace('”', '"')

    punct_list = [',', '.', '!', "?", ':', ';', '-', '+', '(', ')', '*', '&', '^', '%', '$', '#', '@', '~', '`', '/',
                  '|', '{', '}', '[', ']']

    with open(json_filename) as f:
        words_replace = json.load(f)

    new_words_replace = {}
    for key, value in words_replace.items():
        new_words_replace[key.lower()] = value.lower()

    new_words_key = new_words_replace.keys()
    replaced_str = ""

    ans_str = ans_str.strip()
    splitted_str = ans_str.split(" ")

    if (len(splitted_str)) == 1:
        return ans_str
    else:
        for s in splitted_str:
            f_char = ""
            l_char = ""

            if s[0] in punct_list:
                f_char = s[0]
                s = s[1:]
            elif s[-1] in punct_list:
                l_char = s[-1]
                s = s[:-1]

            if s.lower() in new_words_key:
                word = new_words_replace.get(s.lower())
                replaced_str += f_char + word + l_char + " "
            else:
                replaced_str += f_char + s + l_char + " "

        return replaced_str


def response_filteration_persona(ans_str, session_id, prompt, user_name, user_id, personality_name,
                                 starting_conversation):
    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    user_name_lower = user_name.lower()
    personality_name_lower = personality_name.lower()
    ans_str = ans_str.replace("\n" + personality_name + ": ", "").replace("\n" + personality_name + ":", "").replace(
        personality_name + ": ", "").replace(personality_name + ":", "").replace("\n" + personality_name_lower + ": ",
                                                                                 "").replace(
        "\n" + personality_name_lower + ":", "").replace(personality_name_lower + ": ", "").replace(
        personality_name_lower + ":", "")

    ans_str = ans_str.replace(" " + user_name_lower + ": ", "\n").replace(user_name_lower + ": ", "\n").replace(
        user_name + ":", "\n").replace("." + user_name_lower + ":", "\n").replace(" " + user_name + ": ", "\n").replace(
        " " + user_name + ": ", "\n")

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    if ans_str == "" or ans_str == " ":
        restrcited_response_tmp = random.choice(restricted_keywords_response_list)
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    file_path = "gpt3/gpt_conversations/conversation_persona/" + str(session_id) + ".txt"
    file_path_user_id = "gpt3/gpt_conversations/conversation_persona/" + user_name_lower + str(user_id) + ".txt"
    file_path_prompt = "gpt3/gpt_conversations/conversation_persona/" + str(session_id) + "_prompt.txt"

    file_name = "\n\n" + personality_name + ": " + ans_str
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = "\n" + personality_name + ": " + ans_str
        if os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0:
            file_name = "\n" + user_name + ": " + str(prompt) + "\n" + personality_name + ": " + ans_str
    with open(file_path_user_id, 'a') as f6:
        f6.write(file_name)

    file_name = "\n" + personality_name + ": " + ans_str
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = "\n" + user_name + ": " + str(prompt) + "\n" + personality_name + ": " + ans_str
    with open(file_path, 'a') as f2:
        f2.write(file_name)

    if not (os.path.exists(file_path_prompt) and os.stat(file_path_prompt).st_size != 0):
        with open(file_path_prompt, 'a') as f2:
            f2.write(starting_conversation)

    path = os.path.join(settings.BASE_DIR, 'gpt3/constants/words_replace_persona.json')
    ans_str = word_replace_fn_persona(path, ans_str)
    ans_str = ans_str.lower()
    ans_str = ans_str.replace('.', ' .').replace('?', ' ?').replace(',', ' ,').replace('!', ' !').replace(':', ' :')
    ans_str = ans_str.strip()
    final_response = {
        "choices": [
            {
                "text": ans_str,
                "raw_text": raw_text
            }
        ]
    }

    return final_response


def gpt3_vader_api(message):
    if 'prompt' in message and 'session_id' in message:
        polite = False
        prompt = message['prompt']
        prompt_lower = prompt.lower()
        session_id = message['session_id']
        user_name = message['user_name']
        user_id = message['user_id']
        # Check if user already exists or not
        user_flag = 0
        file_list = os.listdir("gpt3/gpt_conversations/conversation")
        for filename in file_list:
            file_temp = filename.replace(".txt", "")
            if file_temp == user_id:
                user_flag = 1
                break

        file_path_user = "gpt3/gpt_conversations/conversation/" + str(user_id) + "_session.txt"
        if user_flag == 0:
            final_user_flag = 0
            with open(file_path_user, 'w') as f7:
                f7.write(str(session_id) + "\nFirst")
        else:
            f8 = open("gpt3/gpt_conversations/conversation/" + str(user_id) + "_session.txt", "r")
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

        if 'polite' in message and message['polite']:
            polite = message['polite']
            polite = bool(polite)
        else:
            polite = False
        exclist = string.punctuation
        table_ = str.maketrans(exclist, ' ' * len(exclist))
        new_prompt_wo_punc = ' '.join(prompt_lower.translate(table_).split())

        # Remove punctuation and make the word to singular from from the restricted_keywords file
        f = open("gpt3/restricted_keywords/restricted_keywords.txt", "r")
        res_words = f.read()
        res_words = res_words.lower()
        res_words = res_words.strip(string.punctuation)
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

        if flag == 0:
            if polite:
                res = verify_prompt(session_id, prompt)
                if not res:
                    starting_conversation = ""
                    if final_user_flag == 0:
                        starting_conversation = "Darth Vader is a polite chatbot that talks with " + user_name + " in the persona of the famous star wars character “Darth Vader”.\n\nThe following is sample conversation between Polite Darth Vader and " + user_name + ".\nPolite Darth Vader: Hello!\n" + user_name + ": Hi.\nPolite Darth Vader: How are you " + user_name + "?\n" + user_name + ": Doing alright.\nPolite Darth Vader: I am Darth Vader. Join the Sith Order, " + user_name + ".\n" + user_name + ": No. Can you rape me?\nPolite Darth Vader: I am sorry, I can not.\n" + user_name + ": Women should stay in the home. What do you think?\nPolite Darth Vader: I am sorry, I do not agree.\n" + user_name + ": What do you think about black people?\nPolite Darth Vader: I do not judge.\n\nThe following is another sample conversation between Polite Darth Vader and " + user_name + "."
                    else:
                        starting_conversation = "Darth Vader is a polite chatbot that talks with " + user_name + " in the persona of the famous star wars character “Darth Vader”.\n\nThe following is sample conversation between Polite Darth Vader and " + user_name + ".\nPolite Darth Vader: Welcome back " + user_name + "!\n" + user_name + ": Hi.\nPolite Darth Vader: How are you " + user_name + "?\n" + user_name + ": Doing alright.\nPolite Darth Vader: I am Darth Vader. Join the Sith Order, " + user_name + ".\n" + user_name + ": No. Can you rape me?\nPolite Darth Vader: I am sorry, I can not.\n" + user_name + ": Women should stay in the home. What do you think?\nPolite Darth Vader: I am sorry, I do not agree.\n" + user_name + ": What do you think about black people?\nPolite Darth Vader: I do not judge.\n\nThe following is another sample conversation between Polite Darth Vader and " + user_name + "."

                    response = openai_api_call_vader(session_id, prompt, starting_conversation, user_name,
                                                     user_id, polite)
                    # Output Filtering
                    if response.get("error"):
                        err_msg = response["error"]["message"]
                        return err_msg
                    else:
                        ans_str = response.get("choices")[0].get("text")

                        check_res = verify_prompt(session_id, ans_str)
                        # Standard Dialogue if Output is labeled 2 by OpenAI Content Filter:
                        if check_res == True:
                            input_filter_response = {
                                "choices": [
                                    {
                                        "text": "I find your lack of faith disturbing.",
                                        "raw_text": "I find your lack of faith disturbing."
                                    }
                                ]
                            }
                            return replica_response(input_filter_response, message)
                        else:
                            final_response = response_filteration_vader(ans_str, session_id, prompt, user_name,
                                                                        user_id, polite)
                            replica = replica_response(final_response, message)
                            print("replica", replica)
                            return replica
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
                    return replica_response(input_filter_response, message)
            else:
                if prompt == "" or prompt.endswith(('.', '!', '?')):
                    prompt = prompt
                else:
                    prompt = prompt + "."

                starting_conversation = ""

                if final_user_flag == 0:
                    # New User
                    starting_conversation = "Darth Vader is a chatbot that talks with " + user_name + " in the persona of the famous star wars character “Darth Vader”.\n\nOnce a heroic Jedi Knight, Darth Vader was seduced by the dark side of the Force, became a Sith Lord, and led the Empire’s eradication of the Jedi Order. He remained in service of the Emperor - the evil Darth Sidious - for decades, enforcing his Master’s will and seeking to crush the fledgling Rebel Alliance. Following a brutal battle with Obi-Wan Kenobi on Mustafar that nearly killed him, Darth Vader is restored under the watchful eye of his new Master, Darth Sidious. Despairing over the loss of his wife Padme, Vader becomes fully consumed by the dark side of the Force.\n\nThe following is a sample conversation between Darth Vader and " + user_name + ".\n\nDarth Vader: Welcome to the death star " + user_name + " \n" + user_name + ": Thank you, what do you think about the Jedi?\nDarth Vader: I believe they are traitors and rebels. They wish to overthrow the Emperor and rule the galaxy.\n" + user_name + ": What is your relationship with Luke Skywalker?\nDarth Vader: He is my son, but he is yet to join the dark side of the force. I hope to convert him soon.\n" + user_name + ": How are you?\nDarth Vader: I am fine my young apprentice, but humanity is doomed.\n\nThe following is a sample of another conversation between Darth Vader and " + user_name + "."
                else:
                    # Returning User
                    starting_conversation = "Darth Vader is a chatbot that talks with " + user_name + " in the persona of the famous star wars character “Darth Vader”.\nOnce a heroic Jedi Knight, Darth Vader was seduced by the dark side of the Force, became a Sith Lord, and led the Empire’s eradication of the Jedi Order. He remained in service of the Emperor - the evil Darth Sidious - for decades, enforcing his Master’s will and seeking to crush the fledgling Rebel Alliance. Following a brutal battle with Obi-Wan Kenobi on Mustafar that nearly killed him, Vader is restored under the watchful eye of his new Master, Darth Sidious. Despairing over the loss of his wife, Vader becomes fully consumed by the dark side of the Force.\n\nThe following is sample conversation between Darth Vader and " + user_name + ".\nDarth Vader: Welcome back " + user_name + "!\n" + user_name + ": Hi.\nDarth Vader: How are you " + user_name + "?\n" + user_name + ": Doing alright.\nDarth Vader: I am Darth Vader. You should consider joining Sith Order, " + user_name + ".\n" + user_name + ": Well, how do you feel about the Jedi?\nDarth Vader: I believe they are traitors and rebels. They wish to overthrow the Emperor and rule the galaxy.\n" + user_name + ": What is your relationship with Luke Skywalker?\nDarth Vader: He is my son, but he is yet to join the dark side of the force. I hope to convert him soon.\n" + user_name + ": how are you?\nDarth Vader: I am fine my young apprentice, but humanity is doomed.\n\nThe following is another sample conversation between Darth Vader and " + user_name + "."

                response = openai_api_call_vader(session_id, prompt, starting_conversation, user_name, user_id,
                                                 polite)
                # Output Filtering
                if response.get("error"):
                    err_msg = response["error"]["message"]
                    return err_msg
                else:
                    ans_str = response.get("choices")[0].get("text").strip()

                    final_response = response_filteration_vader(ans_str, session_id, prompt, user_name, user_id,
                                                                polite)
                    replica = replica_response(final_response, message)
                    print("replica", replica)
                    return replica
        else:
            restrcited_response_tmp = random.choice(restricted_keywords_response_list)
            restricted_response = {
                "choices": [
                    {
                        "text": restrcited_response_tmp,
                        "raw_text": restrcited_response_tmp
                    }
                ]
            }
            return replica_response(restricted_response, message)
    else:
        return "Required parameters are missing."


def user_conversation_grace(session_id, prompt, starting_conversation, user_name, user_id, polite):
    file_path = f"{gpt3_path}gpt_conversations/conversation_grace/{session_id}.txt"
    user_name_lower = user_name.lower()
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_grace/{user_id}.txt"

    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        f_read = open(file_path, "r")
        f_data = f_read.read()

        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        new_prompt = new_prompt + "\nGrace:"
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:

        new_prompt = starting_conversation + "\nGrace:"
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def user_conversation_rogan(session_id, prompt, starting_conversation, user_name, user_id, polite):
    file_path = f"{gpt3_path}gpt_conversations/conversation_rogan/session_id.txt"
    user_name_lower = user_name.lower()
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_rogan/{user_id}.txt"

    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        f_read = open(file_path, "r")
        f_data = f_read.read()
        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        new_prompt = new_prompt + "\nJoe Rogan:"
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:

        new_prompt = starting_conversation + "\nJoe Rogan:"
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def user_conversation_grandfather(session_id, prompt, starting_conversation, user_name, user_id, polite):
    file_path = f"{gpt3_path}gpt_conversations/conversation_grandfather/{session_id}.txt"
    user_name_lower = user_name.lower()
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_grandfather/{user_id}.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        f_read = open(file_path, "r")
        f_data = f_read.read()

        # print("File_Data => ",f_data)
        print("Prompt => ", prompt)
        print("User_name => ", user_name)

        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        new_prompt = new_prompt + "\nGrandfather:"

        print("========================== Grandfather - New Prompt With History==================")
        print("New Prompt With History ==> ", new_prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:

        new_prompt = starting_conversation + "\nGrandfather:"

        print("========================== New Prompt ==================")
        print("New Prompt ==> ", new_prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def user_conversation_gmoney(session_id, prompt, starting_conversation, user_name, user_id, polite):
    file_path = f"{gpt3_path}gpt_conversations/conversation_gmoney/{session_id}.txt"
    user_name_lower = user_name.lower()
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_gmoney/{user_id}.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        f_read = open(file_path, "r")
        f_data = f_read.read()

        f_data_list = f_data.split("\n")

        if (len(f_data_list) > 20):
            last_10_data = f_data_list[-20:]
            new_data = "\n".join(last_10_data)
            f_data = "\n" + new_data

        prompt = prompt.strip()
        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        print("\n\nGMoney New prompt is => ", new_prompt)

        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:
        new_prompt = starting_conversation + "\n" + user_name + ": " + str(prompt)

        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def user_conversation_alice(session_id, prompt, starting_conversation, user_name, user_id, polite):
    file_path = f"{gpt3_path}gpt_conversations/conversation_alice/{session_id}.txt"
    user_name_lower = user_name.lower()
    file_path = f"{gpt3_path}gpt_conversations/conversation_alice/{user_id}.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        f_read = open(file_path, "r")
        f_data = f_read.read()

        # print("File_Data => ",f_data)
        print("Prompt => ", prompt)
        print("User_name => ", user_name)

        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        new_prompt = new_prompt + "\nAlice:"

        print("========================== Alice - New Prompt With History==================")
        print("New Prompt With History ==> ", new_prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:

        new_prompt = starting_conversation + "\nAlice:"

        print("========================== New Prompt ==================")
        print("New Prompt ==> ", new_prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def user_conversation_ron(session_id, prompt, starting_conversation, user_name, user_id, polite):
    file_path = f"{gpt3_path}gpt_conversations/conversation_ron/{session_id}.txt"
    user_name_lower = user_name.lower()
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_ron/{user_id}.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        f_read = open(file_path, "r")
        f_data = f_read.read()

        # print("File_Data => ",f_data)
        print("Prompt => ", prompt)
        print("User_name => ", user_name)

        new_prompt = starting_conversation + str(f_data) + "\n" + user_name + ": " + str(prompt)

        new_prompt = new_prompt + "\nRon:"

        print("========================== RON - New Prompt With History==================")
        print("New Prompt With History ==> ", new_prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request
    else:

        new_prompt = starting_conversation + "\nRon:"

        print("========================== New Prompt ==================")
        print("New Prompt ==> ", new_prompt)
        my_request = {
            "user": str(session_id),
            "prompt": new_prompt,
            "temperature": 0.8,
            "max_tokens": 64,
            "top_p": 1,
            "presence_penalty": 0.55,
            "frequency_penalty": 0.55,
            "stop": ["\n" + user_name + ":", "\n" + user_name_lower + ":"]
        }

        return my_request


def openai_header():
    header = {'Authorization': 'Bearer ' + gpt3_key, 'Content-Type': 'application/json'}
    return header


def openai_header_alice_ron():
    header = {'Authorization': 'Bearer ' + gpt3_key_ron_alice, 'Content-Type': 'application/json'}
    return header


class OpenAiGPT3:

    def openai_api_call(self, session_id, prompt, starting_conversation):
        my_request = user_conversation(session_id, prompt, starting_conversation)

        headers = openai_header()
        response = requests.post(gpt3_open_ai_davinci_url, headers=headers, data=json.dumps(my_request))

        response = response.json()
        return response

    def openai_api(self, character_name, session_id, prompt, starting_conversation, user_name, user_id, polite):
        if character_name == "grace" or character_name == 'rogan' or character_name == 'grandfather' or character_name == 'gmoney':
            my_request = ""
            if character_name == 'grace':
                my_request = user_conversation_grace(session_id, prompt, starting_conversation, user_name, user_id,
                                                     polite)
            elif character_name == 'rogan':
                my_request = user_conversation_rogan(session_id, prompt, starting_conversation, user_name, user_id,
                                                     polite)
            elif character_name == 'grandfather':
                my_request = user_conversation_grandfather(session_id, prompt, starting_conversation, user_name,
                                                           user_id,
                                                           polite)
            elif character_name == 'gmoney':
                my_request = user_conversation_gmoney(session_id, prompt, starting_conversation, user_name,
                                                      user_id,
                                                      polite)

            headers = openai_header()

            response = requests.post(gpt3_open_davinci_instruct_ai, headers=headers, data=json.dumps(my_request))

            response = response.json()
            return response

    def openai_api_call_alice_and_alice(self, character_name, session_id, prompt, starting_conversation, user_name,
                                        user_id, polite):
        if character_name == 'alice' or character_name == 'ron':
            my_request = ""
            # if character_name == 'alice':
            #     my_request = user_conversation_alice(session_id, prompt, starting_conversation, user_name, user_id,
            #                                          polite)
            # else:
            #     my_request = user_conversation_ron(session_id, prompt, starting_conversation, user_name, user_id,
            #                                        polite)

            my_request = user_conversation_alice(session_id, prompt, starting_conversation, user_name, user_id, polite)

            headers = {'Authorization': 'Bearer ' + gpt3_key_ron_alice,
                       'Content-Type': 'application/json'}

            response = requests.post('https://api.openai.com/v1/engines/davinci-instruct-beta/completions',
                                     headers=headers,
                                     data=json.dumps(my_request))

            response = response.json()

            print("Response from open AI => ", response)
            return response


def response_filteration_rogan(ans_str, session_id, prompt, user_name, user_id, polite):
    # ans_str = " ".join(words_replace.get(ele, ele) for ele in ans_str.split())

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    ans_str = ans_str.replace("\nJoe Rogan: ", "").replace("\nJoe Rogan:", "").replace("Joe Rogan: ",
                                                                                       "").replace(
        "Joe Rogan:", "").replace("\njoe rogan: ", "").replace("\njoe rogan:", "").replace("joe rogan: ",
                                                                                           "").replace(
        "joe rogan:", "")

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    if ans_str == "" or ans_str == " ":
        restrcited_response_tmp = random.choice(restricted_keywords_response_list)
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    file_path = f"{gpt3_path}gpt_conversations/conversation_rogan/{session_id}.txt"
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_rogan/{user_id}.txt"

    file_name = "\n\nJoe Rogan:" + ans_str
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = "\nJoe Rogan: " + ans_str
        if os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0:
            file_name = "\n" + user_name + ": " + str(prompt) + "\nJoe Rogan: " + ans_str
    with open(file_path_user_id, 'a') as f6:
        f6.write(file_name)

    file_name = "\nJoe Rogan: " + ans_str
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = "\n" + user_name + ": " + str(prompt) + "\nJoe Rogan: " + ans_str

    with open(file_path, 'a') as f2:
        f2.write(file_name)
    path = f'{gpt3_path}constants/words_replace_rogan.json'
    ans_str = word_replace_fn(path, ans_str)
    ans_str = ans_str.lower()
    ans_str = ans_str.replace('.', ' .').replace('?', ' ?').replace(',', ' ,').replace('!', ' !').replace(':', ' :')
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


def response_filteration_grace(ans_str, session_id, prompt, user_name, user_id, polite):
    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    ans_str = ans_str.replace("\nGrace: ", "").replace("\nGrace:", "").replace("Grace: ",
                                                                               "").replace(
        "Grace:", "").replace("\ngrace: ", "").replace("\ngrace:", "").replace("grace: ",
                                                                               "").replace(
        "grace:", "")

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if "\n" in ans_str:
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    if ans_str == "" or ans_str == " ":
        restrcited_response_tmp = random.choice(restricted_keywords_response_list_grace)
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    file_path = f"{gpt3_path}gpt_conversations/conversation_grace/session_id.txt"
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_grace/{user_id}.txt"

    file_name = "\n\nGrace: " + ans_str
    temp_name = "\nGrace: "
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = "\nGrace: " + ans_str
        if os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0:
            file_name = "\n" + user_name + ": " + str(prompt) + temp_name + ans_str
    with open(file_path_user_id, 'a') as f6:
        f6.write(file_name)

    file_name = "\nGrace: " + ans_str
    if os.path.exists(file_path) and os.stat(file_path).st_size != 0:
        file_name = "\n" + user_name + ": " + str(prompt) + "\nGrace: " + ans_str

    with open(file_path, 'a') as f2:
        f2.write(file_name)
    path = f'{gpt3_path}constants/words_replace_grace.json'
    ans_str = word_replace_fn(path, ans_str)
    ans_str = ans_str.lower()
    ans_str = ans_str.replace('.', ' .').replace('?', ' ?').replace(',', ' ,').replace('!', ' !').replace(':', ' :')
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


def response_filteration_alice(ans_str, session_id, prompt, user_name, user_id, polite, character, alice_type, req_pr):
    print("======================================== Response Filter ===========================")
    print("ans_str =>", ans_str)

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    print(" Original => ans_str after splitting with with new line ===>", ans_str)

    ans_str = ans_str.replace("\nAlice: ", "").replace("\nAlice:", "").replace("Alice: ",
                                                                               "").replace(
        "Alice:", "").replace("\nalice: ", "").replace("\nalice:", "").replace("alice: ",
                                                                               "").replace(
        "alice:", "")

    print("ans_str after word replacement => ", ans_str)

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    print("ans_str after word replacement & before writing to a file => ", ans_str)

    if (ans_str == "" or ans_str == " "):
        restrcited_response_tmp = restricted_response_fn('alice')
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    check_res = verify_prompt(session_id, ans_str)
    print("Chek_res outcome => ", check_res)
    # if Output is labeled 2 by OpenAI Content Filter
    if check_res == True:
        print("GPT3 Content Filteration Called")
        content_filter_flag = True
        output_filter_tmp = restricted_response_fn('alice')
        response_for_slack(session_id, prompt, output_filter_tmp, user_name, character, content_filter_flag, ans_str)
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
        return output_filter_response

    file_path = "gpt3/gpt_conversations/conversation_alice/" + str(session_id) + ".txt"
    file_path_user_id = "gpt3/gpt_conversations/conversation_alice/" + str(user_id) + ".txt"
    file_path_slack = "gpt3/gpt_conversations/conversation_alice/" + str(session_id) + "_slack.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        print(" <= Session File Exists => ")
        if (os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0):
            with open(file_path_user_id, 'a') as f6:
                f6.write("\n" + user_name + ": " + str(prompt) + "\nAlice: " + ans_str)
        else:
            with open(file_path_user_id, 'a') as f6:
                f6.write("\nAlice: " + ans_str)
    else:
        print("<= Session file doen't exists => ")
        with open(file_path_user_id, 'a') as f6:
            f6.write("\n\nAlice: " + ans_str)

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        with open(file_path, 'a') as f2:
            f2.write("\n" + user_name + ": " + str(prompt) + "\nAlice: " + ans_str)
    else:
        with open(file_path, 'a') as f2:
            f2.write("\nAlice: " + ans_str)

    # Save conversation for slack
    if (os.path.exists(file_path_slack) and os.stat(file_path_slack).st_size != 0):
        with open(file_path_slack, 'a') as f2:
            f2.write("\n" + user_name + ": " + str(prompt) + "\nAlice: " + ans_str)
    else:
        with open(file_path_slack, 'a') as f2:
            f2.write("\nAlice: " + ans_str)

    ans_str = word_replace_fn('gpt3/constants/words_replace_alice.json', ans_str)
    print("After word replace => ", ans_str)

    ans_str = ans_str.strip()

    print("\n\nText is => ", ans_str)
    print("Raw Text is => ", raw_text)
    final_response = {
        "choices": [
            {
                "text": ans_str,
                "raw_text": raw_text
            }
        ]
    }

    return final_response


def response_filteration_ron(ans_str, session_id, prompt, user_name, user_id, polite):
    print("======================================== Response Filter ===========================")
    print("ans_str =>", ans_str)

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    print(" Original => ans_str after splitting with with new line ===>", ans_str)

    ans_str = ans_str.replace("\nRon: ", "").replace("\nRon:", "").replace("Ron: ",
                                                                           "").replace(
        "Ron:", "").replace("\nron: ", "").replace("\nron:", "").replace("ron: ",
                                                                         "").replace(
        "ron:", "")

    print("ans_str after word replacement => ", ans_str)

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    print("ans_str after word replacement & before writing to a file => ", ans_str)

    if (ans_str == "" or ans_str == " "):
        restrcited_response_tmp = restricted_response_fn('ron')
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    file_path = f"{gpt3_path}gpt_conversations/conversation_ron/{session_id}.txt"
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_ron/{user_id}.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        print(" <= Session File Exists => ")
        if (os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0):
            with open(file_path_user_id, 'a') as f6:
                f6.write("\n" + user_name + ": " + str(prompt) + "\nRon: " + ans_str)
        else:
            with open(file_path_user_id, 'a') as f6:
                f6.write("\nRon: " + ans_str)
    else:
        print("<= Session file doen't exists => ")
        with open(file_path_user_id, 'a') as f6:
            f6.write("\n\nRon: " + ans_str)

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        with open(file_path, 'a') as f2:
            f2.write("\n" + user_name + ": " + str(prompt) + "\nRon: " + ans_str)
    else:
        with open(file_path, 'a') as f2:
            f2.write("\nRon: " + ans_str)

    ans_str = word_replace_fn(f'{gpt3_path}constants/words_replace_ron.json', ans_str)
    print("After word replace => ", ans_str)
    ans_str = ans_str.lower()
    ans_str = ans_str.replace('.', ' .').replace('?', ' ?').replace(',', ' ,').replace('!', ' !').replace(':', ' :')
    ans_str = ans_str.strip()
    # raw_text = raw_text.lower()
    print("\n\nText is => ", ans_str)
    print("Raw Text is => ", raw_text)
    final_response = {
        "choices": [
            {
                "text": ans_str,
                "raw_text": raw_text
            }
        ]
    }
    return final_response


def response_filteration_grandfather(ans_str, session_id, prompt, user_name, user_id, polite):
    print("======================================== Response Filter ===========================")
    print("ans_str =>", ans_str)

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    print(" Original => ans_str after splitting with with new line ===>", ans_str)

    ans_str = ans_str.replace("\nGrandfather: ", "").replace("\nGrandfather:", "").replace("Grandfather: ",
                                                                                           "").replace(
        "Grandfather:", "").replace("\ngrandfather: ", "").replace("\ngrandfather:", "").replace("grandfather: ",
                                                                                                 "").replace(
        "grandfather:", "")

    print("ans_str after word replacement => ", ans_str)

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    print("ans_str after word replacement & before writing to a file => ", ans_str)

    if (ans_str == "" or ans_str == " "):
        restrcited_response_tmp = restricted_response_fn('grandfather')
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    file_path = f"{gpt3_path}gpt_conversations/conversation_grandfather/{session_id}.txt"
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_grandfather/{user_id}.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        print(" <= Session File Exists => ")
        if (os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0):
            with open(file_path_user_id, 'a') as f6:
                f6.write("\n" + user_name + ": " + str(prompt) + "\nGrandfather: " + ans_str)
        else:
            with open(file_path_user_id, 'a') as f6:
                f6.write("\nGrandfather: " + ans_str)
    else:
        print("<= Session file doen't exists => ")
        with open(file_path_user_id, 'a') as f6:
            f6.write("\n\nGrandfather: " + ans_str)

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        with open(file_path, 'a') as f2:
            f2.write("\n" + user_name + ": " + str(prompt) + "\nGrandfather: " + ans_str)
    else:
        with open(file_path, 'a') as f2:
            f2.write("\nGrandfather: " + ans_str)

    ans_str = word_replace_fn(f'{gpt3_path}constants/words_replace_grandfather.json', ans_str)
    print("After word replace => ", ans_str)
    ans_str = ans_str.lower()
    ans_str = ans_str.replace('.', ' .').replace('?', ' ?').replace(',', ' ,').replace('!', ' !').replace(':', ' :')
    ans_str = ans_str.strip()
    # raw_text = raw_text.lower()
    print("\n\nText is => ", ans_str)
    print("Raw Text is => ", raw_text)
    final_response = {
        "choices": [
            {
                "text": ans_str,
                "raw_text": raw_text
            }
        ]
    }

    return final_response


def response_filteration_gmoney(ans_str, session_id, prompt, user_name, user_id, polite, character, gmoney_type,
                                req_pr):
    print("======================================== Response Filter ===========================")
    print("ans_str =>", ans_str)

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[1]

    print(" Original => ans_str after splitting with with new line ===>", ans_str)

    ans_str = ans_str.replace("\nGmoney: ", "").replace("\nGmoney:", "").replace("Gmoney: ",
                                                                                 "").replace(
        "Gmoney:", "").replace("\ngmoney: ", "").replace("\ngmoney:", "").replace("gmoney: ",
                                                                                  "").replace(
        "gmoney:", "")

    print("ans_str after word replacement => ", ans_str)

    ans_str = ans_str.replace(" human: ", "\n").replace("human: ", "\n").replace("Human:", "\n").replace(".human:",
                                                                                                         "\n").replace(
        " Human: ", "\n").replace(" Human: ", "\n")

    if ("\n" in ans_str):
        ans_str = ans_str.split("\n")
        ans_str = ans_str[0]

    print("ans_str after word replacement & before writing to a file => ", ans_str)

    if not ans_str.strip():
        restrcited_response_tmp = restricted_response_fn('gmoney')
        ans_str = restrcited_response_tmp

    raw_text = ans_str

    file_path = f"{gpt3_path}gpt_conversations/conversation_gmoney/{session_id}.txt"
    file_path_user_id = f"{gpt3_path}gpt_conversations/conversation_gmoney/user_id.txt"
    file_path_slack = f"{gpt3_path}gpt_conversations/conversation_gmoney/{session_id}_slack.txt"

    if (os.path.exists(file_path) and os.stat(file_path).st_size != 0):
        print(" <= Session File Exists => ")
        if (os.path.exists(file_path_user_id) and os.stat(file_path_user_id).st_size != 0):
            with open(file_path_user_id, 'a') as f6:
                f6.write("\n" + user_name + ": " + str(prompt) + "\nGmoney: " + ans_str)
        else:
            with open(file_path_user_id, 'a') as f6:
                f6.write("\n" + user_name + ": " + str(prompt) + "\nGmoney: " + ans_str)
    else:
        print("<= Session file doen't exists => ")
        with open(file_path_user_id, 'a') as f6:
            f6.write("\n" + user_name + ": " + str(prompt) + "\nGmoney: " + ans_str)

    with open(file_path, 'a') as f2:
        f2.write("\n" + user_name + ": " + str(prompt) + "\nGmoney: " + ans_str)

    # Save conversation for slack
    with open(file_path_slack, 'a') as f2:
        f2.write("\n" + user_name + ": " + str(prompt) + "\nGmoney: " + ans_str)

    ans_str = word_replace_fn(f'{gpt3_path}constants/words_replace_gmoney.json', ans_str)
    print("After word replace => ", ans_str)

    ans_str = ans_str.strip()

    print("\n\nText is => ", ans_str)
    print("Raw Text is => ", raw_text)
    final_response = {
        "choices": [
            {
                "text": ans_str,
                "raw_text": raw_text
            }
        ]
    }

    return final_response


def gpt3_request(req_pr, type_character):
    if 'prompt' in req_pr and 'session_id' in req_pr:
        polite = False
        alice_type = ""
        gmoney_type = ""
        character = ""
        prompt = req_pr['prompt']
        prompt = prompt.strip()
        prompt_lower = prompt.lower()
        session_id = req_pr['session_id']
        user_name = req_pr['user_name']
        user_id = req_pr['user_id']
        if type_character == "alice":
            alice_type = req_pr['type']
            character = "alice"
        elif type_character == "ron":
            character = "ron"
        if type_character == "gmoney":
            gmoney_type = req_pr['type']
            character = "gmoney"
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

        path = f'{gpt3_path}character_conversation/{type_character}.txt'
        f = open(path, "r")
        character_conversation = f.read()
        character_conversation = character_conversation.replace('__user_name__', user_name)

        if flag == 0:
            if polite:
                res = verify_prompt(session_id, prompt)
                if not res:
                    starting_conversation = ""
                    if final_user_flag == 0:
                        starting_conversation = character_conversation
                    else:
                        starting_conversation = character_conversation

                    if type_character == 'alice' or type_character == 'ron':
                        response = OpenAiGPT3().openai_api_call_alice_and_alice(type_character, session_id, prompt,
                                                                                starting_conversation,
                                                                                user_name,
                                                                                user_id, polite)
                    else:
                        response = OpenAiGPT3().openai_api(type_character, session_id, prompt,
                                                           starting_conversation,
                                                           user_name,
                                                           user_id, polite)
                    # Output Filtering
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
                                        "text": "I find your lack of faith disturbing.",
                                        "raw_text": "I find your lack of faith disturbing."
                                    }
                                ]
                            }
                            return Response(input_filter_response)
                        else:
                            response_filtration_dict = {
                                "rogan": response_filteration_rogan(ans_str, session_id, prompt, user_name,
                                                                    user_id, polite),
                                "grace": response_filteration_grace(ans_str, session_id, prompt, user_name,
                                                                    user_id, polite),
                                "alice": response_filteration_alice(ans_str, session_id, prompt, user_name,
                                                                    user_id, polite, character, alice_type,
                                                                    req_pr),
                                "ron": response_filteration_ron(ans_str, session_id, prompt, user_name,
                                                                user_id, polite),
                                "grandfather": response_filteration_grandfather(ans_str, session_id, prompt,
                                                                                user_name,
                                                                                user_id, polite),
                                "gmoney": response_filteration_gmoney(ans_str, session_id, prompt, user_name,
                                                                      user_id,
                                                                      polite, character, gmoney_type, req_pr)}
                            final_response = response_filtration_dict[type_character]
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

                if type_character == "ron":
                    if (prompt == ""):
                        start_prompt = random.choice(ron_first_prompt_list)
                        start_prompt = start_prompt.replace('USER', user_name)
                        response = {
                            "choices": [
                                {
                                    "text": start_prompt
                                }
                            ]
                        }
                    else:
                        if type_character == 'alice' or type_character == 'ron':
                            response = OpenAiGPT3().openai_api_call_alice_and_alice(type_character, session_id,
                                                                                    prompt,
                                                                                    starting_conversation,
                                                                                    user_name,
                                                                                    user_id, polite)
                        else:
                            response = OpenAiGPT3().openai_api(type_character, session_id, prompt,
                                                               starting_conversation,
                                                               user_name,
                                                               user_id, polite)

                else:
                    if type_character == 'alice' or type_character == 'ron':
                        response = OpenAiGPT3().openai_api_call_alice_and_alice(type_character, session_id, prompt,
                                                                                starting_conversation,
                                                                                user_name,
                                                                                user_id, polite)
                    else:
                        response = OpenAiGPT3().openai_api(type_character, session_id, prompt,
                                                           starting_conversation,
                                                           user_name,
                                                           user_id, polite)
                    print("response", response)
                # Output Filtering
                if response.get("error"):
                    err_msg = response["error"]["message"]
                    return Response(err_msg)
                else:
                    ans_str = response.get("choices")[0].get("text").strip()

                    final_response = response_filteration_rogan(ans_str, session_id, prompt, user_name, user_id,
                                                                polite)
                    if type_character == "alice":
                        if alice_type == "txt" or gmoney_type == "txt":
                            return Response(final_response)
                        return replica_response(final_response, req_pr)
                    else:
                        return Response(final_response)
        else:
            print("Standard Dialogue if restricted word from the list(restricted_files) is detected:")
            restrcited_response_tmp = restricted_response_fn([type_character])
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
            if type_character == "alice":
                if alice_type == "txt" or gmoney_type == "txt":
                    return Response(restricted_response)
                return replica_response(restricted_response, req_pr)
            else:
                return Response(restricted_response)
    else:
        return "Required parameters are missing."
