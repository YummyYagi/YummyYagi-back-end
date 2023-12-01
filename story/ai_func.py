from django.conf import settings
import openai
from openai import OpenAI
import deepl
import logging
from story.time_decorator import timing_decorator
from .backoff import retry_with_exponential_backoff
from googleapiclient import discovery
from rest_framework import status
from rest_framework.response import Response

error_logger = logging.getLogger("error_logger")


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


@timing_decorator
def translate_text(deepl_translator, user_input_message, deepl_target_lang="EN-US"):
    # Deepl을 사용하여 User에게 받은 질문 번역하기
    try:
        trans_result = deepl_translator.translate_text(
            user_input_message, target_lang=deepl_target_lang
        )
        return trans_result
    except deepl.exceptions.QuotaExceededException as e:
        error_logger.error(f"DeePl) Quota exceeded: {str(e)}")
        return Response(
            {"status": "456", "error": "번역 기능이 작동하지 않습니다. 고객센터에 문의해주세요."},
            status=status.HTTP_456.QUOTA_EXCEEDED,
        )
    except deepl.exceptions.TooManyRequestsException as e:
        error_logger.error(f"DeePl) Too Many Requests: {str(e)}")
        return Response(
            {"status": "429", "error": "연속된 요청으로 번역에 실패했습니다. 다시 요청해주세요."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    except deepl.exceptions.DeepLException as e:
        error_logger.error(f"DeePl) Exception: {str(e)}")
        return Response(
            {"status": "500", "error": "번역에 실패했습니다. 다시 시도해주세요."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        error_logger.error(f"DeePl)  Unexpected Error: {str(e)}")
        return Response(
            {
                "status": "500",
                "error": "죄송합니다. 서버에서 오류가 발생했습니다. 문제가 지속되면 고객센터에 문의해주세요.",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

def check_toxicity(pers_client, check_toxicity_str):
    # Perspective API 사용하여 User가 입력한 질문에서 폭력성 검출하기
    analyze_request = {
        "comment": {"text": check_toxicity_str},
        "requestedAttributes": {"TOXICITY": {}},
    }
    pers_response = pers_client.comments().analyze(body=analyze_request).execute()
    pers_score = pers_response["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
    print("폭력성 검열 전 수치 : ", pers_score)
    return pers_score


def setup_gpt_messages(input_query):
    # GPT 메세지 설정
    input_query = input_query.text
    input_gpt_messages = []
    input_gpt_messages.append(
        {
            "role": "system",
            "content": "You are a super wonderful fairytail author. Please create an engaging story that children can enjoy reading based on the given topic. The generated fairy tales will be used when requesting DALL-E to create images. Please create a fairy tale with content that complies with the Prompt policy. Additionally, please do not include content that is harmful to children, hateful, harassing, violent, promotes sexual services, has political themes, or deals with people's personal information. Please do not use sensitive or difficult language, do not infringe copyrights, and comply with OpenAI's content policy to create fairy tales for children that are safe, creative, imaginative, and with a happy ending."
        }
    )
    input_gpt_messages.append(
        {"role": "user", "content": f"{input_query}"}
    )
    return input_gpt_messages


@timing_decorator
def run_gpt(openai_client, chatgpt_model, input_gpt_messages):
    # GPT 실행
    try:

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

    except openai.AuthenticationError as e:
        error_logger.error(f"ChatGPT) API key or token Error: {str(e)}")
        return Response(
            {"status": "500", "error": "서비스에 문제가 생겨 동화 생성 실패했습니다. 고객센터에 문의해주세요."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except openai.RateLimitError as e:
        error_logger.error(f"ChatGPT) Too Many Requests: {str(e)}")
        return Response(
            {"status": "429", "error": "많은 동시 요청으로 인해 동화 생성에 실패했습니다. 잠시 후 다시 요청해주세요."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    except openai.UnprocessableEntityError as e:
        error_logger.error(f"ChatGPT)  Unable to process the request: {str(e)}")
        return Response(
            {"status": "500", "error": "동화 생성 실패했습니다. 다시 요청해주세요."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except openai.BadRequestError as e:
        error_logger.error(f"ChatGPT) Bad Request Error: {str(e)}")
        return Response(
            {"status": "400", "error": "정책상의 이유로 이미지 생성이 불가능합니다. 내용을 수정해주세요."},
            status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        error_logger.error(f"ChatGPT)  Unexpected Error: {str(e)}")
        return Response(
            {
                "status": "500",
                "error": "죄송합니다. 서버에서 오류가 발생했습니다. 문제가 지속되면 고객센터에 문의해주세요.",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@timing_decorator
@retry_with_exponential_backoff
def generate_images_from_text(script, d_model, quality):
    client = OpenAI(api_key=settings.GPT_API_KEY)

    try:
        response = client.images.generate(
            model=d_model,
            prompt=f"Illustrate '{script}' in an adorable, lovely, and detailed fairy tale style that children will adore. Ensure that the generated image does not contain any text or characters and creates a clear, lively, and detailed fairy tale.",
            size="1024x1024",
            quality=quality,
            n=1,
        )

        image_url = response.data[0].url
        return image_url


    except openai.AuthenticationError as e:
        error_logger.error(f"DALL-E) API key or token Error: {str(e)}")
        return Response(
            {"status": "500", "error": "서비스에 문제가 생겨 동화 생성 실패했습니다. 고객센터에 문의해주세요."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except openai.RateLimitError as e:
        error_logger.error(f"DALL-E) Too Many Requests: {str(e)}")
        return Response(
            {"status": "429", "error": "많은 동시 요청으로 인해 이미지 생성에 실패했습니다. 잠시 후 다시 요청해주세요."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    except openai.UnprocessableEntityError as e:
        error_logger.error(f"DALL-E)  Unable to process the request : {str(e)}")
        return Response(
            {"status": "500", "error": "동화 생성 실패했습니다. 다시 요청해주세요."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except openai.BadRequestError as e:
        error_logger.error(f"DALL-E) Bad Request Error: {str(e)}")
        return Response(
            {"status": "400", "error": "정책상의 이유로 이미지 생성이 불가능합니다. 내용을 수정해주세요."},
            status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        error_logger.error(f"DALL-E)  Unexpected Error : {str(e)}")
        return Response(
            {
                "status": "500",
                "error": "죄송합니다. 서버에서 오류가 발생했습니다. 문제가 지속되면 고객센터에 문의해주세요.",
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
