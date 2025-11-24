from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from .forms import CommentForm
from .models import Comment, News


class NewsList(generic.ListView):
    """Список новостей."""

    model = News
    template_name = 'news/home.html'

    def get_queryset(self):
        """
        Выводим только несколько последних новостей.

        Количество определяется в настройках проекта.
        """
        # Получение QS через атрибут model соответсвует лучшим практикам Django
        # и принципу DRY.
        # Использование select_related приведет декартову произведению.
        return self.model.objects.prefetch_related(
            'comment_set'  # Авто-сгенерированный related_name
        )[:settings.NEWS_COUNT_ON_HOME_PAGE]


class NewsDetail(generic.DetailView):
    """Обрабатывам GET-запрос к отдельной новости."""

    model = News
    template_name = 'news/detail.html'

    def get_object(self, queryset=None):
        """Получаем новость и комментарии."""
        obj = get_object_or_404(
            # prefetch_related сначала загружает комментарии, затем авторов,
            # т.к. работает рекурсивно. Таким образом QS хранит новость,
            # комментарии к ней, и модель Пользователя,
            # который является автором комментария
            self.model.objects.prefetch_related('comment_set__author'),
            pk=self.kwargs['pk']
        )
        # <News: News object (1)> и спец. структура в которой благодаря методу
        # prefetch_related хранятся комментарии и их авторы
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['form'] = CommentForm()
        return context


class NewsComment(
        LoginRequiredMixin,
        generic.detail.SingleObjectMixin,
        generic.FormView
):
    """
    Создание комментария к отдельной новости.

    Обрабатываем POST-запрос к отдельной новости.
    """

    model = News
    form_class = CommentForm
    template_name = 'news/detail.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Создаёт объект модели Comment
        comment = form.save(commit=False)
        comment.news = self.object
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        post = self.get_object()
        return reverse('news:detail', kwargs={'pk': post.pk}) + '#comments'


class NewsDetailView(generic.View):
    """
    Обрабатывает входящие HTTP-запросы.

    Перенаправляем запросы на соответствующие представления в зависимости от
    метода HTTP.
    """

    # Работает, потому что явно определен, вызывается через метод
    # dispatch род. класса
    def get(self, request, *args, **kwargs):
        view = NewsDetail.as_view()
        return view(request, *args, **kwargs)

    # Работает, потому что явно определен, вызывается через метод
    # dispatch род. класса
    def post(self, request, *args, **kwargs):
        view = NewsComment.as_view()
        return view(request, *args, **kwargs)


class CommentBase(LoginRequiredMixin):
    """Базовый класс для работы с комментариями."""

    model = Comment

    def get_success_url(self):
        comment = self.get_object()
        return reverse(
            'news:detail', kwargs={'pk': comment.news.pk}
        ) + '#comments'

    def get_queryset(self):
        """Пользователь может работать только со своими комментариями."""

        # Переопределяем выборку, чтобы Update, Delete получали только свои
        # комменты.
        return self.model.objects.filter(author=self.request.user)


class CommentUpdate(CommentBase, generic.UpdateView):
    """Редактирование комментария."""
    template_name = 'news/edit.html'
    form_class = CommentForm


class CommentDelete(CommentBase, generic.DeleteView):
    """Удаление комментария."""
    template_name = 'news/delete.html'
