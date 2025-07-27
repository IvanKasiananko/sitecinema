
from celery import shared_task
from time import sleep

from django.core.mail import  EmailMessage

from sitecinema import settings




def send_sms(phone, text):
    print(f"📲 Отправка SMS на {phone}: {text}")

def send_email(email, subject, html_content):
    print(f"📲 Отправка Email1 на {email}: {html_content}")
    print(subject, html_content, email)
    email_msg = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.EMAIL_HOST_USER,
        to=[email],
    )
    email_msg.content_subtype = "html"  # чтобы письмо было в HTML
    email_msg.send()


@shared_task(bind=True)
def send_sms_task(self, phone, text):
    for i in range(5):
        sleep(1)  # симуляция отправки по частям
        self.update_state(state='PROGRESS', meta={'current': i+1, 'total': 5})
    send_sms(phone, text)
    print(f"SMS отправлено на {phone}: {text}")
    return {'status': 'SMS отправлено', 'phone': phone}

@shared_task(bind=True)
def send_bulk_sms_task(self, phones, text):

    total = len(phones)
    for i, phone in enumerate(phones, start=1):
        send_sms(phone, text)
        print(i)
        # Обновляем прогресс
        self.update_state(state='PROGRESS', meta={'current': i, 'total': total})
        sleep(1)
    return {'status': 'Все SMS отправлены', 'total': total}

@shared_task(bind=True)
def send_bulk_email_task(self, emails, subject, html_content):
    print(subject, html_content, emails)
    total = len(emails)
    print('gcgffghfhg')
    for i, email in enumerate(emails, start=1):
        print('gcgffghfhg')
        send_email(email, subject, html_content)  # функция отправки
        self.update_state(state='PROGRESS', meta={'current': i, 'total': total})
        sleep(1)
    return {'status': 'Все Email отправлены', 'total': total}