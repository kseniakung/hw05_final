from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Comment, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug="test_slug",
            description="Тестовое описание группы",
        )
        cls.user = User.objects.create_user(username="HasNoName")
        cls.user_author = User.objects.create_user(username="author")
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=PostURLTests.user_author,
            group=PostURLTests.group,
        )
        cls.comment_post = Comment.objects.create(
            author=cls.user, text="Тестовый текст", post=cls.post
        )

    def setUp(self):
        self.guest_client = Client()
        self.author = Client()
        self.author.force_login(PostURLTests.user_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        cache.clear()

    def test_guest_client_urls_status_code(self):
        """Тестируемые страницы доступны любому пользователю."""
        responses_urls = {
            "/": HTTPStatus.OK,
            "/group/test_slug/": HTTPStatus.OK,
            f"/profile/{self.user.username}/": HTTPStatus.OK,
            f"/posts/{self.post.pk}/": HTTPStatus.OK,
            "/unexisting_page/": HTTPStatus.NOT_FOUND,
        }
        for url, response_code in responses_urls.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_authorized_client_urls_status_code(self):
        """Страница /create/ доступна авторизованному клиенту."""
        response = self.authorized_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_urls_status_code(self):
        """Страница posts/../edit/ доступна автору поста."""
        response = self.author.get(f"/posts/{self.post.pk}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_client_redirect(self):
        """Верный redirect для неавторизованного клиента."""
        redirect_response = {
            f"/posts/{self.post.pk}/edit/":
            f"/auth/login/?next=/posts/{self.post.pk}/edit/",
            "/create/": "/auth/login/?next=/create/",
        }
        for url, redirect in redirect_response.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect)

    def test_authorized_client_redirect(self):
        """Верный redirect для автора поста или комментария."""
        redirect_response = {
            f"/posts/{self.post.pk}/edit/": f"/posts/{self.post.pk}/",
            f"/posts/{self.post.pk}/comment/": f"/posts/{self.post.pk}/",
        }
        for url, redirect in redirect_response.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertRedirects(response, redirect)

    def test_urls_use_correct_template(self):
        """Тестируемые страницы используют верные шаблоны."""
        templates_url_names = {
            "/": "posts/index.html",
            "/group/test_slug/": "posts/group_list.html",
            f"/profile/{self.post.author.username}/": "posts/profile.html",
            f"/posts/{self.post.pk}/": "posts/post_detail.html",
            f"/posts/{self.post.pk}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                adress_url = self.author.get(adress)
                self.assertTemplateUsed(adress_url, template)
