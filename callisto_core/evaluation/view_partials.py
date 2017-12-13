from callisto_core.evaluation.models import EvalRow


class EvalDataMixin(object):

    def eval_action(self, action):
        EvalRow.store_eval_row(
            action=action,
            record=getattr(self, 'report', None),
            decrypted_record=getattr(self, 'decrypted_report', None),
        )
