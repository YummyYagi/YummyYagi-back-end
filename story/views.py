
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, exceptions
from rest_framework.generics import get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.files.base import ContentFile
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.timezone import now
from itertools import chain
import requests

import deepl
from openai import OpenAI
from googleapiclient import discovery

from .backoff import retry_with_exponential_backoff
from story.models import Story, Comment
from user.models import UserStoryTimeStamp
from story.serializers import StoryListSerializer, StorySerializer, CommentSerializer, CommentCreateSerializer, StoryCreateSerializer, ContentCreateSerializer
from story.permissions import IsAuthenticated


class RequestFairytail(APIView):
    def post(self, request):
        
        # OpenAI(ChatGPT & DALL-E) API에 연결하기 위한 클라이언트 객체를 생성
        client = OpenAI(api_key = settings.GPT_API_KEY)
        
        # Deepl API 키 설정
        deepl_auth_key = settings.DEEPL_AUTH_KEY
        translator = deepl.Translator(deepl_auth_key)
        deepl_target_lang = 'EN-US'
        
        # ChatGPT 모델 설정
        model = 'gpt-3.5-turbo'
        
        # Perspective API 키 설정
        pres_api_key = settings.PRES_API_KEY
        
        # Perspective client 생성
        pers_client = discovery.build(
            'commentanalyzer',
            'v1alpha1',
            developerKey=pres_api_key,
            discoveryServiceUrl='https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1',
            static_discovery=False,
        )
        
        # User에게 질문 받기
        user_input_message = request.data['subject']
        
        # Deepl을 사용하여 User에게 받은 질문 영어로 번역하기
        trans_result = translator.translate_text(
            user_input_message, target_lang=deepl_target_lang)
        
        # 번역된 값 형변환 'deepl.api_data.TextResult' -> 'str'
        trans_str_result = str(trans_result)
        
        # Perspective API 사용하여 User가 입력한 질문에서 폭력성 검출하기
        analyze_request = {
            'comment': {'text': trans_str_result},
            'requestedAttributes': {'TOXICITY': {}},
        }
        pers_user_response = pers_client.comments().analyze(body=analyze_request).execute()
        pers_user_score = pers_user_response['attributeScores']['TOXICITY']['summaryScore']['value']
        print('폭력성 검열 전 수치 : ', pers_user_score)
        
        # 폭력성 수치를 넘으면 다시 입력하게 하기
        if pers_user_score > 0.3:
            print('입력한 문장에서 폭력성이 검출되었습니다. 점수 : ', pers_user_score)
            return Response({'status':'200', 'message':'주제에서 폭력성이 검출되어 동화 생성이 불가능합니다. 주제를 수정해주세요.'}, status=status.HTTP_200_OK)

        # GPT 질문 작성
        input_query = trans_result.text
        
        # GPT 메세지 설정
        input_gpt_messages = []
        input_gpt_messages.append(
            {'role': 'system', 'content': "You are an excellent fairy tale writer.I will send the content of your fairy tale to DALL-E to create a picture, so make a fairy tale according to the topic I am talking about so as not to violate openai's content policy."})
        input_gpt_messages.append({'role': 'user', 'content': f'fairy tale topic : {input_query}'}) 
        
        @retry_with_exponential_backoff
        def completions_with_backoff(**kwargs):
            return client.chat.completions.create(**kwargs)
        # GPT 실행
        completion = completions_with_backoff(
            model=model,
            messages=input_gpt_messages,
            temperature=1.3,
        )
        gpt_response = completion.choices[0].message.content
        print(f'ChatGPT : {gpt_response}')
        
        # Perspective API 사용하여 GPT가 답변한 내용에서 폭력성 검출하기
        analyze_request = {
            'comment': {'text': gpt_response},
            'requestedAttributes': {'TOXICITY': {}},
        }
        pers_gpt_response = pers_client.comments().analyze(body=analyze_request).execute()
        pers_gpt_score = pers_gpt_response['attributeScores']['TOXICITY']['summaryScore']['value']
        print('폭력성 검열 전 수치 : ', pers_gpt_score)
        
        # 폭력성 수치를 넘으면 다시 입력하게 하기
        if pers_gpt_score > 0.3:
            print('GPT의 답변에서 폭력성이 검출되었습니다. 점수 : ', pers_gpt_score)
            return Response({'status':'200', 'message':'생성된 동화 내용에 폭력성이 검출되어 동화 생성이 불가능합니다. 주제를 수정해주세요.'}, status=status.HTTP_200_OK)
        
        gpt_trans_result = translator.translate_text(
            gpt_response, target_lang=request.data['target_language'])
        
        # 번역된 값 형변환 'deepl.api_data.TextResult' -> 'str'
        gpt_trans_result=str(gpt_trans_result)
        print(f'번역 ChatGPT : {gpt_trans_result}')
        
        input_gpt_messages.append({'role': 'assistant', 'content': gpt_response})
        
        return Response({'status':'200', 'message':'동화를 성공적으로 생성했습니다.', 'original':gpt_response, 'translation':gpt_trans_result}, status=status.HTTP_200_OK)

class RequestImage(APIView):
    def post(self, request):
        client = OpenAI(api_key=settings.GPT_API_KEY)
        original_texts = request.data['original_script'].split('<br><br>')
        translated_texts = request.data['translated_script'].split('<br><br>')
        results = []

        @retry_with_exponential_backoff
        def completions_with_backoff(**kwargs):
            return client.images.generate(**kwargs)
        temp_original_text=''
        temp_translated_text=''
        story_length=len(original_texts)-1
        for i,(original_text,translated_text) in enumerate(zip(original_texts,translated_texts)):
            temp_original_text+=original_text
            temp_translated_text+=translated_text
            if i%2==1 or i==story_length:
                response = completions_with_backoff(
                    model='dall-e-2',
                    prompt=f'"{temp_original_text}" in a drawing of fairy tale style',
                    size='512x512',
                    quality='standard',
                    n=1,
                )

                print(response)
                temp_dict = {'text': temp_translated_text}

                if isinstance(response.data, list) and len(response.data) > 0:
                    temp_dict['image_url'] = response.data[0].url
                else:
                    temp_dict['image_url'] = 'Error or default image URL'

                results.append(temp_dict)
                temp_original_text=''
                temp_translated_text=''

        return Response({'status': '201', 'results': results}, status=status.HTTP_201_CREATED)


class StorySortedByLikeView(APIView):
    def get(self, request):
        """
        모든 게시물을 좋아요 순으로 8개만 Response 합니다.
        """        
        stories = Story.objects.exclude(hate_count__gt=4).order_by('-like_count', '-created_at')[:8] # 좋아요 많은 / 최신순
        serializer = StoryListSerializer(stories, many=True)
        return Response({'status': '200', 'story_list': serializer.data}, status=status.HTTP_200_OK)
        
        
class StorySortedByCountryView(APIView):
    def get(self, request, author_country):
        """
        국가별 게시물을 Response 합니다.
        """
        stories = Story.objects.filter(hate_count__lte=4, author__country=author_country).order_by('-like_count', '-created_at')[:8] # 국가별 / 좋아요 많은 / 최신순
        serializer = StoryListSerializer(stories, many=True)
        return Response({'status': '200', 'story_list': serializer.data}, status=status.HTTP_200_OK)


class StoryView(APIView):
    def get(self, request, story_id = None):
        """
        story_id가 없을 경우 모든 계시물을 Response 합니다.
        story_id가 있을 경우 특정 게시물을 Response 합니다.
        """
        page = request.GET.get('page', 1)
        per_page = settings.REST_FRAMEWORK['PAGE_SIZE']
        
        if story_id is None:
            stories = Story.objects.exclude(hate_count__gt=4).order_by('-created_at') # 최신순
            paginator = Paginator(stories, per_page)
            try:
                stories_page = paginator.page(page)
            except PageNotAnInteger:
                stories_page = paginator.page(1)
            except EmptyPage:
                stories_page = paginator.page(paginator.num_pages)
            serializer = StoryListSerializer(stories_page, many=True)
            page_info = {
                'current_page': stories_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
            }
            return Response({'status': '200', 'story_list': serializer.data, 'page_info': page_info}, status=status.HTTP_200_OK)
        else:
            """상세 페이지"""
            story = Story.objects.get(id=story_id)
            self.user_viewed(now(),story)
                
            if story.hate_count < 5:
                serializer = StorySerializer(story)
                return Response({'status':'200', 'detail':serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status':'403', 'error':'관리자만 열람 가능한 스토리입니다.'}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        """게시글(동화) 작성 페이지입니다."""
        serializer = StoryCreateSerializer(data=request.data)


        if serializer.is_valid():
            story = serializer.save(author = request.user)

            story_id=story.id
            paragraph_list = request.data['paragraph_list']
            image_url_list = request.data['image_url_list']

            image_file_list = []
            for image_url in image_url_list:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_content = ContentFile(response.content)
                    image_content.name = 'story_image.jpg'
                    image_file_list.append(image_content)

            for i in range(len(paragraph_list)):
                content_data = {'paragraph':paragraph_list[i], 'image':image_file_list[i]}
                content_serializer = ContentCreateSerializer(data=content_data)
                if content_serializer.is_valid():
                    content_serializer.save(story=story)
                else:
                    
                    return Response({'status':'400', 'error':'동화 페이지 작성에 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'status':'201', 'success':'동화가 작성되었습니다.', 'story_id':story_id}, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response({'status':'400', 'error':'동화 작성에 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, story_id):
        """작성된 게시글(동화)을 삭제하는 기능입니다."""
        try:
            story = Story.objects.get(id = story_id)
        except Story.DoesNotExist:
            raise exceptions.NotFound({'status':'404', 'error':'스토리를 찾을 수 없습니다.'})

        if request.user.is_authenticated:
            if request.user == story.author:
                story.delete()
                return Response({'status':'204', 'success':'동화가 삭제되었습니다.'})
            else :
                return Response({'status':'403', 'error':'삭제 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'status':'401', 'error':'로그인 후 이용해주세요'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def user_viewed(self,timestamp,story):
        user=self.request.user
        if not user.is_authenticated:
            return
        ust, _ =UserStoryTimeStamp.objects.get_or_create(user=user,story=story)
        ust.timestamp=timestamp
        ust.save()
        return ust.timestamp

class LikeView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):
        """게시글 좋아요 기능입니다."""
        try:
            story = Story.objects.get(id = story_id)
        except Story.DoesNotExist:
            raise exceptions.NotFound({'status':'404', 'error':'스토리를 찾을 수 없습니다.'})

        if request.user in story.like.all():
            story.like.remove(request.user)
            story.like_count -= 1
            story.save()
            like_count = story.like_count
            return Response({'status':'200', 'success':'좋아요 취소', 'like_count': like_count}, status=status.HTTP_200_OK)
        else:
            story.like.add(request.user)
            story.like_count += 1
            story.save()
            like_count = story.like_count
            return Response({'status':'200', 'success':'좋아요', 'like_count':like_count}, status=status.HTTP_200_OK)
            
    
class HateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):
        """게시글 싫어요 기능입니다."""
        try:
            story = Story.objects.get(id = story_id)
        except Story.DoesNotExist:
            raise exceptions.NotFound({'status':'404', 'error':'스토리를 찾을 수 없습니다.'})

        if request.user in story.hate.all():
            story.hate.remove(request.user)
            story.hate_count -= 1
            story.save()
            hate_count = story.hate_count
            return Response({'status':'200', 'success':'싫어요 취소', 'hate_count':hate_count}, status=status.HTTP_200_OK)
        else:
            story.hate.add(request.user)
            story.hate_count += 1
            story.save()
            hate_count = story.hate_count
            return Response({'status':'200', 'success':'싫어요', 'hate_count':hate_count}, status=status.HTTP_200_OK)

    
class BookmarkView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, story_id):
        """관심있는 게시글(동화)을 북마크합니다."""
        try:
            story = Story.objects.get(id = story_id)
        except Story.DoesNotExist:
            raise exceptions.NotFound({'status':'404', 'error':'스토리를 찾을 수 없습니다.'})

        if request.user in story.bookmark.all():
            story.bookmark.remove(request.user)
            return Response({'status':'200', 'success':'북마크 취소'}, status=status.HTTP_200_OK)
        else:
            story.bookmark.add(request.user)
            return Response({'status':'200', 'success':'북마크'}, status=status.HTTP_200_OK)


class CommentView(APIView):
    def get(self, request, story_id):
        """댓글을 조회합니다."""
        story = Story.objects.get(id=story_id)
        comments = story.comment_set.all().order_by('-id')
        serializer = CommentSerializer(comments, many=True)
        return Response({'status':'200', 'comments':serializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request, story_id):
        """댓글을 작성합니다."""
        if request.user.is_authenticated:
            serializer = CommentCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(author=request.user, story_id=story_id)
                return Response({'status':'201', 'success':'댓글 작성 완료'}, status=status.HTTP_201_CREATED)
            elif 'content' in serializer.errors:
                return Response({'status':'400', 'error':'댓글 내용을 입력해주세요'}, status=status.HTTP_400_BAD_REQUEST)
        else :
            return Response({'status':'401', 'error':'로그인 후 이용가능합니다.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    def delete(self, request, story_id, comment_id):
        """댓글을 삭제합니다."""
        if request.user.is_authenticated:
            comment = get_object_or_404(Comment, id=comment_id)
            if request.user == comment.author:
                comment.delete()
                return Response({'status':'204', 'success':'댓글 삭제 완료'})
            else:
                return Response({'status':'403', 'error':'권한이 없습니다'}, status=status.HTTP_403_FORBIDDEN)
        else :
            return Response({'status':'401', 'error':'로그인 후 이용가능합니다.'}, status=status.HTTP_401_UNAUTHORIZED)


class KakaoShareView(APIView):
    """카카오 API 키를 제공하는 뷰입니다."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        kakao_api_key = settings.KAKAO_API_KEY
        return Response({'status':'200', 'kakao_api_key':kakao_api_key})
    

class StoryTranslation(APIView):
    """스토리 상세 페이지를 번역해주는 뷰입니다."""
    def post(self, request):
        try:
            # Deepl API 키 설정
            deepl_auth_key = settings.DEEPL_AUTH_KEY
            translator = deepl.Translator(deepl_auth_key)
            deepl_target_lang = request.data['target_language']
        
            # 제목 번역
            trans_title_result = translator.translate_text(
                request.data['story_title'], target_lang=deepl_target_lang)
            trans_title_str_result = str(trans_title_result)
            
            translated_scripts = []
            
            # 스크립트 번역
            for script in request.data['story_script'] :
                trans_script_result = translator.translate_text(
                script['paragraph'], target_lang=deepl_target_lang)

                # 번역된 값 형변환 'deepl.api_data.TextResult' -> 'str'
                trans_script_str_result = str(trans_script_result)
                translated_scripts.append(trans_script_str_result)
        
            return Response({'status':'200', 'translated_scripts':translated_scripts, 'translated_title':trans_title_str_result}, status=status.HTTP_200_OK)
        except:
            return Response({'status':'400', 'error':'번역 실패'}, status=status.HTTP_400_BAD_REQUEST)