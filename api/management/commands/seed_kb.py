from django.core.management.base import BaseCommand

from api.models import KBEntry

ENTRIES = [
    {
        "question": "What is select_related in Django ORM?",
        "answer": "select_related performs a SQL JOIN and fetches related objects in the same query, which avoids extra queries when you follow foreign keys.",
        "category": KBEntry.Category.DATABASE,
    },
    {
        "question": "How does select_related differ from prefetch_related?",
        "answer": "select_related is for single-valued relationships and uses a JOIN. prefetch_related is for many-valued relationships and runs a separate query.",
        "category": KBEntry.Category.DATABASE,
    },
    {
        "question": "How does transaction.atomic() work?",
        "answer": "transaction.atomic wraps a block in a database transaction. If an exception is raised, every write inside the block is rolled back.",
        "category": KBEntry.Category.DATABASE,
    },
    {
        "question": "When should I use transaction.atomic for a search log?",
        "answer": "Use transaction.atomic when a query and its QueryLog row must succeed together, so usage is never recorded without the search, or the reverse.",
        "category": KBEntry.Category.DATABASE,
    },
    {
        "question": "What is a JWT token?",
        "answer": "A JWT is a signed token. TeamBoard uses SimpleJWT so a company proves identity without sending a password on every request.",
        "category": KBEntry.Category.API,
    },
    {
        "question": "How does JWT authentication work with DRF?",
        "answer": "The client sends Authorization: Bearer <access>. JWTAuthentication validates the signature and loads the user. Protected endpoints reject missing tokens with 401.",
        "category": KBEntry.Category.API,
    },
    {
        "question": "When should I use Q objects?",
        "answer": "Use Q objects when a filter needs OR logic, such as matching a search term against both question and answer.",
        "category": KBEntry.Category.DATABASE,
    },
    {
        "question": "How do Q objects combine with icontains?",
        "answer": "Q(question__icontains=term) | Q(answer__icontains=term) is a case-insensitive match on either field.",
        "category": KBEntry.Category.DATABASE,
    },
    {
        "question": "What are Django signals used for?",
        "answer": "Signals let you run code when a model is saved. TeamBoard uses post_save on User to create a Company and an api_key.",
        "category": KBEntry.Category.FRAMEWORK,
    },
    {
        "question": "How do post_save signals work in Django?",
        "answer": "post_save fires after a model save. Check created, or instance._state.adding captured in pre_save, so the profile is created only the first time.",
        "category": KBEntry.Category.FRAMEWORK,
    },
    {
        "question": "Why does an API use an api_key instead of a company id?",
        "answer": "A client can type any company id. An api_key is a secret the server generated, so the platform can tell which company is calling.",
        "category": KBEntry.Category.API,
    },
    {
        "question": "How do I run PostgreSQL for a Django app in the cloud?",
        "answer": "Run Postgres in Docker locally, keep credentials in environment variables, and point DATABASES at that host when you deploy.",
        "category": KBEntry.Category.CLOUD,
    },
    {
        "question": "What status code should a search return when nothing matches?",
        "answer": "Return 200 with an empty results list and count 0. A search that finds nothing is still a successful query and should be logged.",
        "category": KBEntry.Category.GENERAL,
    },
]


class Command(BaseCommand):
    help = "Insert sample knowledge-base entries."

    def handle(self, *args, **options):
        created = 0
        for entry in ENTRIES:
            _, was_created = KBEntry.objects.get_or_create(
                question=entry["question"],
                defaults={
                    "answer": entry["answer"],
                    "category": entry["category"],
                },
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} new KB entries ({KBEntry.objects.count()} total)."
            )
        )
