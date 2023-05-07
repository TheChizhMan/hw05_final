import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateEditFormTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.post = Post.objects.create(text='Тестовый текст',
                                        author=self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test-slug')

    def test_create_post(self):
        """Создание записи в БД при отправке валидной формы."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        url = reverse('posts:post_create')
        data = {'text': 'Тестовый текст', 'image': uploaded}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.user.username,)))
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.text, data['text'])
        self.assertTrue(self.post.text, self.post.image)

    def test_edit_post(self):
        """Тест отправки валидной формы при редактировании поста."""
        url = reverse('posts:post_edit', args=(self.post.id,))
        data = {'text': 'Измененный текст'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=(self.post.id,)))
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, data['text'])

    def test_edit_post_with_group_anonymous(self):
        """Тест создания и редактирования анонимным пользователем."""
        self.client.logout()
        url = reverse('posts:post_edit', args=(self.post.id,))
        data = {'text': 'Измененный текст', 'group': self.group.id}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('login') + '?next=' + url)

    def test_anonymous_create_post(self):
        """Проверка, что анонимный пользователь не может создать пост."""
        self.client.logout()
        url = reverse('posts:post_create')
        data = {'text': 'Тестовый текст'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('login') + '?next=' + url)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.following = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.following,
        )
        cls.follow_index_url = reverse('posts:follow_index')

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_following = Client()
        self.authorized_following.force_login(self.following)
        self.another_client = Client()
        self.another_client.force_login(self.following)
        cache.clear()

    def test_auth_user_can_follow_author(self):
        """Проверка работоспособности подписки."""
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower, author=self.following
            ).exists()
        )
        self.authorized_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following.username},
            )
        )
        self.assertEqual(Follow.objects.count(), 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower, author=self.following
            ).exists()
        )

    def test_auth_user_can_unfollow_author(self):
        """Проверка работоспособности отписки."""
        Follow.objects.create(user=self.follower, author=self.following)
        self.authorized_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.following.username},
            )
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower, author=self.following
            ).exists()
        )

    def test_subscription_feed_for_auth_users(self):
        """Проверяем появление в ленте подписчика."""
        Follow.objects.create(user=self.follower, author=self.following)
        response = self.authorized_follower.get('/follow/')
        follower_index = response.context['page_obj'][0]
        self.assertEqual(self.post, follower_index)

    def test_subscription_feed_not_show_own_user_post(self):
        """Проверяем непоявление в ленте подписчика."""
        response = self.another_client.get(self.follow_index_url)
        self.assertNotIn(self.post, response.context['page_obj'])
