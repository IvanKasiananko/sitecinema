from collections import defaultdict
import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils import timezone, translation

from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.timezone import localdate, now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, ListView, DetailView

from cinema.models import Film, BannerFon, Session, Hall, Price, Cinema, Banner, About, Ticket, Image


# Create your views here.
class CinemaView(ListView):
    model = Cinema
    template_name = 'cinema/cinema.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get('lang', 'uk')
        translation.activate(lang)
        context['lang'] = lang  # нужно для выделения в <select>

        context['all_cinema'] = Cinema.objects.all()
        context['side_banners'] = Banner.objects.all()[:3]
        return context

class CinemaDetailView(TemplateView):
    template_name = 'cinema/cinema_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cinema_id = self.kwargs.get('pk')
        cinema = get_object_or_404(Cinema, id=cinema_id)
        today = timezone.now().date()

        halls = Hall.objects.filter(cinema=cinema)
        sessions_today = Session.objects.filter(hall__cinema=cinema, date_session=today).order_by('time_session')
        banners = Banner.objects.all()  # если есть общая модель баннеров
        context['halls'] = Hall.objects.all()
        print(banners)
        context['today_sessions'] = Session.objects.filter(date_session=timezone.now().date())
        context.update({
            'cinema': cinema,
            'halls': halls,
            'sessions_today': sessions_today,
            'banners': banners,
            'today': today,
        })
        return context



class HallDetailView(TemplateView):
    template_name = 'cinema/hall_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hall_id = self.kwargs.get('pk')
        hall = get_object_or_404(Hall, id=hall_id)

        today = timezone.now().date()
        sessions_today = Session.objects.filter(hall=hall, date_session=today).order_by('time_session')

        context.update({
            'hall': hall,
            'sessions_today': sessions_today,
            'today': today,
        })
        return context

class ActionsView(View):
    template_name = 'cinema/actions.html'

    def get(self, request, category):
        promotions = About.objects.filter(name=category, publication=True).order_by('-date_publication')

        main_banner = Banner.objects.first().image_main if Banner.objects.exists() else None

        side_banners = list(Banner.objects.all()[:3])
        while len(side_banners) < 3:
            side_banners.append(None)

        context = {
            'promotions': promotions,
            'main_banner': main_banner,
            'side_banners': side_banners,
            'category': category,
        }
        return render(request, self.template_name, context)



class ActionDetailView(TemplateView):
    template_name = 'cinema/action_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action_id = self.kwargs.get('pk')
        action = get_object_or_404(About, id=action_id)
        side_banners = Banner.objects.all()[:3]

        placeholders_needed = max(0, 3 - side_banners.count())

        context.update({
            'action': action,
            'side_banners': side_banners,
            'placeholders_needed': range(placeholders_needed),
        })
        return context


class FilmView(TemplateView):
    template_name = 'cinema/main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        lang = self.request.GET.get('lang', 'uk')
        translation.activate(lang)
        context['lang'] = lang  # нужно для выделения в <select>

        today = timezone.now().date()
        context['today'] = today
        context['today_films'] = Film.objects.filter(start_date__lte=today)
        context['coming_soon_films'] = Film.objects.filter(start_date__gt=today).order_by('start_date')

        #  фон
        banner_fon = BannerFon.objects.filter(fon=True).first()
        context['banner_fon'] = banner_fon

        return context

class FilmsPageView(TemplateView):
    template_name = 'cinema/poster.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        category = self.kwargs.get('category')

        if category == 'current':
            films = Film.objects.filter(start_date__lte=today).order_by('start_date')
        elif category == 'coming':
            films = Film.objects.filter(start_date__gt=today).order_by('start_date')
        else:
            films = Film.objects.none()  # если категория некорректна

        context.update({
            'today': today,
            'category': category,
            'films': films,
        })
        return context


class ScheduleView(TemplateView):
    template_name = 'cinema/schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        lang = self.request.GET.get('lang', 'uk')
        translation.activate(lang)
        context['lang'] = lang
        cinema_id = self.request.GET.get('cinema')
        date = self.request.GET.get('date')
        film_id = self.request.GET.get('film')
        hall_id = self.request.GET.get('hall')

        sessions = Session.objects.select_related('film', 'hall', 'hall__cinema', 'price').all()

        if cinema_id:
            sessions = sessions.filter(hall__cinema_id=cinema_id)
        if date:
            sessions = sessions.filter(date_session=date)
        if film_id:
            sessions = sessions.filter(film_id=film_id)
        if hall_id:
            sessions = sessions.filter(hall_id=hall_id)

        sessions_by_date = defaultdict(list)
        for s in sessions.order_by('date_session', 'time_session'):
            sessions_by_date[s.date_session].append(s)

        context.update({
            'sessions_by_date': sorted(sessions_by_date.items()),
            'cinemas': Cinema.objects.all(),
            'films': Film.objects.all(),
            'halls': Hall.objects.all(),
            'selected_cinema': int(cinema_id) if cinema_id and cinema_id.isdigit() else None,
            'selected_date': date,
            'selected_film': int(film_id) if film_id and film_id.isdigit() else None,
            'selected_hall': int(hall_id) if hall_id and hall_id.isdigit() else None,
        })

        return context

class HallsByCinemaView(View):
    def get(self, request):
        cinema_id = request.GET.get('cinema_id')
        if not cinema_id:
            return JsonResponse({'halls': []})

        halls = Hall.objects.filter(cinema_id=cinema_id).values('id', 'name')
        halls_list = list(halls)
        return JsonResponse({'halls': halls_list})

class FilmDetailView(TemplateView):
    template_name = 'cinema/film_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # активация языка
        lang = self.request.GET.get('lang', 'ru')
        translation.activate(lang)
        context['lang'] = lang

        film_id = self.kwargs.get('pk')
        film = get_object_or_404(Film, id=film_id)

        # получаем связанные изображения галереи фильма
        gallery_images = Image.objects.filter(gall=film.gall)

        cinemas = Cinema.objects.all()

        selected_cinema = self.request.GET.get('cinema')
        selected_types = self.request.GET.getlist('type')

        sessions = Session.objects.filter(film=film)

        if selected_cinema:
            sessions = sessions.filter(hall__cinema_id=selected_cinema)

        if selected_types:
            sessions = sessions.filter(type_film__in=selected_types)

        sessions_by_date = defaultdict(list)
        for s in sessions.order_by('date_session', 'time_session'):
            sessions_by_date[s.date_session].append(s)

        context.update({
            'film': film,
            'cinemas': cinemas,
            'sessions_by_date': sessions_by_date.items(),
            'selected_cinema': int(selected_cinema) if selected_cinema else None,
            'selected_types': selected_types,
            'types_list': ['2D', '3D', 'IMAX'],
            'gallery_images': gallery_images,  # ✅ теперь передаётся список картинок галереи фильма
        })
        return context

class LoginView(View):
    template_name = 'cinema/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('index')  # админка
            else:
                return redirect('main')
        else:
            context = {'error': 'Неверный логин или пароль'}
            return render(request, self.template_name, context)

class TicketBookingView(LoginRequiredMixin, View):
    def get(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
        tickets = Ticket.objects.filter(session=session).order_by('row', 'place')
        hall = session.hall
        main_banner = Banner.objects.first().image_main if Banner.objects.exists() else None

        matrix = [[None for _ in range(hall.col)] for _ in range(hall.row)]
        for ticket in tickets:
            matrix[ticket.row - 1][ticket.place - 1] = ticket

        return render(request, 'cinema/booking.html', {
            'session': session,
            'matrix': matrix,
            'film': session.film,
            'main_banner':main_banner,
        })

@method_decorator(csrf_exempt, name='dispatch')
class SubmitTicketsView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            ticket_ids = data.get('tickets', [])
            action = data.get('action')

            with transaction.atomic():
                # Блокируем билеты для безопасного обновления
                tickets = Ticket.objects.select_for_update().filter(id__in=ticket_ids, status='free')

                if tickets.count() != len(ticket_ids):
                    return JsonResponse({'success': False, 'error': 'Некоторые билеты уже заняты'}, status=400)

                if action == 'book':
                    tickets.update(status='booked', user=request.user)
                elif action == 'buy':
                    tickets.update(status='bought', user=request.user)
                else:
                    return JsonResponse({'success': False, 'error': 'Неизвестное действие'}, status=400)

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class CinemaListView(TemplateView):
    template_name = 'cinema/cinema_coord.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get('lang', 'uk')
        translation.activate(lang)
        context['lang'] = lang
        context['main_banner'] = Banner.objects.first().image_main if Banner.objects.exists() else None

        context['cinemas'] = Cinema.objects.all()
        context['side_banners'] = Banner.objects.all()[:3]  # если используешь баннеры
        return context

class CafeView(TemplateView):
    template_name = 'cinema/cafe.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get('lang', 'uk')
        translation.activate(lang)
        context['lang'] = lang

        cafe = About.objects.get(id=16)
        gallery_photos = Image.objects.filter(gall=cafe.gall)

        context['cafe'] = cafe
        context['gallery_photos'] = gallery_photos
        context['side_banners'] = Banner.objects.all()[:3]

        return context

class MobilPageView(TemplateView):
    template_name = 'cinema/mobil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get('lang', 'uk')
        translation.activate(lang)
        context['lang'] = lang

        mobil = About.objects.get(id=28)
        gallery_photos = Image.objects.filter(gall=mobil.gall)
        print(mobil.description)

        context['mobil'] = mobil
        context['gallery_photos'] = gallery_photos
        context['side_banners'] = Banner.objects.all()[:3]

        return context


class AdvertisingView(View):
    def get(self, request):
        # Активируем язык
        lang = request.GET.get('lang', 'uk')
        translation.activate(lang)

        # Получаем объект About с ID 27
        about = get_object_or_404(About, id=27)

        # Переведённые поля
        title = getattr(about, f'name_about_{lang}', about.name_about)
        description = getattr(about, f'description_{lang}', about.description)

        gallery_images = Image.objects.filter(gall=about.gall)
        side_banners = Banner.objects.all()[:3]
        return render(request, 'cinema/advertising.html', {
            'title': title,
            'description': description,
            'main_image': about.main_image,
            'video_url': about.video_url,
            'gallery_images': gallery_images,
            'lang': lang,
            'side_banners':side_banners,
        })

def hall_datail(request):
    return render(request, 'cinema/hall_detail.html')