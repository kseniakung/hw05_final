# Generated by Django 2.2.9 on 2023-02-12 16:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0002_auto_20230210_0128"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="group",
            options={
                "verbose_name": "Группа",
                "verbose_name_plural": "Группы",
            },
        ),
        migrations.AlterModelOptions(
            name="post",
            options={
                "ordering": ["-pub_date"],
                "verbose_name": "Пост",
                "verbose_name_plural": "Посты",
            },
        ),
        migrations.AlterField(
            model_name="group",
            name="description",
            field=models.TextField(verbose_name="Описание группы"),
        ),
        migrations.AlterField(
            model_name="group",
            name="slug",
            field=models.SlugField(
                max_length=200, unique=True, verbose_name="Адрес группы"
            ),
        ),
        migrations.AlterField(
            model_name="group",
            name="title",
            field=models.CharField(
                max_length=200, verbose_name="Название группы"
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="posts",
                to="posts.Group",
                verbose_name="Группа",
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="text",
            field=models.TextField(verbose_name="Текст"),
        ),
    ]
