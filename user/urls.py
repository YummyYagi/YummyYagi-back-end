from django.urls import path
from user import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register_view'),
    path('login/', views.LoginView.as_view(), name='login_view'),
    path('mypage/', views.MyPageView.as_view(), name='mypage_view'),
    path('info/', views.UserInfoView.as_view(), name='user_info_view'),
    path('info-update/', views.UserInfoView.as_view(), name='user_info_update_view'),
    path('pwd-update/', views.UserInfoView.as_view(), name='user_pwd_update_view'),
    path('delete/', views.UserInfoView.as_view(), name='user_info_delete_view'),
    path('qna/', views.QnaView.as_view(), name='qna_view'),
    path('pwd-reset/', views.PasswordResetView.as_view(), name='password_reset_view'),
]