from rest_framework.views import APIView


class MainPageView(APIView):
    def get(self, request):
        """메인페이지입니다."""
        pass
  
    
class DetailPageView(APIView):
    def get(self, request, story_id):
        """작성된 게시글(동화) 상세페이지입니다."""
        pass
  
  
class StoryCreateView(APIView):
    def post(self, request):
        """게시글(동화) 작성 페이지입니다."""
        pass

class StoryDeleteView(APIView):
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