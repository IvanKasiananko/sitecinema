from datetime import timedelta
from math import trunc
import random

import requests
from ajax_datatable import AjaxDatatableView
from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
from django.forms import modelformset_factory, ChoiceField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.base import kwarg_re
from django.template.loader import render_to_string
from django.template.smartif import prefix
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET

from admin_cinema.tasks import send_bulk_sms_task, send_sms_task, send_bulk_email_task
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from datetime import datetime, timedelta, time
from django.views import View
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, FormView

import cinema
from admin_cinema.forms import BannerForm, UserAddForm, UserForm, BannerFormSetMain, BannerFormSetAction, FilmForm, \
    FilmAddForm, SeoForm, ImageFormSet, ImageForm, CinemaAddForm, NewsActionAddForm, HallAddForm, SMSForm, EmailForm, \
    SessionForm, CinemaAdressForm
from cinema.models import Banner, User, BannerFon, Gallery, Image, Film, Seo, Cinema, About, Hall, Newsletter, Session, \
    Price
import json

class CinemaAddView(CreateView):
    model = Cinema
    template_name = 'admin_cinema/create_cinema.html'
    form_class = CinemaAddForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')

        ImageFormSet = modelformset_factory(
            model=Image,
            form=ImageForm,
            extra=1,
            can_delete=True
        )

        context['seo_form'] = SeoForm(self.request.POST or None)
        context['image_formset'] = ImageFormSet(self.request.POST or None, self.request.FILES or None,
                                                queryset=Image.objects.none())
        context['form'] = form
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']

        if seo_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                seo = seo_form.save()

                gall = Gallery.objects.create(name=form.cleaned_data.get("name", "Cinema"))

                Cinema = form.save(commit=False)
                Cinema.seo = seo
                Cinema.gall = gall
                Cinema.save()

                images = image_formset.save(commit=False)
                for img in images:
                    img.gall = gall
                    img.save()

                return redirect('cinema_admin')
        return self.form_invalid(form)


class CinemaEditView(UpdateView):
    model = Cinema
    form_class = CinemaAddForm
    template_name = 'admin_cinema/create_cinema.html'
    context_object_name = 'cinema'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        cinema = self.object

        existing_count = cinema.gall.image_set.count()
        extra = max(0, 5 - existing_count)

        ImageFormSetDynamic = modelformset_factory(
            model=cinema.gall.image_set.model,
            form=ImageForm,
            extra=extra,
            can_delete=True,
        )

        if self.request.method == 'POST':
            context['seo_form'] = SeoForm(self.request.POST, instance=cinema.seo)
            context['image_formset'] = ImageFormSetDynamic(
                self.request.POST,
                self.request.FILES,
                queryset=cinema.gall.image_set.all()
            )
        else:
            context['seo_form'] = SeoForm(instance=cinema.seo)
            context['image_formset'] = ImageFormSetDynamic(
                queryset=cinema.gall.image_set.all()
            )

        context['form'] = form
        return context

    def form_valid(self, form):
        cinema = form.save(commit=False)
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']

        if seo_form.is_valid() and image_formset.is_valid():
            try:
                with transaction.atomic():
                    cinema.save()
                    seo = seo_form.save()
                    cinema.seo = seo
                    cinema.save()

                    images = image_formset.save(commit=False)
                    for image in images:
                        image.gall = cinema.gall
                        image.save()

                    for obj in image_formset.deleted_objects:
                        obj.delete()

                return redirect('cinema_admin')
            except Exception:
                return self.form_invalid(form)
        return self.form_invalid(form)


class BannerAddView(View):
    template_name = 'admin_cinema/banner.html'

    def get(self, request):
        BannerFormSet = modelformset_factory(
            Banner,
            fields=('image_main', 'url_banner', 'text_banner'),
            extra=1,
            can_delete=True
        )
        main_formset = BannerFormSet(
            queryset=Banner.objects.filter(name_page='Главная'),
            prefix='main'
        )
        action_formset = BannerFormSet(
            queryset=Banner.objects.filter(name_page='Акция'),
            prefix='action'
        )
        banner_fon = BannerFon.objects.first()  # одна запись с фоном

        speed_main = Banner.objects.filter(name_page='Главная').first()
        speed_action = Banner.objects.filter(name_page='Акция').first()

        context = {
            'main_formset': main_formset,
            'action_formset': action_formset,
            'speed_range': range(5, 16),
            'speed_main': speed_main.speed if speed_main else 5,
            'speed_action': speed_action.speed if speed_action else 5,
            'banner_fon': banner_fon,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        BannerFormSet = modelformset_factory(
            Banner,
            fields=('image_main', 'url_banner', 'text_banner'),
            extra=0,
            can_delete=True
        )

        # Обработка сохранения форм главной группы
        if 'save_main' in request.POST:
            formset = BannerFormSet(
                request.POST, request.FILES,
                queryset=Banner.objects.filter(name_page='Главная'),
                prefix='main'
            )
            speed_main = request.POST.get('speed_main', 5)
            if formset.is_valid():
                instances = formset.save(commit=False)
                for obj in formset.deleted_objects:
                    obj.delete()
                for instance in instances:
                    instance.name_page = 'Главная'
                    instance.speed = speed_main
                    instance.save()
                Banner.objects.filter(name_page='Главная').update(speed=speed_main)
            return redirect('banner')

        # Обработка сохранения форм акции
        elif 'save_action' in request.POST:
            formset = BannerFormSet(
                request.POST, request.FILES,
                queryset=Banner.objects.filter(name_page='Акция'),
                prefix='action'
            )
            speed_action = request.POST.get('speed_action', 5)
            if formset.is_valid():
                instances = formset.save(commit=False)
                for obj in formset.deleted_objects:
                    obj.delete()
                for instance in instances:
                    instance.name_page = 'Акция'
                    instance.speed = speed_action
                    instance.save()
                Banner.objects.filter(name_page='Акция').update(speed=speed_action)
            return redirect('banner')

        # Обработка фонового изображения
        elif 'submit_fon' in request.POST or 'delete_fon' in request.POST:
            banner_fon = BannerFon.objects.first()
            if 'submit_fon' in request.POST:
                # Добавить или обновить фон
                image_back = request.FILES.get('image_back')
                fon_value = request.POST.get('fon') == 'True'
                if banner_fon:
                    if image_back:
                        banner_fon.image_back = image_back
                    banner_fon.fon = fon_value
                    banner_fon.save()
                else:
                    BannerFon.objects.create(
                        image_back=image_back,
                        fon=fon_value
                    )
            elif 'delete_fon' in request.POST:
                # Удалить фон
                if banner_fon:
                    banner_fon.delete()
            return redirect('banner')

        # Если ничего не подошло — просто перерисовываем страницу
        return self.get(request)


class CinemaView(ListView):
    model = Cinema
    template_name = 'admin_cinema/cinema_admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now().date()
        context['all_cinema'] = Cinema.objects.all()
        return context


class FilmAddView(CreateView):
    model = Film
    form_class = FilmAddForm
    template_name = 'admin_cinema/create_film.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')

        ImageFormSet = modelformset_factory(
            model=Image,
            form=ImageForm,
            extra=1,
            can_delete=True
        )

        context['seo_form'] = SeoForm(self.request.POST or None)
        context['image_formset'] = ImageFormSet(self.request.POST or None, self.request.FILES or None,
                                                queryset=Image.objects.none())
        context['form'] = form
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']

        if seo_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                seo = seo_form.save()

                gall = Gallery.objects.create(name=form.cleaned_data.get("name", "Без названия"))

                film = form.save(commit=False)
                film.seo = seo
                film.gall = gall
                film.save()

                images = image_formset.save(commit=False)
                for img in images:
                    img.gall = gall
                    img.save()

                return redirect('film_admin')
        return self.form_invalid(form)


class HallAddView(CreateView):
    model = Hall
    form_class = HallAddForm
    template_name = 'admin_cinema/create_hall.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')

        ImageFormSet = modelformset_factory(
            model=Image,
            form=ImageForm,
            extra=1,
            can_delete=True
        )

        context['seo_form'] = SeoForm(self.request.POST or None)
        context['image_formset'] = ImageFormSet(self.request.POST or None, self.request.FILES or None,
                                                queryset=Image.objects.none())
        context['form'] = form
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']
        cinema_id = self.kwargs.get('pk')
        cinema = get_object_or_404(Cinema, id=cinema_id)

        if seo_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                seo = seo_form.save()

                gall = Gallery.objects.create(name=form.cleaned_data.get("name", "Hall"))

                hall = form.save(commit=False)
                hall.seo = seo
                hall.gall = gall
                hall.cinema = cinema
                hall.save()

                images = image_formset.save(commit=False)
                for img in images:
                    img.gall = gall
                    img.save()

                return redirect('cinema_admin')
        return self.form_invalid(form)


class HallEditView(UpdateView):
    model = Hall
    form_class = HallAddForm
    template_name = 'admin_cinema/create_hall.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ImageFormSet = modelformset_factory(
            model=Image,
            form=ImageForm,
            extra=1,
            can_delete=True,
        )

        # SEO форма с данными из текущего SEO или пустая
        seo_instance = self.object.seo if self.object else None
        context['seo_form'] = SeoForm(
            self.request.POST or None,
            instance=seo_instance
        )

        # Formset картинок галереи, если есть галерея у зала — грузим картинки
        if self.object and self.object.gall:
            qs = Image.objects.filter(gall=self.object.gall)
        else:
            qs = Image.objects.none()

        context['image_formset'] = ImageFormSet(
            self.request.POST or None,
            self.request.FILES or None,
            queryset=qs
        )

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']

        if seo_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                # Сохраняем SEO
                seo = seo_form.save(commit=False)
                seo.save()

                # Сохраняем зал, привязываем SEO
                hall = form.save(commit=False)
                hall.seo = seo

                # Если у зала нет галереи, создаём новую
                if not hall.gall:
                    hall.gall = Gallery.objects.create(name=hall.name_hall_uk or "Hall")

                hall.save()

                # Сохраняем картинки, привязываем к галерее
                images = image_formset.save(commit=False)
                for img in images:
                    img.gall = hall.gall
                    img.save()

                # Удаляем отмеченные для удаления картинки
                for img in image_formset.deleted_objects:
                    img.delete()

                # ✅ Получаем cinema и возвращаем на его редактирование
                cinema = hall.cinema
                return redirect('edit_cinema', pk=cinema.id)

        else:
            return self.render_to_response(
                self.get_context_data(form=form)
            )


class NewsActionAddView(CreateView):
    model = About
    form_class = NewsActionAddForm
    template_name = 'admin_cinema/create_news_action.html'

    def get_initial(self):
        initial = super().get_initial()
        name = self.request.GET.get('name')
        if name:
            initial['name'] = name
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ImageFormSet = modelformset_factory(
            model=Image,
            form=ImageForm,
            extra=5,
            can_delete=True
        )

        context['seo_form'] = SeoForm(self.request.POST or None)
        context['image_formset'] = ImageFormSet(
            self.request.POST or None,
            self.request.FILES or None,
            queryset=Image.objects.none()
        )

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']
        name = self.request.GET.get('name') or self.request.POST.get('name') or 'news'

        if seo_form.is_valid() and image_formset.is_valid():
            with transaction.atomic():
                seo = seo_form.save()

                name_value = form.cleaned_data.get("name") or "Без названия"
                gall = Gallery.objects.create(name=name_value)

                about = form.save(commit=False)
                about.seo = seo
                about.gall = gall
                about.save()

                images = image_formset.save(commit=False)
                for img in images:
                    img.gall = gall
                    img.save()

                # Редирект с учётом name
                return redirect(f'/admin/news/?name={name}')

        return self.form_invalid(form)

class NewsActionEditView(UpdateView):
    model = About
    form_class = NewsActionAddForm
    template_name = 'admin_cinema/create_news_action.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        news_action = self.object

        existing_count = news_action.gall.image_set.count()
        extra = max(0, 5 - existing_count)

        ImageFormSetDynamic = modelformset_factory(
            model=news_action.gall.image_set.model,
            form=ImageForm,
            extra=extra,
            can_delete=True,
        )

        if self.request.method == 'POST':
            context['seo_form'] = SeoForm(self.request.POST, instance=news_action.seo)
            context['image_formset'] = ImageFormSetDynamic(
                self.request.POST,
                self.request.FILES,
                queryset=news_action.gall.image_set.all()
            )
        else:
            context['seo_form'] = SeoForm(instance=news_action.seo)
            context['image_formset'] = ImageFormSetDynamic(
                queryset=news_action.gall.image_set.all()
            )

        context['form'] = form
        return context

    def form_valid(self, form):
        news_action = form.save(commit=False)
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']

        name = self.request.GET.get('name') or self.request.POST.get('name') or news_action.name or 'news'

        if seo_form.is_valid() and image_formset.is_valid():
            try:
                with transaction.atomic():
                    news_action.save()
                    seo = seo_form.save()
                    news_action.seo = seo
                    news_action.save()

                    images = image_formset.save(commit=False)
                    for image in images:
                        image.gall = news_action.gall
                        image.save()

                    for obj in image_formset.deleted_objects:
                        obj.delete()

                # Редирект с учётом name
                return redirect(f'/admin/news/?name={name}')

            except Exception:
                return self.form_invalid(form)

        return self.form_invalid(form)

class FilmEditView(UpdateView):
    model = Film
    form_class = FilmAddForm
    template_name = 'admin_cinema/create_film.html'
    context_object_name = 'film'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        film = self.object

        existing_count = film.gall.image_set.count()
        extra = max(0, 5 - existing_count)

        ImageFormSetDynamic = modelformset_factory(
            model=film.gall.image_set.model,
            form=ImageForm,
            extra=extra,
            can_delete=True,
        )

        if self.request.method == 'POST':
            context['seo_form'] = SeoForm(self.request.POST, instance=film.seo)
            context['image_formset'] = ImageFormSetDynamic(
                self.request.POST,
                self.request.FILES,
                queryset=film.gall.image_set.all()
            )
        else:
            context['seo_form'] = SeoForm(instance=film.seo)
            context['image_formset'] = ImageFormSetDynamic(
                queryset=film.gall.image_set.all()
            )

        context['form'] = form
        return context

    def form_valid(self, form):
        film = form.save(commit=False)
        context = self.get_context_data()
        seo_form = context['seo_form']
        image_formset = context['image_formset']

        if seo_form.is_valid() and image_formset.is_valid():
            try:
                with transaction.atomic():
                    film.save()
                    seo = seo_form.save()
                    film.seo = seo
                    film.save()

                    images = image_formset.save(commit=False)
                    for image in images:
                        image.gall = film.gall
                        image.save()

                    for obj in image_formset.deleted_objects:
                        obj.delete()

                return redirect('film_admin')
            except Exception:
                return self.form_invalid(form)
        return self.form_invalid(form)


class FilmView(ListView):
    model = Film
    template_name = 'admin_cinema/film_admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now().date()
        context['current_films'] = Film.objects.filter(start_date__lte=today)
        context['upcoming_films'] = Film.objects.filter(start_date__gt=today)
        return context

class SessionCreateView(CreateView):
    model = Session
    form_class = SessionForm
    template_name = 'admin_cinema/create_session.html'
    success_url = reverse_lazy('create_session')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = Session.objects.select_related(
            'film',
            'hall__cinema',
            'price'
        ).order_by('date_session', 'time_session')
        return context

class GenerateSessionsView(View):
    def post(self, request):
        count = int(request.POST.get('count', 0))
        generated = 0

        films = list(Film.objects.all())
        cinemas = list(Cinema.objects.all())
        halls = list(Hall.objects.select_related('cinema'))
        prices = list(Price.objects.all())  # если цена выбирается рандомно

        if not films or not cinemas or not halls:
            return JsonResponse({'error': 'Нет данных для генерации сеансов'}, status=400)

        # создаём даты на 5 дней вперёд начиная с сегодня
        dates = [timezone.now().date() + timedelta(days=i) for i in range(5)]
        # создаём список возможных времён (каждые 30 мин с 10:00 до 23:00)
        times = [time(hour=h, minute=m) for h in range(10, 24) for m in (0,30)]

        type_choices = ['2D', '3D', 'IMAX']

        attempts = 0
        max_attempts = count * 5  # чтобы избежать вечного цикла при заполненной сетке

        while generated < count and attempts < max_attempts:
            film = random.choice(films)
            hall = random.choice(halls)
            date_session = random.choice(dates)
            time_session = random.choice(times)
            type_film = random.choice(type_choices)
            price = random.choice(prices)

            # проверяем дубликаты: нет ли такого сеанса в зале на ту же дату и время
            exists = Session.objects.filter(
                hall=hall,
                date_session=date_session,
                time_session=time_session
            ).exists()

            if not exists:
                Session.objects.create(
                    film=film,
                    hall=hall,
                    date_session=date_session,
                    time_session=time_session,
                    type_film=type_film,
                    price=price
                )
                generated += 1

            attempts += 1

        return JsonResponse({'generated': generated})



@require_GET
def load_halls(request):
    cinema_id = request.GET.get('cinema_id')
    halls = Hall.objects.filter(cinema_id=cinema_id).order_by('name_hall_uk')
    return render(request, 'admin_cinema/hall_dropdown_list_options.html', {'halls': halls})

class UserAddView(CreateView):
    form_class = UserAddForm
    template_name = 'admin_cinema/useradd.html'
    success_url = reverse_lazy('user')  # или нужный URL после регистрации

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        login(self.request, user)
        return super().form_valid(form)


class UserEditView(UpdateView):
    model = User
    form_class = UserAddForm
    # fields = ['first_name', 'last_name', 'username', 'email', 'adress', 'password', 'card_user',
    #           'language', 'sex', 'phone_user', 'birthday', 'town']
    template_name = 'admin_cinema/useradd.html'
    success_url = reverse_lazy('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context




class UserJsonView(View):
    def get(self, request):
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))
        search_value = request.GET.get("search[value]", "")

        order_column_index = request.GET.get('order[0][column]', 0)
        order_column = request.GET.get(f'columns[{order_column_index}][name]', 'id')
        order_dir = request.GET.get('order[0][dir]', 'asc')

        queryset = User.objects.all()

        if search_value:
            queryset = queryset.filter(
                Q(username__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(town__icontains=search_value) |
                Q(first_name__icontains=search_value) |
                Q(last_name__icontains=search_value)
            )

        total = queryset.count()

        if order_column == 'full_name':
            queryset = queryset.order_by(
                '-first_name' if order_dir == 'desc' else 'first_name',
                '-last_name' if order_dir == 'desc' else 'last_name',
            )
        else:
            if order_dir == 'desc':
                order_column = f'-{order_column}'
            queryset = queryset.order_by(order_column)

        paginator = Paginator(queryset, length)
        page_number = start // length + 1
        page = paginator.get_page(page_number)

        data = []
        for user in page:
            edit_url = f"/admin/user_edit/{user.id}/"
            delete_button = f'<a href="#" class="delete-news" data-id="{user.id}" title="Удалить">🗑️</a>'
            edit_button = f'<a href="{edit_url}" title="Редактировать">✏️</a>'
            actions = f'{edit_button}&nbsp;{delete_button}'

            data.append({
                "id": user.id,
                "registration_date": user.registration_date.strftime("%Y-%m-%d") if user.registration_date else "",
                "birthday": user.birthday.strftime("%Y-%m-%d") if user.birthday else "",
                "email": user.email,
                "phone_user": getattr(user, 'phone_user', ''),
                "full_name": f"{user.first_name} {user.last_name}",
                "username": user.username,
                "town": user.town,
                "actions": actions,
            })

        return JsonResponse({
            "draw": draw,
            "recordsTotal": total,
            "recordsFiltered": queryset.count(),
            "data": data
        })



class LetterUserAjaxView(AjaxDatatableView):
    model = User
    title = "Выбор пользователей"
    initial_order = [["date_joined", "desc"]]

    column_defs = [
        {'name': 'checkbox', 'title': '', 'orderable': False, 'searchable': False},
        {'name': 'date_joined', 'title': 'Дата регистрации', 'orderable': True, 'searchable': False},
        {'name': 'birthday', 'title': 'День рождения', 'orderable': True, 'searchable': False},
        {'name': 'username', 'orderable': True, 'searchable': True},
        {'name': 'email', 'orderable': True, 'searchable': True},
        {'name': 'phone_user', 'orderable': True, 'searchable': True},
        {'name': 'first_name', 'orderable': True, 'searchable': True},
        {'name': 'last_name', 'orderable': True, 'searchable': True},
        {'name': 'town', 'orderable': True, 'searchable': True},
    ]

    def render_column(self, row, column):
        if column == 'checkbox':
            return f'<input type="checkbox" class="user-checkbox" value="{row.pk}" data-username="{row.username}">'
        return super().render_column(row, column)


def select_users(request):
    return render(request, 'admin_cinema/letter_user.html')


class UserView(TemplateView):
    template_name = 'admin_cinema/user.html'


class UserDeleteView(View):
    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'ID не указан'})

        try:
            user = User.objects.get(pk=user_id)
            user.delete()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Пользователь не найден'})





class NewsletterView(View):
    def get(self, request):
        sms_form = SMSForm()
        email_form = EmailForm()
        latest_templates = Newsletter.objects.order_by('-id')[:5]
        return render(request, 'admin_cinema/newsletter.html', {
            'sms_form': sms_form,
            'email_form': email_form,
            'latest_templates': latest_templates,
        })

    def post(self, request):
        print(request.POST)
        sms_form = SMSForm(request.POST)
        email_form = EmailForm(request.POST, request.FILES)
        latest_templates = Newsletter.objects.order_by('-id')[:5]

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        print(f"is_ajax: {is_ajax}")

        # --- Отправка SMS ---
        if 'send_sms' in request.POST:
            print("Обработка SMS формы")
            if sms_form.is_valid():
                user_ids = request.POST.getlist('sms_selected_users')
                users = User.objects.filter(id__in=user_ids)
                all_users = sms_form.cleaned_data.get('sms_all_user')
                message = sms_form.cleaned_data.get('text_sms')

                print(f"all_users: {all_users}, выбранные: {users}")

                if not all_users and not users:
                    if is_ajax:
                        return JsonResponse({'error': 'Нет выбранных пользователей'}, status=400)
                    messages.warning(request, "Выберите получателей для SMS")
                    return render(request, 'admin_cinema/newsletter.html', {
                        'sms_form': sms_form,
                        'email_form': email_form,
                        'latest_templates': latest_templates
                    })

                recipients = (
                    list(users.values_list('phone_user', flat=True))
                    if all_users == 'choice'
                    else list(User.objects.values_list('phone_user', flat=True))
                )
                print(f"Отправка SMS {len(recipients)} получателям")

                task = send_bulk_sms_task.delay(recipients, message)
                return JsonResponse({'task_id': task.id})
            else:
                print("SMS форма невалидна")
                if is_ajax:
                    return JsonResponse({'error': 'Форма SMS невалидна'}, status=400)
                messages.error(request, "Форма SMS заполнена неверно")

        # --- Отправка Email ---
        if 'send_email' in request.POST:
            if email_form.is_valid():
                user_choice = email_form.cleaned_data.get('email_all_user')  # значение радиокнопки
                if user_choice == 'all':
                    users = User.objects.all()
                else:
                    user_ids = request.POST.getlist('email_selected_users')
                    users = User.objects.filter(id__in=user_ids)

                emails = users.values_list('email', flat=True)
                subject = email_form.cleaned_data.get('subject')
                html_content = email_form.cleaned_data.get('html_content')

                # Запускаем таск отправки email с Celery

                task = send_bulk_email_task.delay(list(emails), subject, html_content)
                return JsonResponse({'task_id': task.id})
            else:
                if is_ajax:
                    return JsonResponse({'error': 'Форма email невалидна'}, status=400)
                messages.error(request, "Ошибка в email-форме")

        return render(request, 'admin_cinema/newsletter.html', {
            'sms_form': sms_form,
            'email_form': email_form,
            'latest_templates': latest_templates
        })




@require_GET
def task_status(request, task_id):
    result = AsyncResult(task_id)
    if result.state == 'PROGRESS':
        data = result.info or {}
        return JsonResponse({'state': result.state, 'current': data.get('current', 0), 'total': data.get('total', 1)})
    elif result.state == 'SUCCESS':
        return JsonResponse({'state': result.state, 'result': result.result})
    else:
        return JsonResponse({'state': result.state})

@csrf_exempt
def delete_template_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            template_id = data.get('id')
            if template_id is None:
                return JsonResponse({'success': False, 'error': 'No id provided'})

            deleted, _ = Newsletter.objects.filter(id=template_id).delete()
            if deleted:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def upload_template(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        instance = Newsletter.objects.create(
            name_template=file.name,
            path_template=file
        )
        latest = Newsletter.objects.order_by('-id')[:5]
        templates = [{"id": t.id, "name_template": t.name_template} for t in latest]
        return JsonResponse({"success": True, "templates": templates})
    return JsonResponse({"success": False})


def get_ordering(self):
    sort = self.request.GET.get('sort', 'username')  # значение из ?sort=
    allowed = ['username', '-username', 'email', '-email', 'id', '-id',
               'birthday', '-birthday', 'last_name', '-last_name', 'town', '-town',
               'registration_date', '-registration_date ',
               'user_phone', '-user_phone']
    return sort if sort in allowed else 'username'



def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['columns'] = [
        {'label': 'ID', 'field': 'id'},
        {'label': 'Дата регистрации', 'field': 'registration_date'},
        {'label': 'День рождения', 'field': 'birthday'},
        {'label': 'Email', 'field': 'email'},
        {'label': 'Телефон', 'field': 'phone_user'},
        {'label': 'ФИО', 'field': 'lastname'},
        {'label': 'Псевдоним ', 'field': 'username'},
        {'label': 'Город', 'field': 'town'},
    ]
    context['current_sort'] = self.request.GET.get('sort', '')
    context['query_string'] = self.request.GET.copy()
    if 'page' in context['query_string']:
        del context['query_string']['page']
    return context

#Статистика по городам
def dash_town(request):
    data=User.objects.values('town').annotate(total=Count('id')).order_by('-total')
    labels=[]
    counts=[]
    for item in data:
        labels.append(item['town'])
        counts.append(item['total'])
    return JsonResponse({
        'labels': labels,
        'counts': counts
    })

#Статистика по фильму
def dash_film(request):
    date = Film.objects.annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')
    labels=[]
    counts=[]
    for item in date:
        labels.append(item['month'].strftime('%Y-%m'))
        counts.append(item['total'])
    return JsonResponse({
        'labels':labels,
        'counts':counts

    })

def dashboard(request):
    return render(request, 'admin_cinema/dashboard.html')

def hall_data(request):
    cinema_id = request.GET.get('cinema_id')  # Получаем cinema_id из GET
    hall_list = Hall.objects.filter(cinema_id=cinema_id).order_by('-date_create')
    data = []
    print(cinema_id)
    for hall in hall_list:
        data.append({
            'id': hall.id,
            'name_hall': hall.name_hall,
            'date_create': hall.date_create.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({'data': data})


def news_data(request):
    category = request.GET.get('name')  # получаем параметр из URL, например ?name=news

    if category not in ['news', 'action', 'pages']:
        return JsonResponse({'error': 'Invalid category'}, status=400)

    news_list = About.objects.filter(name=category).order_by('date_create')
    data = []
    for news in news_list:
        data.append({
            'id': news.id,
            'name_about': news.name_about,
            'date_create': news.date_create.strftime('%Y-%m-%d %H:%M'),
            'status': 'Активна' if news.publication else 'Неактивна',
        })

    return JsonResponse({'data': data})


def hall_delete(request, pk):
    if request.method == 'POST':
        try:
            hall = Hall.objects.get(id=pk)
            hall.delete()
            return JsonResponse({'success': True})
        except Hall.DoesNotExist:
            return JsonResponse({'error': 'Зал не найден'}, status=404)
    return JsonResponse({'error': 'Метод не разрешён'}, status=405)


def news_page(request):
    name = request.GET.get('name', 'news')
    return render(request, 'admin_cinema/news.html', {
        'name': name,
        'edit_url_base': '/admin/news_action/'
    })


def news_action_delete(request, pk):
    if request.method == 'POST':
        try:
            about = About.objects.get(pk=pk)

            # Удаляем все изображения из галереи
            about.gall.image_set.all().delete()

            # Удаляем галерею
            about.gall.delete()

            # Удаляем seo
            about.seo.delete()

            # Удаляем сам About
            about.delete()

            return JsonResponse({'success': True})
        except About.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Not found'}, status=404)

class CinemaAdressView(View):
    template_name = 'admin_cinema/cinema_adress.html'

    def get(self, request):
        cinemas = Cinema.objects.all()
        cinema_forms = []

        for idx, c in enumerate(cinemas):
            form = CinemaAdressForm(instance=c, prefix=f'cinema-{idx}')
            seo_form = SeoForm(instance=c.seo if c.seo else None, prefix=f'seo-{idx}')
            cinema_forms.append((form, seo_form, c))

        context = {
            'cinema_forms': cinema_forms,
            'total_forms': len(cinema_forms),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        total_forms = int(request.POST.get('form-TOTAL_FORMS', 0))

        for i in range(total_forms):
            # получаем id кинотеатра из скрытого input
            cinema_id = request.POST.get(f'cinema-{i}-id')
            cinema_instance = Cinema.objects.get(id=cinema_id) if cinema_id else None

            # создаём форму кинотеатра с данными POST
            cinema_form = CinemaAdressForm(request.POST, request.FILES, prefix=f'cinema-{i}', instance=cinema_instance)

            # создаём SEO форму только для валидации (instance берётся, если есть)
            seo_form = SeoForm(request.POST, prefix=f'seo-{i}', instance=cinema_instance.seo if cinema_instance and cinema_instance.seo else None)

            print(f"Processing form {i}")
            print("cinema_form valid:", cinema_form.is_valid())
            print(cinema_form.errors)
            print("seo_form valid:", seo_form.is_valid())
            print(seo_form.errors)

            if cinema_form.is_valid():
                cinema = cinema_form.save()

                # ✅ Сохраняем SEO только при СОЗДАНИИ нового кинотеатра
                if not cinema_instance:
                    if seo_form.is_valid():
                        seo_instance = seo_form.save()
                        cinema.seo = seo_instance
                        cinema.save()

        # после сохранения перенаправляем на эту же страницу
        return redirect('cinema_adress')









# Create your views here.
def index(request):
    data = {
        'title': 'Главное меню',

    }

    return render(request, 'admin_cinema/index2.html', context=data)


def hall(request):
    return render(request, 'admin_cinema/hall.html')


def cinema_card(request):
    return render(request, 'admin_cinema/cinema_card.html')


def news(request):
    return render(request, 'admin_cinema/news.html')


def create_news(request):
    return render(request, 'admin_cinema/create_news.html')




def action(request):
    return render(request, 'admin_cinema/action.html')


def hall_editor(request):
    return render(request, 'admin_cinema/hall_editor.html')




def create_news_action(request):
    return render(request, 'admin_cinema/create_news_action.html')


def user(request):
    return render(request, 'admin_cinema/user.html')


def edit_user(request):
    return render(request, 'admin_cinema/create_hall.html')


def newsletter(request):
    return render(request, 'admin_cinema/newsletter.html')


def letter_user(request):
    return render(request, 'admin_cinema/letter_user.html')


def statistic(request):
    return render(request, 'admin_cinema/statistic.html')


def main_page(request):
    return render(request, 'admin_cinema/main_page.html')


def delete(request):
    return render(request, 'admin_cinema/banner.html')


def pages(request, post_id):
    menu = {
        "nomer": post_id,
    }

    data = {
        "1": "Главная страница",
        "2": "Новости",
        '3': 'Кафе-бар',
        '4': 'VIP-зал',
        '5': 'Реклама',
        '6': 'Детская комната',
        '7': 'Контакты',
    }
    name = data[str(post_id)]

    return render(request, 'admin_cinema/pages.html', {'title': name})
