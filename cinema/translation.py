
from modeltranslation.translator import translator, TranslationOptions
from .models import Film, About, Hall, Cinema


class FilmTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

translator.register(Film, FilmTranslationOptions)

class AboutTranslationOptions(TranslationOptions):
    fields = ('name_about', 'description')

translator.register(About, AboutTranslationOptions)

class HallTranslationOptions(TranslationOptions):
    fields = ('name_hall', 'description')

translator.register(Hall, HallTranslationOptions)

class CinemaTranslationOptions(TranslationOptions):
    fields = ('name_cinema', 'seo_text','conditions')

translator.register(Cinema, CinemaTranslationOptions)
