import django.apps
from django.db import connections


class DatabaseRouter(object):
    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'auth' and \
                        obj2._meta.app_label == 'auth':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default' and app_label != 'command'
