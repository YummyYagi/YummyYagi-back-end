from rest_framework.views import APIView
from story.models import Story
from rest_framework.response import Response
from story.serializers import StoryListSerializer, CommentSerializer
from rest_framework import status, exceptions
from story.permissions import IsAuthenticated


class StoryView(APIView):
    def get(self, request, story_id = None):
        """
        story_id가 없을 경우 모든 계시물을 Response 합니다.
        story_id가 있을 경우 특정 게시물을 Response 합니다.
        """
        if story_id is None:
            stories = Story.objects.all().order_by('-created_at')
            serializer = StoryListSerializer(stories, many=True)
            return Response({'status':'200', 'story_list':serializer.data}, status=status.HTTP_200_OK)
        else:
            """상세 페이지"""

    def post(self, request):
        """게시글(동화) 작성 페이지입니다."""
        pass
    
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
    def post(self, request, story_id):
        """게시글 싫어요 기능입니다."""
        pass
    
    
class BookmarkView(APIView):
    def post(self, request, story_id):
        """관심있는 게시글(동화)을 북마크합니다."""
        pass


class CommentView(APIView):
    def get(self, request, story_id):
        """댓글을 조회합니다."""
        story = Story.objects.get(id=story_id)
        comments = story.comment_set.all()
        serializer = CommentSerializer(comments, many=True)
        return Response({'status':'200', 'comments':serializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request, story_id):
        """댓글을 작성합니다."""
        pass
    
    def delete(self, request, story_id, comment_id):
        """댓글을 삭제합니다."""
        pass