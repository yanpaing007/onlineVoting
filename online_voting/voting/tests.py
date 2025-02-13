from django.test import TestCase, TransactionTestCase
from .factories import VotingEventFactory, CategoryFactory

class VotingEventTestCase(TransactionTestCase):
    def setUp(self):
        self.category = CategoryFactory()
        self.voting_event = VotingEventFactory(categories=[self.category])

    def test_voting_event_creation(self):
        self.assertIsNotNone(self.voting_event.id)
        self.assertEqual(self.voting_event.categories.count(), 1)
        # Add a breakpoint here to inspect the database
        import pdb; pdb.set_trace()