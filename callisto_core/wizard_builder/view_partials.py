'''

docs / reference:
    - https://docs.djangoproject.com/en/1.11/topics/class-based-views/

view_partials should define:
    - forms
    - models
    - helper classes
    - access checks
    - redirect handlers

and should not define:
    - templates
    - url names

'''
from django.contrib.sites.models import Site
from django.http.response import HttpResponseRedirect
from django.views import generic as views

from . import view_helpers


class WizardFormPartial(
    views.edit.FormView,
):
    storage_helper = view_helpers.StorageHelper

    @property
    def storage(self):
        return self.storage_helper(self)

    def get_site_id(self):
        try:
            return self.request.site.id
        except Site.DoesNotExist:
            return 1

    def get_forms(self):
        return self.storage.get_form_models()

    def get_serialized_forms(self):
        return self.storage.serialized_forms

    def dispatch(self, request, *args, **kwargs):
        self._dispatch_processing()
        return super().dispatch(request, *args, **kwargs)

    def _dispatch_processing(self):
        # TODO: rename to self.wizard_forms
        self.forms = self.get_forms()


class WizardPartial(
    WizardFormPartial,
    view_helpers.WizardViewTemplateHelpers,
):
    site_id = None
    url_name = None
    steps_helper = view_helpers.StepsHelper

    @property
    def steps(self):
        return self.steps_helper(self)

    @property
    def wizard_form(self):
        return WizardPartial.get_form(self)

    def get_form(self):
        if isinstance(self.steps.current, int):
            return self.forms[self.steps.current]
        else:
            return None

    def form_valid(self, form):
        form.full_clean()
        self.storage.update()
        self.steps.set_from_post()
        if self.steps.finished(self.steps.current):
            return self.render_form_done()
        elif self.steps.overflowed(self.steps.current):
            return self.render_last()
        else:
            return self.render_current()

    def get_context_data(self, **kwargs):
        if self.steps.current_is_done:
            self._rendering_done_hook()
            self.template_name = self.done_template_name
            kwargs['form'] = None
            kwargs['form_data'] = self.storage.cleaned_form_data
            return super().get_context_data(**kwargs)
        else:
            return super().get_context_data(**kwargs)

    def render_form_done(self):
        if self.steps.current_is_done:
            return self.render_finished()
        else:
            return self.render_done()

    def render_done(self):
        return HttpResponseRedirect(self.steps.done_url)

    def render_finished(self):
        return self.render_to_response(self.get_context_data())

    def render_last(self):
        return HttpResponseRedirect(self.steps.last_url)

    def render_current(self):
        return HttpResponseRedirect(self.steps.current_url)

    def _dispatch_processing(self):
        super()._dispatch_processing()
        step = self.kwargs.get('step')
        if step:
            self.curent_step = self.steps.parse_step(step)

    def _rendering_done_hook(self):
        pass
