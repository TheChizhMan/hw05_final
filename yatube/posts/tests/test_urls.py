from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.post = Post.objects.create(text='Тестовый заголовок',
                                       author=cls.user)
        cls.group = Group.objects.create(title='Тестовый тайтл',
                                         slug='test-slug')

    def setUp(self):
        self.guest_client = self.client
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{PostURLTests.group.slug}/',
            'posts/profile.html': f'/profile/{PostURLTests.user.username}/',
            'posts/post_detail.html': f'/posts/{PostURLTests.post.id}/',
        }

        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_create_post_page(self):
        """Страница создания доступна только для авторизованных."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_page(self):
        """Страница редактирования доступна только для автора публикации."""
        post = Post.objects.create(text='Тестовый текст', author=self.user)
        response = self.guest_client.get(f'/posts/{post.id}/edit/')
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{post.id}/edit/')
        other_user = User.objects.create(username='otheruser')
        other_authorized_client = Client()
        other_authorized_client.force_login(other_user)
        response = other_authorized_client.get(f'/posts/{post.id}/edit/')
        response = self.authorized_client.get(f'/posts/{post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
