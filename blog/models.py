from django.db import models
from django.db.models import Count, Prefetch
from django.urls import reverse
from django.contrib.auth.models import User


class PostQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(likes_count=Count('likes')).order_by('-likes_count')

    def fetch_with_comments_count(self):
        """
            Добавляет к каждому посту поле `comments_count`, содержащее количество комментариев.

            Этот метод выполняет дополнительный SQL-запрос, который подсчитывает количество
            комментариев для каждого поста и вручную присваивает это значение атрибуту `comments_count`.

            Преимущества:
            - Можно использовать срезы.
            - Можно использовать после `select_related` и `prefetch_related` без потери производительности.
            - Не увеличивает время на обработку запроса
        """
        posts = list(self)
        post_ids = [post.id for post in posts]

        posts_with_counts = Post.objects.filter(id__in=post_ids)\
            .annotate(
            comments_count=Count('comments'),
            likes_amount=Count('likes')
        )

        id_to_counts = {
            post.id: {
                'comments_count': post.comments_count,
                'likes_amount': post.likes_amount,
            }
            for post in posts_with_counts
        }

        for post in posts:
            counts = id_to_counts.get(post.id, {})
            post.comments_count = counts.get('comments_count', 0)
            post.likes_amount = counts.get('likes_amount', 0)

        return posts

    def fetch_with_related_data(self):
        return self.select_related('author')\
            .prefetch_related(
            Prefetch(
                'tags',
                queryset=Tag.objects.annotate(posts_with_tag=Count('posts'))
            )
        )


class TagQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(posts_with_tag=Count('posts')).order_by('-posts_with_tag')


class TagManager(models.Manager):
    def get_queryset(self):
        return TagQuerySet(self.model, using=self._db)

    def popular(self):
        return self.get_queryset().popular()


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    objects = PostQuerySet.as_manager()


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    def clean(self):
        self.title = self.title.lower()

    objects = TagQuerySet.as_manager()


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name = 'comments')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'
