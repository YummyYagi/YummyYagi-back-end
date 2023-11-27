from django.conf import settings
from openai import OpenAI
from openai._exceptions import OpenAIError
import deepl
from rest_framework import status
from rest_framework.response import Response

def translateText(script):
    """번역 기능 함수"""

    # Deepl API 키 설정
    deepl_auth_key = settings.DEEPL_AUTH_KEY
    translator = deepl.Translator(deepl_auth_key)
    deepl_target_lang = 'EN-US'

    
    # Deepl을 사용하여 User에게 받은 질문 번역하기
    trans_result = translator.translate_text(
        script, target_lang=deepl_target_lang)

    return trans_result


def generate_images_from_text(script, d_model, quality):
    """DALL-E 실행 함수"""
    try:
        client = OpenAI(api_key=settings.GPT_API_KEY)

        response = client.images.generate(
            model=d_model,
            prompt=f'{script} in a drawing of fairy tale style',
            size='1024x1024',
            quality=quality,
            n=1,
        )

        # 정상적으로 이미지 URL을 받았을 때의 처리
        image_url = response.data[0].url
        return image_url

    except OpenAIError:
        # OpenAI API 호출 중 발생한 예외 처리
        return Response({'status': '400', 'error': '죄송합니다. 이미지 생성 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

    except Exception:
        # 다른 예외들에 대한 일반적인 예외 처리
        return Response({'status': '400', 'error': '죄송합니다. 이미지 생성 중 예기치 않은 문제가 발생했습니다. 잠시 후 다시 시도해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
