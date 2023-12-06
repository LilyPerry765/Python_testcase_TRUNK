import sys

from django.apps import AppConfig

from rspsrv.apps.mis.versions.v1_0.config import load_templates


class MisConfig(AppConfig):
    name = 'rspsrv.apps.mis'

    def ready(self):
        if sys.argv[0] == "uwsgi" or (
                len(sys.argv) > 1 and sys.argv[1] not in (
                "start_ari",
                "collectstatic",
                "makemigrations",
                "migrate",
                "loaddata",
                "makemessages",
                "compilemessages",
                "cdr_plant_seeds",
                "createsuperuser",
        )):
            print("Trying to load notification templates")
            try:
                load_templates()
                print("Templates loaded successfully")
            except Exception as e:
                print("Failed to templates: {}".format(str(e)))
                exit()
