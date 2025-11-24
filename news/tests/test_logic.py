from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


class TestCommentCreation(TestCase):
    COMMENT_TEXT = 'Текст комментария'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Заголовок',
            text='Текст'
        )
        cls.url = reverse('news:detail', args=(cls.news.pk,))
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Отправляем значение только для поля text, т.к. остальные данные
        # представление получит в методе form_valid, из запроса.
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self):
        # Настроен обработчик, который знает как обрабатывать POST-запрос.
        self.client.post(self.url, data=self.form_data)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)

    def test_user_can_create_comment(self):
        response = self.auth_client.post(
            self.url,
            data=self.form_data
        )
        # Редирект после создания комментария. #comments - якорь.
        # Ссылка с якорем позволяет не просто сослаться на страницу,
        # а прокрутить эту страницу до определённого раздела; в нашем случае —
        # до HTML-тега с атрибутом id="comments".
        self.assertRedirects(response, f'{self.url}#comments')

        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)

        comment = Comment.objects.get()
        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)

    def test_user_cant_use_bad_words(self):
        # Форма для POST-запроса
        bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
        response = self.auth_client.post(self.url, data=bad_words_data)

        form = response.context['form']
        self.assertFormError(
            form=form,
            field='text',
            errors=WARNING,
        )

        # Дополнительно убедимся, что комментарий не был создан.
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)


class TestCommentEditDelete(TestCase):
    COMMENT_TEXT = 'Текст комментария'
    NEW_COMMENT_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        news_url = reverse('news:detail', args=(cls.news.id,))
        cls.url_to_comments = news_url + '#comments'
        cls.author = User.objects.create(username='Автор комментария')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT
        )
        # URL для редактирования комментария.
        cls.edit_url = reverse('news:edit', args=(cls.comment.id,))
        # URL для удаления комментария.
        cls.delete_url = reverse('news:delete', args=(cls.comment.id,))
        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def test_author_can_delete_comment(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_to_comments)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_comment(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_to_comments)
        # Обновляем объект комментария.
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.COMMENT_TEXT)
