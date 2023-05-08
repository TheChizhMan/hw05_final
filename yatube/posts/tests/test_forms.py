import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment

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
        self.assertTrue(
            Post.objects.filter(image='posts/' + uploaded.name).exists()
        )

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


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='testuser')
        cls.auth_client = Client()
        cls.author = User.objects.create(username='author')
        cls.auth_client.force_login(cls.author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(text='Тестовый пост',
                                       author=cls.user)
        cls.comment = Comment.objects.create(text='Тестовый комментарий',
                                             author=cls.user,
                                             post=cls.post)

    def test_commenting_by_authorized_user(self):
        """Тестируем возможность коментирования авторизованным."""
        form_data = {'text': 'Тестовый комментарий'}
        # извините, не понимаю, вроде сделал как надо
        response = self.authorized_client.post(
            f'/posts/{self.post.id}/comment/',
            data=form_data,
            follow=True)
        self.assertRedirects(response, f'/posts/{self.post.id}/')
        expected_count = 2
        self.assertEqual(Comment.objects.count(), expected_count)
        comment = Comment.objects.last()
        self.assertEqual(comment.text, self.comment.text)
        self.assertEqual(comment.author.username, 'testuser')

    def test_commenting_by_guest_user(self):
        """Тестируем невозможность коментирования гостем."""
        form_data = {'text': 'Тестовый комментарий'}
        response = self.guest_client.post(
            f'/posts/{self.post.id}/comment/',
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/')
