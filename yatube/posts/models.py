from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

LEN_TEXT = 15


class Group(models.Model):
    title = models.CharField(verbose_name="Название группы", max_length=200)
    slug = models.SlugField(
        verbose_name="Адрес группы", max_length=200, unique=True
    )
    description = models.TextField(verbose_name="Описание группы")

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title


class Post(models.Model):

    text = models.TextField(
        verbose_name="Текст поста", help_text="Введите текст поста"
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="posts",
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
    )
    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        help_text="Загрузите картинку",
        verbose_name="Картинка",
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:LEN_TEXT]


class Comment(models.Model):

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments",
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(
        verbose_name="Текст комментария", help_text="Введите комментарий"
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата публикации",
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:LEN_TEXT]


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name="unique subs"
            )
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
