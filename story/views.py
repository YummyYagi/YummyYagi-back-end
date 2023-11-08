from rest_framework.views import APIView
from story.models import Story
from rest_framework.response import Response
from story.serializers import StoryListSerializer
from rest_framework import status


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
        pass


class LikeView(APIView):
    def post(self, request, story_id):
        """게시글 좋아요 기능입니다."""
        pass
    
    
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
        pass
    
    def post(self, request, story_id):
        """댓글을 작성합니다."""
        pass
    
    def delete(self, request, story_id, comment_id):
        """댓글을 삭제합니다."""
        pass