import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.contrib.sites.models import Site


class DumpdataHackMixin(object):

    def running_dumpdata_command(self):
        import inspect
        from pprint import pprint
        pprint(inspect.stack())
        if len(sys.argv) > 1 and sys.argv[1] == 'dumpdata':
            return True
        else:
            print('!!!!!!!')
            print('!!!!!!!')
            print('!!!!!!!')
            print('!!!!!!!')
            print('!!!!!!!')
            return False


class PageBaseQuerySet(InheritanceQuerySet):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            site__id=site_id,
        )


class PageBaseManager(DumpdataHackMixin, InheritanceManager):

    def get_queryset(self):
        base_queryset = PageBaseQuerySet(self.model, using=self._db)
        if self.running_dumpdata_command():
            return base_queryset
        else:
            return base_queryset.select_subclasses()

    def on_site(self, site_id=None):
        return self.get_queryset().on_site(site_id)


class FormQuestionQuerySet(InheritanceQuerySet):
    pass


class FormQuestionManager(DumpdataHackMixin, InheritanceManager):

    def get_queryset(self):
        base_queryset = FormQuestionQuerySet(self.model, using=self._db)
        if self.running_dumpdata_command():
            return base_queryset
        else:
            return base_queryset.select_subclasses()
