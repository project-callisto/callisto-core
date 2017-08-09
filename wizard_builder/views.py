from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from .forms import PageFormManager
from .models import Page
from .storage import SessionStorage

# from django-formtools
# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE


class StepsHelper(object):

    def __init__(self, wizard):
        self._wizard = wizard

    def __dir__(self):
        return self.all

    def __len__(self):
        return self.count

    def __repr__(self):
        return '<StepsHelper for %s (steps: %s)>' % (self._wizard, self.all)

    @property
    def all(self):
        "Returns the names of all steps/forms."
        return list(self._wizard.get_form_list())

    @property
    def count(self):
        "Returns the total number of steps/forms in this the wizard."
        return len(self.all)

    @property
    def current(self):
        """
        Returns the current step. If no current step is stored in the
        storage backend, the first step will be returned.
        """
        return self._wizard.storage.current_step or self.first

    @property
    def first(self):
        "Returns the name of the first step."
        return self.all[0]

    @property
    def last(self):
        "Returns the name of the last step."
        return self.all[-1]

    def step_key(self, adjustment):
        form_list = self._wizard.get_form_list()
        keys = list(form_list.keys())
        key = self.step_key + adjustment
        if len(keys) > key:
            return keys[key]
        else:
            return None

    @property
    def next(self):
        return self.step_key(1)

    @property
    def prev(self):
        return self.step_key(-1)

    @property
    def step(self):
        return self._wizard.steps.current

    @property
    def index(self):
        return list(self._wizard.get_form_list().keys()).index(self.step)

    @property
    def step0(self):
        return int(self.index)

    @property
    def step1(self):
        return int(self.index) + 1


class RenderMixin(object):

    def render(self, form=None, **kwargs):
        """
        Returns a ``HttpResponse`` containing all needed context data.
        """
        form = form or self.get_form()
        context = self.get_context_data(form=form, **kwargs)
        return self.render_to_response(context)

    def render_next_step(self, form, **kwargs):
        self.storage.current_step = self.steps.next
        return redirect(self.get_step_url(self.steps.next))

    def render_goto_step(self, goto_step, **kwargs):
        self.storage.current_step = goto_step
        return redirect(self.get_step_url(goto_step))

    def render_revalidation_failure(self, step, form, **kwargs):
        self.storage.current_step = failed_step
        return redirect(self.get_step_url(failed_step))

    def render_done(self, form, **kwargs):
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key))
            # don't reject form if it's not bound (modification from original)
            if form_obj.is_bound and not form_obj.is_valid():
                return self.render_revalidation_failure(
                    form_key,
                    form_obj,
                    **kwargs,
                )
            final_forms[form_key] = form_obj

        # hook to allow processing of answers before done
        self.process_answers(final_forms.values())

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        done_response = self.done(
            final_forms.values(),
            form_dict=final_forms,
            **kwargs)
        self.storage.reset()
        return done_response


class RoutingMixin(object):

    def dispatch(self, request, *args, **kwargs):
        # add the storage engine to the current wizardview instance
        self.prefix = self.get_prefix(request, *args, **kwargs)
        self.storage = SessionStorage(
            self.prefix,
            request,
            self.file_storage
        )
        self.steps = self.steps_helper(self)
        response = super().dispatch(request, *args, **kwargs)

        # update the response (e.g. adding cookies)
        self.storage.update_response(response)
        return response

    def get(self, request, *args, **kwargs):
        step_url = kwargs.get('step', None)
        if step_url is None:
            if 'reset' in self.request.GET:
                self.storage.reset()
                self.storage.current_step = self.steps.first
            if self.request.GET:
                query_string = "?%s" % self.request.GET.urlencode()
            else:
                query_string = ""
            return redirect(
                self.get_step_url(
                    self.steps.current) +
                query_string)

        # is the current step the "done" name/view?
        elif step_url == self.done_step_name:
            last_step = self.steps.last
            form = self.get_form(
                step=last_step,
                data=self.storage.get_step_data(last_step),
                files=self.storage.get_step_files(last_step),
            )
            return self.render_done(form, **kwargs)

        # is the url step name not equal to the step in the storage?
        # if yes, change the step in the storage (if name exists)
        elif step_url == self.steps.current:
            # URL step name and storage step name are equal, render!
            form = self.get_form(
                data=self.storage.current_step_data,
                files=self.storage.current_step_files,
            )
            return self.render(form, **kwargs)

        elif step_url in self.get_form_list():
            self.storage.current_step = step_url
            return self.render(
                self.get_form(
                    data=self.storage.current_step_data,
                    files=self.storage.current_step_files,
                ),
                **kwargs
            )

        # invalid step name, reset to first and redirect.
        else:
            self.storage.current_step = self.steps.first
            return redirect(self.get_step_url(self.steps.first))

    def post(self, *args, **kwargs):
        form_current_step = self.request.POST.get('current_step')
        if (
            form_current_step != self.steps.current and
            self.storage.current_step is not None
        ):
            # form refreshed, change current step
            self.storage.current_step = form_current_step

        # get the form for the current step
        form = self.get_form(data=self.request.POST, files=self.request.FILES)

        # and try to validate
        if form.is_valid():
            # if the form is valid, store the cleaned data and files.
            self.storage.set_step_data(
                self.steps.current,
                form.data,
            )
            self.storage.set_step_files(
                self.steps.current,
                form.files,
            )

            # this check was moved from beginning of the method (modification
            # from original)
            wizard_goto_step = self.request.POST.get('wizard_goto_step', None)
            if wizard_goto_step and wizard_goto_step in self.get_form_list():
                return self.render_goto_step(wizard_goto_step)

            # check if the current step is the last step
            # render done if "skip to end" has been sent (modification from
            # original)
            if self.steps.current == self.steps.last or wizard_goto_step == "end":
                # no more steps, render done view
                return self.render_done(form, **kwargs)
            else:
                # proceed to the next step
                return self.render_next_step(form)
        return self.render(form)


class ConfigurableFormWizard(RenderMixin, RoutingMixin, TemplateView):
    form_list = None
    initial_dict = None
    instance_dict = None
    condition_dict = None
    url_name = None
    template_name = 'wizard_builder/wizard_form.html'
    done_step_name = 'done'
    steps_helper = StepsHelper

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: don't define self values before init???
        self.processed_answers = []
        self.form_to_edit = self.get_form_to_edit(self.object_to_edit)

    @classmethod
    def wizard_factory(cls, object_to_edit=None, site_id=None, **kwargs):
        pages = Page.objects.on_site(site_id).all()
        formsets = {}
        items = {}
        # TODO: make this for loop a manager method
        for idx, page in enumerate(pages):
            for question in page.questions:
                items[question.field_id] = question
        # TODO: smell this type
        return type(
            cls.__name__,
            (cls,),
            {
                "items": items,
                "form_list": PageFormManager.forms(pages),
                "object_to_edit": object_to_edit,
                "formsets": formsets,
                "page_count": len(pages),
            },
        )

    def get_form(self, step=None, data=None, files=None):
        """
        Constructs the form for a given `step`. If no `step` is defined, the
        current step will be determined automatically.

        The form will be initialized using the `data` argument to prefill the
        new form. If needed, instance or queryset (for `ModelForm` or
        `ModelFormSet`) will be added too.
        """
        if step is None:
            step = self.steps.current
        form = self.form_list[step]
        for name, value in {
            'data': data,
            'files': files,
            'prefix': self.get_form_prefix(step),
            'initial': self.get_form_initial(step),
        }.items():
            setattr(form, name, value)
        return form

    def get_form_instance(self, step):
        return self.instance_dict.get(step, None)

    def get_form_prefix(self, step=None):
        if step is None:
            step = self.steps.current
        return str(step)

    def get_form_to_edit(self, object_to_edit):
        return []

    def get_form_list(self):
        form_list = OrderedDict()
        for form_key, form_class in self.form_list:
            # try to fetch the value from condition list, by default, the form
            # gets passed to the new list.
            condition = self.condition_dict.get(form_key, True)
            if callable(condition):
                # call the value if needed, passes the current instance.
                condition = condition(self)
            if condition:
                form_list[form_key] = form_class
        return form_list

    def process_answers(self, form_list):
        for form in form_list:
            self.processed_answers.append(form.processed)

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context.update(self.storage.extra_data)
        context.update({
            'page_count': self.page_count,
            'current_page': form.page_index,
            'editing': self.object_to_edit,
            'wizard': {
                'form': form,
                'steps': self.steps,
                'current_step': self.steps.current,
                'url_name': self.url_name,
            }
        })
        return context

    def get_form_initial(self, step):
        if self.form_to_edit:
            return self._process_non_formset_answers_for_edit(
                self.form_to_edit,
            )
        else:
            return self.initial_dict.get(step, {})

    def get_prefix(self, request, *args, **kwargs):
        identifier = str(self.object_to_edit.id) if self.object_to_edit else ""
        return "form_wizard" + identifier

    def get_step_url(self, step):
        kwargs = {'step': step}
        if self.object_to_edit:
            kwargs['edit_id'] = self.object_to_edit.id
        return reverse(self.url_name, kwargs=kwargs)

    def done(self, form_list, **kwargs):
        if kwargs.get('step', None) != self.done_step_name:
            return redirect(self.get_step_url(self.done_step_name))
        else:
            return self.render_done(form, **kwargs)

    def _process_non_formset_answers_for_edit(self, json_questions):
        answers = {}
        for question in json_questions:
            answer = question.get('answer')
            question_id = question.get('id')
            if answer and question_id:
                # TODO: smell this string interpolation
                answers["question_%i" % question_id] = answer
                extra = question.get('extra')
                if extra:
                    extra_answer = extra.get('answer')
                    if extra_answer:
                        answers['question_%i_extra-%s' %
                                (question_id, answer)] = extra_answer
        return answers

    def _process_formset_answers_for_edit(self, json_questions, page_id):
        answers = []
        # TODO: smell this next
        formset = next(
            (i for i in json_questions if i.get('page_id') == page_id), None)
        if formset:
            for form in formset.get('answers'):
                answers.append(
                    self._process_non_formset_answers_for_edit(form))
        return answers
