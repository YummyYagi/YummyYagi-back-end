from django.conf import settings
from openai import OpenAI
import deepl

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


def generate_images_from_text(script, d_model, quality, user_tickets):

    client = OpenAI(api_key=settings.GPT_API_KEY)

    response = client.images.generate(
        model=d_model,
        prompt=f'{script} in a drawing of fairy tale style',
        size='1024x1024',
        quality=quality,
        n=1,
    )

    image_url = response.data[0].url
    return image_url
