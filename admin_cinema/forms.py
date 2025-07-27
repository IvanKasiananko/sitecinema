from cProfile import label
from email.policy import default

from django import forms
from django.db.models import TextField, CharField
from django.forms import modelformset_factory, inlineformset_factory
from django.templatetags.i18n import language
from pygame.cursors import sizer_y_strings

from cinema import models
from cinema.models import Image, Banner, User, BannerFon, Film, Seo, Cinema, About, Hall, Newsletter, Session

TYPE_CHOICES = [
    ('2D', '2D'),
    ('3D', '3D'),
    ('IMAX', 'IMAX'),
]

class CinemaAdressForm(forms.ModelForm):
    class Meta:
        model = Cinema
        fields = ['name_cinema', 'adress', 'coord', 'logo']
        labels = {
            'name_cinema': 'Название кинотеатра',
            'adress': 'Адрес',
            'coord': 'Координаты для карты',
            'logo': 'Лого',
        }
        # widgets = {
        #     'adress': forms.Textarea(attrs={'placeholder': 'Адрес'}),
        #     'coord': forms.TextInput(attrs={'placeholder': 'Координаты для карты'}),
        # }
        widgets = {
            'name_cinema': forms.TextInput(attrs={
                'style': 'width:400px;',  # задаёт ширину
                'placeholder': 'Введите название',
                # 'class': 'my-input',  # кастомный класс для CSS
            }),
            'adress': forms.Textarea(attrs={
                'style': 'width:800px; height:100px;',
                'placeholder': 'Введите адрес',
                # 'class': 'my-textarea',
            }),
            'coord': forms.TextInput(attrs={
                'style': 'width:400px;',
                'placeholder': 'Введите координаты',
                # 'class': 'my-input',
            }),
        }


class CinemaForm(forms.ModelForm):
    class Meta:
        model = Cinema
        fields = ['logo', 'name_cinema']

class CinemaAddForm(forms.ModelForm):
    language = forms.ChoiceField(  # это поле НЕ в модели
        choices=[('ru', 'Русский'), ('uk', 'Українська')],
        widget=forms.RadioSelect,
        required=False,
        initial='uk',
    )

    class Meta:
        model=Cinema
        fields = [
            'name_cinema_uk',
            'name_cinema_ru',
            'seo_text_uk',
            'seo_text_ru',
            'conditions_uk',
            'conditions_ru',
            'logo',
            'banner',
            'adress',
            'coord',
        ]
        widgets = {
            'seo_text_uk': forms.Textarea(attrs={'rows': 3}),
            'seo_text_ru': forms.Textarea(attrs={'rows': 3}),
            'conditions_uk': forms.Textarea(attrs={'rows': 3}),
            'conditions_ru': forms.Textarea(attrs={'rows': 3}),
            'logo': forms.FileInput(attrs={'class': 'hidden-input'}),
            'banner': forms.FileInput(attrs={'class': 'hidden-input'}),

        }


class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        exclude = ['cinema', 'seo', 'gall']


class FilmForm(forms.ModelForm):
    class Meta:
        model = Film
        fields = ['main_image', 'name']

class HallAddForm(forms.ModelForm):
    language = forms.ChoiceField(  # это поле НЕ в модели
        choices=[('ru', 'Русский'), ('uk', 'Українська')],
        widget=forms.RadioSelect,
        required=False,
        initial='uk',

    )
    class Meta:
        model=Hall
        fields=[
            'name_hall_uk',
            'name_hall_ru',
            'description_uk',
            'description_ru',
            'sheme',
            'banner',
        ]
        widgets = {
            'description_uk': forms.Textarea(attrs={'rows': 3}),
            'description_ru': forms.Textarea(attrs={'rows': 3}),
            'sheme': forms.FileInput(attrs={'class': 'hidden-input'}),
            'banner': forms.FileInput(attrs={'class': 'hidden-input'}),

        }

class SMSForm(forms.Form):
    sms_all_user = forms.ChoiceField(choices=[('all', 'Все пользователи'), ('choice', 'Выбранные')],
                                     widget=forms.RadioSelect)

    text_sms = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Введите текст SMS',
            'rows': 4,
            'style': 'width: 300px;',
            'class': 'form-control',
        }),
        label='Текст SMS',
        required=True,
    )

class EmailForm(forms.Form):
    email_all_user = forms.ChoiceField(
        choices=[('all', 'Все пользователи'), ('choice', 'Выбранные')],
        widget=forms.RadioSelect
    )
    selected_template = forms.IntegerField(required=True)

class FilmAddForm(forms.ModelForm):
    # Тип тут

    type_film = forms.MultipleChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Тип'
    )

    class Meta:
        model = Film
        fields = [
            'language',      # Можно оставить для справки или убрать, если не нужен
            'name_uk',       # Языковые поля, добавленные modeltranslation
            'name_ru',
            'description_uk',
            'description_ru',
            'main_image',
            'treiler_url',
            'start_date',
            'type_film',
        ]
        widgets = {
            'description_uk': forms.Textarea(attrs={'rows': 3}),
            'description_ru': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'language': forms.RadioSelect,
            'main_image': forms.FileInput(attrs={'class': 'hidden-input'}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # При загрузке формы преобразуем строку в список для поля MultipleChoiceField
        if self.instance and self.instance.pk and self.instance.type_film:
            self.initial['type_film'] = self.instance.type_film.split(',')

    def clean_type_film(self):
        data = self.cleaned_data.get('type_film')
        return ','.join(data) if data else ''


class SessionForm(forms.ModelForm):
    type_film = forms.ChoiceField(choices=TYPE_CHOICES, label='Тип фильма')

    cinema = forms.ModelChoiceField(
        queryset=Cinema.objects.all(),
        label='Кинотеатр',
        required=True
    )

    class Meta:
        model = Session
        fields = ['film', 'type_film', 'cinema', 'hall', 'price', 'date_session', 'time_session']
        widgets = {
            'date_session': forms.DateInput(attrs={'type': 'date'}),
            'time_session': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔷 Сначала список залов пустой или общий
        self.fields['hall'].queryset = Hall.objects.none()

        if 'cinema' in self.data:
            try:
                cinema_id = int(self.data.get('cinema'))
                self.fields['hall'].queryset = Hall.objects.filter(cinema_id=cinema_id).order_by('name_hall_uk')
            except (ValueError, TypeError):
                pass  # invalid input; ignore and fallback to empty
        elif self.instance.pk:
            self.fields['hall'].queryset = self.instance.cinema.hall_set.order_by('name_hall_uk')


class NewsActionAddForm(forms.ModelForm):
    LANGUAGE_CHOICES = [
        ('uk', 'Украинский'),
        ('ru', 'Русский'),
    ]
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        label='Моя радиокнопка',
        initial='uk',
    )

    class Meta:
        model = About
        fields = [
            'name',
            'publication',
            'date_publication',
            'name_about_uk',
            'name_about_ru',
            'description_uk',
            'description_ru',
            'main_image',
            'video_url',
            'cinema',
        ]
        widgets = {
            'description_uk': forms.Textarea(attrs={'rows': 3}),
            'description_ru': forms.Textarea(attrs={'rows': 3}),
            'date_publication': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'main_image': forms.FileInput(attrs={'class': 'hidden-input'}),

        }
        # exclude = ['cinema', 'seo', 'gall']






class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'hidden-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False


ImageFormSet = modelformset_factory(
    Image,
    form=ImageForm,
    extra=5,
    can_delete=True
)


class SeoForm(forms.ModelForm):
    class Meta:
        model = Seo
        fields = ['seo_url', 'seo_title', 'seo_keywords', 'seo_description']
        labels = {
            'seo_url': 'URL',
            'seo_title': 'Title',
            'seo_keywords': 'Keyword',
            'seo_description': 'Description',
        }


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['image_main', 'url_banner', 'text_banner']
        widgets = {
            'image_main': forms.FileInput(attrs={'accept': 'image/*'}),
            'url_banner': forms.URLInput(attrs={'class': 'small-input'}),
            'text_banner': forms.TextInput(attrs={'class': 'small-input'}),

        }


BannerFormSetMain = modelformset_factory(
    Banner, form=BannerForm, extra=1, can_delete=True
)

BannerFormSetAction = modelformset_factory(
    Banner, form=BannerForm, extra=1, can_delete=True
)


class BannerFonForm(forms.ModelForm):
    class Meta:
        model = BannerFon
        fields = ['image_back', 'fon']
        widgets = {
            'fon': forms.RadioSelect(choices=[(True, 'Фото на фон'), (False, 'Просто фон')]),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'adress', 'password', 'card_user',
                  'language', 'sex', 'phone_user', 'birthday', 'town']
        labels = {
            'first_name': 'Имя',
            "last_name": 'Фамилия',
            'username': 'Псевдоним',
            'adress': 'Адресс',
            'password': 'Пароль',
            'card_user': 'Номер карты',
            'language': 'Язык',
            'sex': 'Пол',
            'phone_user': 'Телефон',
            'birthday': 'День рождения',
            'town': 'Город',
        }

class Session(forms.ModelForm):

    class Meta:
        model=Session
        fields='__all__'

class UserAddForm(forms.ModelForm):
    CHOICES_SEX = (
        ("men", 'Мужской'),
        ("women", 'Женский'),
    )

    LANGUAGE_CHOICES = (
        (1, 'Украинский'),
        (2, 'Русский'),
    )

    TOWN_CHOICES = [
        ('kiev', 'Киев'),
        ('odessa', 'Одесса'),
        ('lviv', 'Львов'),
        ('donetsk', 'Донецк'),
        ('harkiv', 'Харьков'),
    ]

    sex = forms.ChoiceField(choices=CHOICES_SEX, widget=forms.RadioSelect)
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES, widget=forms.RadioSelect)
    town = forms.ChoiceField(choices=TOWN_CHOICES, widget=forms.Select, required=False)
    card_user = forms.CharField(max_length=19, widget=forms.TextInput(attrs={'placeholder': '**** **** **** ****'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}),
        label="Пароль"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Подтвердите пароль'}),
        label="Подтвердите пароль"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'adress', 'password', 'card_user',
                  'language', 'sex', 'phone_user', 'birthday', 'town']

        widgets = {
            'birthday': forms.SelectDateWidget(years=range(1900, 2025)),
            'password': forms.PasswordInput(),
        }

        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Псевдоним',
            'adress': 'Адрес',
            'password': 'Пароль',
            'card_user': 'Номер карты',
            'language': 'Язык',
            'sex': 'Пол',
            'phone_user': 'Телефон',
            'birthday': 'День рождения',
            'town': 'Город',
        }

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

