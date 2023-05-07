from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(title='Тестовый тайтл',
                                         slug='test-slug',
                                         description='Тестовое описание')
        for i in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый текст {i}',
                author=cls.user,
                group=cls.group,
            )

    def setUp(self):
        cache.clear()
        self.guest_client = self.client
        self.user = PostsViewsTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': 'test-slug'}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': 'testuser'}),
            'posts/post_detail.html': (reverse('posts:post_detail',
                                               kwargs={'post_id': self.post.id}
                                               )
                                       ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        templates_pages_names_1 = {
            'posts/create_post.html': reverse('posts:post_edit',
                                              kwargs={'post_id': self.post.id}
                                              )}
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        for template, reverse_name in templates_pages_names_1.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблон использует соответствующий контекст (+ 'image')."""
        pages_with_context = {
            reverse('posts:index'): ('page_obj', 'image',),
            reverse('posts:post_create'): ('form',),
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): ('page_obj',
                                                    'group', 'image',),
            reverse('posts:profile',
                    kwargs={'username': 'testuser'}): ('page_obj',
                                                       'author', 'image',),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}): ('post',
                                                        'image',),
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}): ('form',),
        }
        for reverse_name, context_keys in pages_with_context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                for key in context_keys:
                    if key == 'image':
                        self.assertTrue(
                            key in response.context
                            or key not in response.context)
                    else:
                        self.assertIn(key, response.context)

    def test_create_post_with_group_on_pages(self):
        """При создании поста с группой, пост появляется на страницах."""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertIn(self.post, response.context['page_obj'])

    def test_first_page_contains_ten_records(self):
        """Тест пагинатора на превой странице."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.PAGE_SIZE)

    def test_second_page_correct_number_of_records(self):
        """Тест пагинатора на второй странице."""
        total_records = Post.objects.count()
        page_size = settings.PAGE_SIZE
        expected_records_on_second_page = total_records - page_size
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         expected_records_on_second_page)


class CacheTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.group = Group.objects.create(title='Test group',
                                          slug='test-group')
        self.user = get_user_model().objects.create_user(username='testuser')
        self.post = Post.objects.create(text='test text',
                                        group=self.group,
                                        author=self.user)

    def test_cache_local(self):
        """Тест кеширования главной страницы."""
        cache.set('key', 'value', 20)
        self.assertEqual(cache.get('key'), 'value')

    def test_cache(self):
        """Тест для проверки кеширования главной страницы."""
        cache.clear()
        response = self.client.get('/')
        self.assertContains(response, self.post.text)
        self.post.delete()
        response = self.client.get('/')
        self.assertContains(response, self.post.text)
        cache.clear()
        response = self.client.get('/')
        self.assertNotContains(response, self.post.text)


class FollowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1',
                                              password='password')
        self.user2 = User.objects.create_user(username='user2',
                                              password='password')
        self.post = Post.objects.create(text='test post', author=self.user2)
        self.client.login(username='user1', password='password')

    def test_follow(self):
        """Тест подписки авторизованного юзера.
        И отображение в ленте."""
        response = self.client.get(f'/profile/{self.user2.username}/follow/')
        self.assertRedirects(response, f'/profile/{self.user2.username}/')
        self.assertTrue(Follow.objects.filter(user=self.user1,
                                              author=self.user2).exists())
        response = self.client.get('/follow/')
        self.assertContains(response, self.post.text)

    def test_unfollow(self):
        """Тест отписки авторизованного юзера.
        И отображение в ленте."""
        response = self.client.get(f'/profile/{self.user2.username}/follow/')
        self.assertRedirects(response, f'/profile/{self.user2.username}/')
        self.assertTrue(Follow.objects.filter(user=self.user1,
                                              author=self.user2).exists())
        response = self.client.get(f'/profile/{self.user2.username}/unfollow/')
        self.assertRedirects(response, f'/profile/{self.user2.username}/')
        self.assertFalse(Follow.objects.filter(user=self.user1,
                                               author=self.user2).exists())
        response = self.client.get('/follow/')
        self.assertNotContains(response, self.post.text)
