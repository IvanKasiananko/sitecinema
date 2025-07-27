from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CASCADE, URLField, TextField, SlugField
from django.forms import CharField
from django.utils import timezone


class Price(models.Model):
    price1=models.FloatField(max_length=10)
    price2 = models.FloatField(max_length=10)
    vip_price = models.FloatField(max_length=10)


    def __str__(self):
        return f"{self.price1} грн"

class Gallery(models.Model):
    name=models.CharField(max_length=20)

class Image(models.Model):
    image=models.ImageField(upload_to='photos/')
    gall=models.ForeignKey('Gallery',on_delete=CASCADE)

class Seo(models.Model):
    seo_url=models.URLField()
    seo_title=models.CharField(max_length=100)
    seo_keywords=models.CharField(max_length=100)
    seo_description=models.TextField()

class Hall(models.Model):
    name_hall=models.CharField(max_length=100)
    description=models.TextField()
    sheme=models.ImageField(upload_to='photos/')
    banner=models.ImageField(upload_to='photos/')
    row=models.PositiveIntegerField(default=10)
    col=models.PositiveIntegerField(default=10)
    cinema = models.ForeignKey('Cinema', on_delete=CASCADE)
    date_create = models.DateTimeField(default=timezone.now)
    seo=models.ForeignKey('Seo',on_delete=CASCADE)
    gall=models.ForeignKey('Gallery',on_delete=CASCADE)


    def __str__(self):
        return self.name_hall


class Cinema(models.Model):
    name_cinema=models.CharField(max_length=100)
    phone_num1=models.SlugField(max_length=15)
    phone_num2 = models.SlugField(max_length=15)
    seo_text=models.TextField()
    conditions=models.TextField(default=" ")
    adress=models.TextField()
    coord=models.URLField(max_length=450)
    logo=models.ImageField(upload_to='photos/')
    banner = models.ImageField(upload_to='photos/')
    seo = models.ForeignKey('Seo', on_delete=CASCADE,null=True, blank=True)
    gall = models.ForeignKey('Gallery', on_delete=CASCADE,null=True, blank=True)
    def __str__(self):
        return self.name_cinema

class Film(models.Model):
    LANGUAGE_CHOICES = [
        ('uk', 'Украинский'),
        ('ru', 'Русский'),
    ]
    name=models.CharField(max_length=150)
    description=models.TextField()
    main_image=models.ImageField(upload_to='photos/')
    treiler_url=models.URLField()
    start_date=models.DateField()
    type_film=models.CharField(max_length=200)
    seo = models.ForeignKey('Seo', on_delete=CASCADE)
    gall = models.ForeignKey('Gallery', on_delete=CASCADE)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='uk')

    def __str__(self):
        return self.name

class Session(models.Model):
    date_session=models.DateField(null=True, blank=True)
    time_session=models.TimeField(null=True, blank=True)
    type_film = models.CharField(max_length=200)
    film = models.ForeignKey('Film', on_delete=CASCADE)
    hall= models.ForeignKey('Hall', on_delete=CASCADE,null=True, blank=True)
    price = models.ForeignKey('Price', on_delete=CASCADE,null=True, blank=True)


    def save(self, *args, **kwargs):
        is_new = self.pk is None  # True, если объект ещё не в базе (новый сеанс)
        super().save(*args, **kwargs)  # Сохраняем сеанс

        if is_new:
            hall = self.hall
            for r in range(1, hall.row + 1):
                for c in range(1, hall.col + 1):
                    Ticket.objects.create(
                        row=r,
                        place=c,
                        session=self,
                        status='free'
                    )


class About(models.Model):
    name=models.CharField(max_length=100, null=True, blank=True)
    name_about=models.CharField(max_length=100)
    date_create=models.DateTimeField(default=timezone.now)
    date_publication=models.DateField()
    publication=models.BooleanField(default=False)
    description=models.TextField()
    main_image=models.ImageField(upload_to='photos/')
    video_url=models.URLField()
    cinema = models.ForeignKey('Cinema', on_delete=CASCADE)
    seo = models.ForeignKey('Seo', on_delete=CASCADE)
    gall = models.ForeignKey('Gallery', on_delete=CASCADE)

class BannerFon(models.Model):
    image_back=models.ImageField(upload_to='photos/',blank=True, null=True)
    fon=models.BooleanField()

class Banner(models.Model):
    name_page = models.CharField(max_length=100, choices=[('Главная', 'Главная'), ('Акция', 'Акция')])
    image_main = models.ImageField(upload_to='banners/')
    url_banner = models.URLField(blank=True, null=True)
    text_banner = models.CharField(max_length=255, blank=True, null=True)
    speed = models.IntegerField(default=5)

class Ticket(models.Model):
    row=models.PositiveIntegerField()
    place=models.PositiveIntegerField()
    session = models.ForeignKey('Session', on_delete=CASCADE)
    user = models.ForeignKey('User', on_delete=CASCADE, null=True, blank=True)
    STATUS_CHOICES = [
        ('free', 'Свободно'),
        ('booked', 'Забронировано'),
        ('bought', 'Куплено'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='free')


class User(AbstractUser):
    registration_date=models.DateField(auto_now_add=True)
    town=models.CharField(max_length=100)
    adress=models.CharField(max_length=200)
    phone_user=models.SlugField(max_length=15)
    card_user=models.CharField(max_length=20)
    birthday=models.DateField()
    sex=models.CharField(max_length=10)
    language=models.CharField(max_length=15)

class Newsletter(models.Model):
    name_template=models.CharField()
    path_template=models.FileField(upload_to='sample/',verbose_name="Загрузить HTML-письмо ")