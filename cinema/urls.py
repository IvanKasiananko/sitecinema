from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views
from .views import CinemaView, FilmsPageView, ScheduleView, HallsByCinemaView, FilmDetailView, FilmView, \
    CinemaDetailView, ActionsView, ActionDetailView, LoginView, TicketBookingView, SubmitTicketsView, CinemaListView, \
    CafeView, AdvertisingView, MobilPageView

urlpatterns = [
    path('', FilmView.as_view(),name='main'),
    path('films/<str:category>/', FilmsPageView.as_view(), name='films_by_category'),
    path('schedule/', ScheduleView.as_view(), name='schedule'),
    path('ajax/halls/', HallsByCinemaView.as_view(), name='ajax_halls_by_cinema'),
    path('film/<int:pk>/', FilmDetailView.as_view(), name='film_detail'),
    path('cinema/', CinemaView.as_view(), name='cinema'),
    path('cinema/<int:pk>/', CinemaDetailView.as_view(), name='cinema_detail'),
    path('hall/<int:pk>/', views.HallDetailView.as_view(), name='hall_detail'),
    path('actions/<int:pk>/', ActionDetailView.as_view(), name='action_detail'),
    path('actions/', ActionsView.as_view(), {'category': 'action'}, name='actions'),
    path('news/', ActionsView.as_view(), {'category': 'news'}, name='news_cinema'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='main'), name='logout'),
    path('booking/<int:session_id>/', TicketBookingView.as_view(), name='booking_page'),
    path('submit-tickets/', SubmitTicketsView.as_view(), name='submit_tickets'),
    path('coord/', CinemaListView.as_view(), name='cinema_coord'),
    path('cafe/', CafeView.as_view(), name='cafe'),
    path('advertising/', AdvertisingView.as_view(), name='advertising'),
    path('mobil', MobilPageView.as_view(), name='mobil'),
]
