from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        # Проверка, что статус ответа сервера - 404
        self.assertEqual(response.status_code, 404)
        # Проверка, что используется шаблон core/404.html
        self.assertTemplateUsed(response, 'core/404.html')
