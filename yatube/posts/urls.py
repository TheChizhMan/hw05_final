from django.urls import path

from . import views

app_name = 'posts'


urlpatterns = [
    path('', views.index,
         name='index'),

    path('group/<slug:slug>/',
         views.group_posts,
         name='group_list'),

    # Профайл пользователя
    path('profile/<str:username>/',
         views.profile,
         name='profile'),

    # Просмотр записи
    path('posts/<int:post_id>/',
         views.post_detail,
         name='post_detail'),

    # Создание поста
    path('create/',
         views.post_create,
         name='post_create'),

    # Редактирование поста
    path('posts/<int:post_id>/edit/',
         views.post_edit,
         name='post_edit'),

    # Коментирование поста
    path('posts/<int:post_id>/comment/',
         views.add_comment,
         name='add_comment'),

    # Список подписок
    path('follow/', views.follow_index, name='follow_index'),

    # Список подписчиков
    path('profile/<str:username>/follow/',
         views.profile_follow,
         name='profile_follow'),

    # Отписка
    path('profile/<str:username>/unfollow/',
         views.profile_unfollow,
         name='profile_unfollow'),
]
