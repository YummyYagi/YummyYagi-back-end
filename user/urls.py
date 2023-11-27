from django.urls import path
from user import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register_view'),
    path('verify-email/<str:uidb64>/<str:token>/', views.VerifyEmailView.as_view(), name='verify_email_view'),
    path('login/', views.LoginView.as_view(), name='login_view'),
    
    path('social-register/', views.SocialRegisterView.as_view(), name='social_register_view'),
    path('social/', views.SocialUrlView.as_view(), name='social_login'),
    path('kakao/', views.KakaoLoginView.as_view(), name='kakao_login'),
    
    path('mypage/', views.MyPageView.as_view(), name='mypage_view'),
    path('info/', views.UserInfoView.as_view(), name='user_info_view'),
    
    path('qna/', views.QnaView.as_view(), name='qna_view'),
    path('pwd-reset/', views.PasswordResetView.as_view(), name='password_reset_view'),
    
    path('verify-email-for-pw/<str:uidb64>/<str:token>/', views.SendRandomPassword.as_view(), name='send_random_password_view'),

    path('payment-page/', views.PaymentPageView.as_view(), name='payment_page_view'),
    path('payment-result/', views.PaymentResult.as_view(), name='payment_result_view'),
]