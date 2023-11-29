from django.db import models
from django.conf import settings

class Story(models.Model):
    """
    게시글(스토리)을 정의하는 클래스입니다.
    
    - author : 스토리 작성자입니다.
        - 로그인 한 사용자를 자동으로 지정합니다.
    - title : 스토리 제목입니다.
    - like : 스토리를 좋아요 한 사용자와의 관계입니다.
    - hate : 스토리를 싫어요 한 사용자와의 관계입니다.
    - bookmark : 스토리를 북마크 한 사용자와의 관계입니다.
    - created_at : 스토리가 작성된 일자 및 시간입니다.
        - 스토리가 작성된 시간을 자동으로 저장하도록 설정합니다.
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='작성자', on_delete=models.CASCADE)
    title = models.CharField('스토리 제목', max_length=255)
    like = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='좋아요', related_name='like_stories', blank=True)
    like_count = models.PositiveIntegerField('좋아요 개수', default=0)
    hate = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='싫어요', related_name='hate_stories', blank=True)
    hate_count = models.PositiveIntegerField('싫어요 개수', default=0)
    bookmark = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name='북마크', related_name='bookmark_stories', blank=True)
    created_at = models.DateTimeField('생성시각', auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'story'
        verbose_name_plural = 'stories'
        

def story_image_upload_path(instance, filename):
    """게시글(스토리) 이미지의 저장 경로를 정의합니다."""
    return f'story/{instance.story.id}/{filename}'

class Content(models.Model):
    """
    게시글(스토리)의 내용을 정의하는 클래스입니다.
    
    - story : 게시글입니다.
    - paragraph : 게시글 내용의 문단입니다.
    - image : 해당 문단의 이미지입니다.
    
    """
    story = models.ForeignKey(Story, verbose_name='스토리', on_delete=models.CASCADE, related_name="contents")
    paragraph = models.TextField('문단')
    image = models.ImageField('문단 이미지', upload_to=story_image_upload_path)
    
    class Meta:
        db_table = 'content'
    
    
class Comment(models.Model):
    """
    게시글(스토리)의 댓글을 정의하는 클래스입니다.
    
    - author : 댓글 작성자입니다.
        - 로그인 한 사용자를 자동으로 지정합니다.
    - story : 댓글이 작성된 게시글(스토리)입니다.  
    - content : 댓글의 내용입니다.
    """
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='작성자', on_delete=models.CASCADE)
    story = models.ForeignKey(Story, verbose_name='스토리', on_delete=models.CASCADE)
    content = models.TextField('댓글 내용')
    
    def __str__(self):
        return self.content

    class Meta:
        db_table = 'comment'