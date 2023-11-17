from django.urls import path
from story import views

urlpatterns = [
    path('',views.StoryView.as_view(), name='story_view'),
    path('like_sorted/',views.StorySortedByLikeView.as_view(), name='story_sorted_like_view'),
    path('country_sorted/<str:author_country>/',views.StorySortedByCountryView.as_view(), name='story_sorted_country_view'),
    path('<int:story_id>/',views.StoryView.as_view(), name='detail_page_view'),

    path('<int:story_id>/like/',views.LikeView.as_view(), name='like_view'),
    path('<int:story_id>/hate/',views.HateView.as_view(), name='hate_view'),
    path('<int:story_id>/bookmark/',views.BookmarkView.as_view(), name='bookmark_view'),

    path('<int:story_id>/comment/',views.CommentView.as_view(), name='comment_view'),
    path('<int:story_id>/comment/<int:comment_id>/',views.CommentView.as_view(), name='comment_delete_view'),

    path('fairytail_gpt/', views.RequestFairytail.as_view(), name='request_fairytail_view'),
    path('image_dall-e/', views.RequestImage.as_view(), name='request_image_view'),
    
    path('kakao/', views.KakaoShareView.as_view(), name='kakao_share_view()'),
    path('translation/', views.StoryTranslation.as_view(), name='story_translation'),
]