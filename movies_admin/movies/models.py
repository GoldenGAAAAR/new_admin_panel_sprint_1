from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
# Create your models here.
import uuid
from django.db import models

class TimeStampedMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class Genre(TimeStampedMixin, UUIDMixin):
    def __str__(self):
        return self.name
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    class Meta:
        db_table = "content\".\"genre"
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Person(TimeStampedMixin, UUIDMixin):
    def __str__(self):
        return self.full_name

    full_name = models.CharField(_('name'), max_length=255)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = 'Человек'
        verbose_name_plural = 'Люди'


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"

class PersonFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    role = models.TextField(_('role'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content\".\"person_film_work"

class Filmwork(TimeStampedMixin, UUIDMixin):
    def __str__(self):
        return self.title
    class FilmType(models.TextChoices):
        MOVIE = 'movie', _('Movie')
        TV_SHOW = 'tv_show', _('TV Show')
    title = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    creation_date = models.DateField()
    rating = models.FloatField(_('rating'), blank=True, validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])
    file_path = models.CharField(_('file path'), null=True, default=None, max_length=255)
    type = models.CharField(max_length=10, choices=FilmType.choices)
    genres = models.ManyToManyField(Genre, through='GenreFilmwork')
    persons = models.ManyToManyField(Person, through="PersonFilmwork")
    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = 'Кинопроизведение'
        verbose_name_plural = 'Кинопроизведения'

