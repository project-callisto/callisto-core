from callisto_core.evaluation.models import EvalRow


class EvalDataMixin(object):

    def dispatch(self, request, *args, **kwargs):
        eval_action_type = getattr(self, 'EVAL_ACTION_TYPE', None)
        if eval_action_type:
            self.eval_action(eval_action_type)
        return super().dispatch(request, *args, **kwargs)

    def eval_action(self, action):
        EvalRow.store_eval_row(
            action=action,
            record=getattr(self, 'report', None),
            decrypted_record=getattr(self, 'decrypted_report', None),
        )
