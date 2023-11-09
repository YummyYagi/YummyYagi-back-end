from rest_framework.views import APIView
from story.models import Story, Comment
from rest_framework.response import Response
from story.serializers import StoryListSerializer, StorySerializer, CommentSerializer, CommentCreateSerializer, StoryCreateSerializer, ContentCreateSerializer
from rest_framework import status, exceptions
from story.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404 

from django.conf import settings
import deepl
from openai import OpenAI
from googleapiclient import discovery
import requests
from django.core.files.base import ContentFile

class RequestFairytail(APIView):
    def post(self, request):
        
        # OpenAI(ChatGPT & DALL-E) API에 연결하기 위한 클라이언트 객체를 생성
        client = OpenAI(api_key = settings.GPT_API_KEY)
        
        # Deepl API 키 설정
        deepl_auth_key = settings.DEEPL_AUTH_KEY
        translator = deepl.Translator(deepl_auth_key)
        deepl_target_lang = 'EN-US'
        
        # ChatGPT 모델 설정
        model = "gpt-3.5-turbo"
        
        # Perspective API 키 설정
        pres_api_key = settings.PRES_API_KEY
        
        # Perspective client 생성
        pers_client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=pres_api_key,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
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
            return Response({'status':'200', 'success':'주제에서 폭력성이 검출되어 동화 생성이 불가능합니다. 주제를 수정해주세요.'}, status=status.HTTP_200_OK)

        # GPT 질문 작성
        input_query = trans_result.text
        
        # GPT 메세지 설정
        input_gpt_messages = []
        input_gpt_messages.append(
            {'role': 'system', 'content': 'You are a helpful assistant. You must not use violent language.'})
        input_gpt_messages.append({'role': 'user', 'content': input_query}) 
        
        # GPT 실행
        completion = client.chat.completions.create(
            model=model,
            messages=input_gpt_messages,
            temperature=1.3,
            max_tokens=500
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
            return Response({'status':'200', 'success':'생성된 동화 내용에 폭력성이 검출되어 동화 생성이 불가능합니다. 주제를 수정해주세요.'}, status=status.HTTP_200_OK)
        
        gpt_trans_result = translator.translate_text(
            gpt_response, target_lang=request.data['target_language'])
        print(f'번역 ChatGPT : {gpt_trans_result}')
        
        input_gpt_messages.append({'role': 'assistant', 'content': gpt_response})
        
        return Response({'status':'200', 'success':'', '원본':gpt_response, '번역본':gpt_trans_result}, status=status.HTTP_200_OK)


class RequestImage(APIView):
    def post(self, request):
        
        # OpenAI API에 연결하기 위한 클라이언트 객체를 생성
        client = OpenAI(api_key = settings.GPT_API_KEY)
        
        # 문단 나누는 로직
        paragragh_list = request.data["script"].split('/n/n')

        image_url_list = []

        for paragragh in paragragh_list:
            response = client.images.generate(
            model='dall-e-3',
            prompt=paragragh,
            size='1024x1024',
            quality='standard',
            n=1,
            )
            
            image_url = response.data[0].url
            image_url_list.append(image_url)
        
        return Response({'status':'201', 'paragraph_list':paragragh_list, 'image_url_list':image_url_list}, status=status.HTTP_201_CREATED)


class StoryView(APIView):
    def get(self, request, story_id = None):
        """
        story_id가 없을 경우 모든 계시물을 Response 합니다.
        story_id가 있을 경우 특정 게시물을 Response 합니다.
        """
        if story_id is None:
            stories = Story.objects.exclude(hate_count__gt=5).order_by('-created_at')
            serializer = StoryListSerializer(stories, many=True)
            return Response({'status':'200', 'story_list':serializer.data}, status=status.HTTP_200_OK)
        else:
            """상세 페이지"""
            story = Story.objects.get(id=story_id)
            if story.hate_count < 5:
                serializer = StorySerializer(story)
                return Response({'status':'200', 'detail':serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'status':'403', 'error':"관리자만 열람 가능한 스토리입니다."}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        """게시글(동화) 작성 페이지입니다."""
        serializer = StoryCreateSerializer(data=request.data)


        if serializer.is_valid():
            story = serializer.save(author = request.user)

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
            return Response({'status':'201', 'success':'동화가 작성되었습니다.'}, status=status.HTTP_201_CREATED)
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
                return Response({'status':'204', 'success':'동화가 삭제되었습니다.'}, status=status.HTTP_204_NO_CONTENT)
            else :
                return Response({'status':'403', 'error':'삭제 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'status':'401', 'error':'로그인 후 이용해주세요'}, status=status.HTTP_401_UNAUTHORIZED)


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
            return Response({'status':'200', 'success':'좋아요 취소'}, status=status.HTTP_200_OK)
        else:
            story.like.add(request.user)
            return Response({'status':'200', 'success':'좋아요'}, status=status.HTTP_200_OK)
            
    
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

            return Response({'status':'200', 'success':'싫어요 취소'}, status=status.HTTP_200_OK)
        else:
            story.hate.add(request.user)
            story.hate_count += 1
            story.save()
            return Response({'status':'200', 'success':'싫어요'}, status=status.HTTP_200_OK)

    
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
        comments = story.comment_set.all()
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
                return Response({'status':'204', 'success':'댓글 삭제 완료'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'status':'403', 'error':'권한이 없습니다'}, status=status.HTTP_403_FORBIDDEN)
        else :
            return Response({'status':'401', 'error':'로그인 후 이용가능합니다.'}, status=status.HTTP_401_UNAUTHORIZED)