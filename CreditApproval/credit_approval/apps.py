from django.apps import AppConfig


class CreditApprovalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "credit_approval"

    def ready(self):
        from .tasks import ingest_customer_data, ingest_loan_data

        ingest_customer_data.delay()
        ingest_loan_data.delay()
