import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.user = User.objects.create(username="post_author",)
        cls.group = Group.objects.create(
            title="Тестовый заголовок группы",
            slug="test-slug",
            description="Тестовое описание группы",
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=PostPagesTests.user,
            group=PostPagesTests.group,
            image=uploaded,
        )
        cls.group_without_post = Group.objects.create(
            title="Фейк группа",
            slug="fake-slug",
            description="Описание фейк группы",
        )
        cls.comment_post = Comment.objects.create(
            author=cls.user, text="Тестовый текст", post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author = Client()
        self.author.force_login(PostPagesTests.user)
        cache.clear()

    def test_views_use_correct_template(self):
        """View-классы используют ожидаемые HTML-шаблоны."""
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.pk}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.pk}
            ): "posts/create_post.html",
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Контекст страниц содержит ожидаемые значения."""
        context_fields = {
            reverse("posts:index"): self.post,
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): self.post,
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): self.post,
        }
        for reverse_page, object in context_fields.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.author.get(reverse_page)
                page_object = response.context["page_obj"][0]
                self.assertEqual(page_object.text, object.text)
                self.assertEqual(page_object.pub_date, object.pub_date)
                self.assertEqual(page_object.author, object.author)
                self.assertEqual(page_object.group, object.group)
                self.assertEqual(page_object.image, object.image)

    def test_forms_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом 'form'."""
        context_fields = [
            reverse("posts:post_create"),
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk}),
        ]
        for reverse_page in context_fields:
            with self.subTest(reverse_page=reverse_page):
                response = self.author.get(reverse_page)
                self.assertIsInstance(
                    response.context["form"].fields["text"],
                    forms.fields.CharField,
                )
                self.assertIsInstance(
                    response.context["form"].fields["group"],
                    forms.fields.ChoiceField,
                )
                self.assertIsInstance(
                    response.context["form"].fields["image"],
                    forms.fields.ImageField,
                )

    def test_groups_page_show_correct_context(self):
        """Существование созданного поста в группе."""
        context_fields = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): self.group,
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group_without_post.slug},
            ): self.group_without_post,
        }
        response = self.author.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": self.group_without_post.slug},
            )
        )
        self.assertFalse(response.context["page_obj"])
        for reverse_page, object in context_fields.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.author.get(reverse_page)
                group_object = response.context["group"]
                self.assertEqual(group_object.title, object.title)
                self.assertEqual(group_object.slug, object.slug)
                self.assertEqual(group_object.description, object.description)

    def test_authors_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом 'author'."""
        context_fields = {
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): self.user,
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.pk}
            ): self.user,
        }
        for reverse_page, object in context_fields.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.author.get(reverse_page)
                author_object = response.context["author"]
                self.assertEqual(author_object.username, object.username)

    def test_post_page_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом 'post'."""
        context_fields = [
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk}),
        ]
        for reverse_page in context_fields:
            with self.subTest(reverse_page=reverse_page):
                response = self.author.get(reverse_page)
                post_object = response.context["post"]
                self.assertEqual(post_object.text, self.post.text)
                self.assertEqual(post_object.pub_date, self.post.pub_date)
                self.assertEqual(post_object.author, self.user)
                self.assertEqual(post_object.group, self.group)
                self.assertEqual(post_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом 'comments'."""
        response = self.author.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk})
        )
        self.assertEqual(response.context["comments"][0], self.comment_post)

    def test_posts_count_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом 'posts_count'."""
        context_fields = [
            reverse("posts:profile", kwargs={"username": self.user.username}),
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
        ]
        for reverse_page in context_fields:
            with self.subTest(reverse_page=reverse_page):
                response = self.author.get(reverse_page)
                posts_count_object = response.context["posts_count"]
                self.assertEqual(posts_count_object, 1)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом 'is_edit'."""
        response = self.author.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk})
        )
        self.assertTrue(response.context["is_edit"])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="posts_author",)
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug="test-slug",
            description="Тестовое описание группы",
        )
        cls.post = [
            Post.objects.create(
                text=f"Пост {i}",
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group,
            )
            for i in range(13)
        ]

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.client.force_login(PaginatorViewsTest.user)

    def test_paginator_on_pages(self):
        """Тестирование паджинатора."""
        first_page_len_posts = 10
        second_page_len_posts = 3
        context_fields = {
            reverse("posts:index"): first_page_len_posts,
            reverse("posts:index") + "?page=2": second_page_len_posts,
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): first_page_len_posts,
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
            + "?page=2": second_page_len_posts,
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): first_page_len_posts,
            reverse("posts:profile", kwargs={"username": self.user.username})
            + "?page=2": second_page_len_posts,
        }
        for reverse_page, len_posts in context_fields.items():
            with self.subTest(reverse_page=reverse_page):
                self.assertEqual(
                    len(self.client.get(reverse_page).context["page_obj"]),
                    len_posts,
                )

    def test_object_list_first_page(self):
        """Содержимое на первой странице соответствует ожидаемому."""
        response = self.client.get(reverse("posts:index"))
        for i in range(10):
            page_object = response.context.get("page_obj").object_list[i]
            expected_object = response.context["page_obj"][i]
            self.assertEqual(page_object.author, expected_object.author)
            self.assertEqual(page_object.text, expected_object.text)
            self.assertEqual(page_object.group, expected_object.group)
            self.assertEqual(page_object.pub_date, expected_object.pub_date)

    def test_object_list_second_page(self):
        """Содержимое на второй странице соответствует ожидаемому."""
        response = self.client.get(reverse("posts:index") + "?page=2")
        for i in range(3):
            page_object = response.context.get("page_obj").object_list[i]
            expected_object = response.context["page_obj"][i]
            self.assertEqual(page_object.author, expected_object.author)
            self.assertEqual(page_object.text, expected_object.text)
            self.assertEqual(page_object.group, expected_object.group)
            self.assertEqual(page_object.pub_date, expected_object.pub_date)


class CacheIndexPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="posts_author",)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Тестирование кеша главной страницы."""
        new_post = Post.objects.create(text="Тестовый пост", author=self.user,)
        response_content_1 = self.authorized_client.get(
            reverse("posts:index")
        ).content
        new_post.delete()
        response_content_2 = self.authorized_client.get(
            reverse("posts:index")
        ).content
        self.assertEqual(response_content_1, response_content_2)
        cache.clear()
        response_content_3 = self.authorized_client.get(
            reverse("posts:index")
        ).content
        self.assertNotEqual(response_content_2, response_content_3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username="posts_author",)
        cls.follower = User.objects.create(username="follower",)
        cls.post = Post.objects.create(
            author=FollowViewsTest.author, text="Тестовый текст",
        )

    def setUp(self):
        cache.clear()
        self.follower_client = Client()  # Подписчик
        self.follower_client.force_login(self.follower)
        self.author_client = Client()  # Автор постов
        self.author_client.force_login(self.author)

    def test_follow_page_context(self):
        """Тестирование подписки и отписки от авторов."""
        response = self.follower_client.get(reverse("posts:follow_index"))
        page_object = response.context.get("page_obj").object_list
        self.assertEqual((len(page_object)), 0)
        # Подписка
        self.follower_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.author.username},
            )
        )
        response = self.follower_client.get(reverse("posts:follow_index"))
        self.assertEqual((len(response.context["page_obj"])), 1)
        page_object = response.context.get("page_obj").object_list[0]
        self.assertEqual(page_object.author, self.author)
        self.assertEqual(page_object.text, self.post.text)
        self.assertEqual(page_object.pub_date, self.post.pub_date)
        # Отписка
        self.follower_client.get(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": self.author.username},
            )
        )
        response = self.follower_client.get(reverse("posts:follow_index"))
        page_object = response.context.get("page_obj").object_list
        self.assertEqual((len(page_object)), 0)

    def test_cant_following_self(self):
        """Подписки не появляются у тех, кто не подписан."""
        response = self.author_client.get(reverse("posts:follow_index"))
        page_object = response.context.get("page_obj").object_list
        self.assertEqual((len(page_object)), 0)
        self.author_client.get(
            reverse(
                "posts:profile_follow",
                kwargs={"username": self.author.username},
            )
        )
        response = self.author_client.get(reverse("posts:follow_index"))
        self.assertEqual((len(page_object)), 0)
