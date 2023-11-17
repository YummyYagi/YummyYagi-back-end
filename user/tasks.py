from celery import shared_task
from django.core.mail import send_mail


@shared_task                                                                                # '@shared_task' : Django에서 Celery 작업을 정의하는 데 사용되는 데코레이터입니다. Celery를 통해 백그라운드에서 실행되어야 하는 비동기 작업을 만들 때 사용됩니다.
def send_verification_email(user_id, verification_url, recipient_email):                    # 이 작업은 Celery worker에서 실행될 때 백그라운드에서 비동기로 실행됩니다. 
    subject = '이메일 확인 링크'
    message = f'이메일 확인을 완료하려면 다음 링크를 클릭하세요: {verification_url}'
    from_email = 'yammyyagi@gmail.com'
    print(f'subject:{subject}')
    send_mail(subject, message, from_email, [recipient_email])
    
    
@shared_task
def send_verification_email_for_pw(user_id, verification_url, recipient_email):
    subject = '이메일 확인 링크'
    message = f'이메일 확인을 완료하려면 다음 링크를 클릭하세요: {verification_url}'
    from_email = 'yammyyagi@gmail.com'
    print(f'subject:{subject}')
    send_mail(subject, message, from_email, [recipient_email])


@shared_task
def send_email_with_pw(user_id, temp_password, recipient_email):
    subject = '임시 비밀번호 발급'
    message = f'임시 비밀번호: {temp_password}'
    from_email = 'yammyyagi@gmail.com'
    print(f'subject:{subject}')
    send_mail(subject, message, from_email, [recipient_email])