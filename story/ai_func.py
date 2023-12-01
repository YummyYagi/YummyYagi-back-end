from django.conf import settings
from openai import OpenAI
import deepl
from .backoff import retry_with_exponential_backoff
from googleapiclient import discovery


def load_deepl_model():
    # Deepl API 키 설정 및 객체 생성
    deepl_auth_key = settings.DEEPL_AUTH_KEY
    deepl_translator = deepl.Translator(deepl_auth_key)
    return deepl_translator


def load_open_ai_model():
    # OpenAI(ChatGPT & DALL-E) API에 연결하기 위한 키 설정 및 클라이언트 객체 생성
    openai_client = OpenAI(api_key=settings.GPT_API_KEY)

    # ChatGPT 모델 설정
    chatgpt_model = "gpt-3.5-turbo"
    return openai_client, chatgpt_model


def load_pers_model():
    # Perspective API 키 설정 및 객체 생성
    pers_client = discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=settings.PRES_API_KEY,
        discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        static_discovery=False,
    )
    return pers_client


def translate_text(deepl_translator, user_input_message, deepl_target_lang="EN-US"):
    # Deepl을 사용하여 User에게 받은 질문 번역하기
    trans_result = deepl_translator.translate_text(
        user_input_message, target_lang=deepl_target_lang
    )
    return trans_result


def check_toxicity(pers_client, checkToxicity_str):
    # Perspective API 사용하여 User가 입력한 질문에서 폭력성 검출하기
    analyze_request = {
        "comment": {"text": checkToxicity_str},
        "requestedAttributes": {"TOXICITY": {}},
    }
    pers_response = pers_client.comments().analyze(body=analyze_request).execute()
    pers_score = pers_response["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
    print("폭력성 검열 전 수치 : ", pers_score)
    return pers_score


def setup_gpt_messages(inputQurry):
    # GPT 메세지 설정
    input_query = inputQurry.text
    input_gpt_messages = []
    input_gpt_messages.append(
        {
            "role": "system",
            "content": "You are an excellent fairy tale writer.I will send the content of your fairy tale to DALL-E to create a picture, so make a fairy tale according to the topic I am talking about so as not to violate openai's content policy.",
        }
    )
    input_gpt_messages.append(
        {"role": "user", "content": f"fairy tale topic : {input_query}"}
    )
    return input_gpt_messages


def run_gpt(openai_client, chatgpt_model, input_gpt_messages):
    # GPT 실행
    @retry_with_exponential_backoff
    def completions_with_backoff(**kwargs):
        return openai_client.chat.completions.create(**kwargs)

    completion = completions_with_backoff(
        model=chatgpt_model,
        messages=input_gpt_messages,
        temperature=1.3,
    )
    gpt_response = completion.choices[0].message.content
    print(f"ChatGPT : {gpt_response}")
    return gpt_response


@retry_with_exponential_backoff
def generate_images_from_text(script, d_model, quality, user_tickets):
    client = OpenAI(api_key=settings.GPT_API_KEY)

    response = client.images.generate(
        model=d_model,
        prompt=f"{script} in a drawing of fairy tale style",
        size="1024x1024",
        quality=quality,
        n=1,
    )

    image_url = response.data[0].url
    return image_url
