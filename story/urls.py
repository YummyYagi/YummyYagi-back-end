from django.urls import path
from story import views

urlpatterns = [
    path('create/',views.StoryCreateView.as_view(), name='story_create_view'),
    path('',views.MainPageView.as_view(), name='main_page_view'),
    path('<int:story_id>/',views.DetailPageView.as_view(), name='detail_page_view'),
    path('delete/<int:story_id>/',views.StoryDeleteView.as_view(), name='story_delete_view'),

    path('<int:story_id>/like/',views.LikeView.as_view(), name='like_view'),
    path('<int:story_id>/hate/',views.HateView.as_view(), name='hate_view'),
    path('<int:story_id>/bookmark/',views.BookmarkView.as_view(), name='bookmark_view'),
    
    path('<int:story_id>/comment/create/',views.CommentView.as_view(), name='comment_create_view'),
    path('<int:story_id>/comment/',views.CommentView.as_view(), name='comment_view'),
    path('<int:story_id>/comment/delete/<int:comment_id>/',views.CommentView.as_view(), name='comment_delete_view'),
]