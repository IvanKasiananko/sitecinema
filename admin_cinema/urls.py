from django.urls import path
from . import views
from .views import BannerAddView, UserAddView, UserView, UserEditView, FilmView, FilmAddView, \
    FilmEditView, CinemaView, CinemaAddView, NewsActionEditView, HallAddView, CinemaEditView, UserJsonView, \
    UserDeleteView, NewsletterView, LetterUserAjaxView, task_status, SessionCreateView, GenerateSessionsView, \
    CinemaAdressView

urlpatterns = [
    path('', views.index, name='index'),
    path('film/', FilmView.as_view(), name='film_admin'),
    path('create_film/', FilmAddView.as_view(), name='create_film'),
    path('films/<int:pk>/edit/', FilmEditView.as_view(), name='edit_film'),
    path('sessions/', SessionCreateView.as_view(), name='create_session'),
    path('cinema_admin/', CinemaView.as_view(), name='cinema_admin'),
    path('create_cinema/', CinemaAddView.as_view(), name='create_cinema'),
    path('edit_cinema/<int:pk>/edit/', CinemaEditView.as_view(), name='edit_cinema'),
    path('hall/', views.hall, name='hall'),
    path('news/', views.news_page, name='news'),
    path('news-data/', views.news_data, name='news_data'),
    path('hall_data/', views.hall_data, name='hall_data'),
    path('hall_delete/<int:pk>/', views.hall_delete, name='hall_delete'),
    path('hall_edit/<int:pk>/', views.HallEditView.as_view(), name='hall_edit'),
    path('news_action/<int:pk>/edit/', NewsActionEditView.as_view(), name='edit_news_action'),
    path('news_action_delete/<int:pk>/', views.news_action_delete, name='news_action_delete'),
    path('create_news_action/', views.NewsActionAddView.as_view(), name='create_news_action'),
    path('useradd/', UserAddView.as_view(), name='useradd'),
    path('user_edit/<int:pk>/', UserEditView.as_view(), name='user_edit'),
    path('user_delete/', UserDeleteView.as_view(), name='user_delete'),
    path('user_json/', UserJsonView.as_view(), name='user_json'),
    path('user/', UserView.as_view(), name='user'),
    path('create_hall/<int:pk>/', HallAddView.as_view(), name='create_hall'),
    path('hall_editor/', views.hall_editor, name='hall_editor'),
    path('edit_user/', views.edit_user, name='edit_user'),
    path('newsletter/', NewsletterView.as_view(), name='newsletter'),
    path("upload-template/", views.upload_template, name="upload_template"),
    path('select-users/', views.select_users, name='select_users_page'),
    path('users_ajax/', LetterUserAjaxView.as_view(), name='users_ajax'),
    path('newsletter/delete_template/', views.delete_template_ajax, name='delete_template'),
    path('task-status/<str:task_id>/', views.task_status, name='task_status'),
    path('dash_town/', views.dash_town, name='dash_town'),
    path('dash_film/', views.dash_film, name='dash_film'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('banner/', BannerAddView.as_view(), name='banner'),
    path('cinema_adress', CinemaAdressView.as_view(), name='cinema_adress'),
    # path('delete/', views.delete, name='delete'),
    path('statistic/', views.statistic, name='statistic'),
    path('main_page/', views.main_page, name='main_page'),
    path('pages/<int:post_id>/', views.pages, name='pages'),
    path('ajax/load-halls/', views.load_halls, name='ajax_load_halls'),
    path('generate_sessions/', GenerateSessionsView.as_view(), name='generate_sessions'),
]
