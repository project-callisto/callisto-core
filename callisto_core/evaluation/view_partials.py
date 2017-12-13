from callisto_core.evaluation.models import EvalRow


class EvalDataMixin(object):

    def eval_action(self, action):
        EvalRow.store_eval_row(
            action=action,
            record=self.record,
            decrypted_record=self.decrypted_report,
        )
