from django.apps import AppConfig
import os


class CreditApprovalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "credit_approval"

    def ready(self):
        # only run ingestions when RUN_INGESTION is set to true
        if os.environ.get("RUN_INGESTION") == "true":
            from .tasks import ingest_customer_data, ingest_loan_data

            ingest_customer_data.delay()
            ingest_loan_data.delay()
