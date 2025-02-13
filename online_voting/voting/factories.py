import factory
from django.contrib.auth.models import User
from .models import VotingEvent, Category

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')

class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')

class VotingEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VotingEvent

    event_name = factory.Faker('sentence', nb_words=4)
    start_time = factory.Faker('date_time')
    end_time = factory.Faker('date_time')
    event_token = factory.Faker('bothify', text='?????#####')
    created_by = factory.SubFactory(UserFactory)
    candidate_numbers = 2
    is_private = False

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for category in extracted:
                self.categories.add(category)