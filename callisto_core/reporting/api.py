import logging

logger = logging.getLogger(__name__)


class CallistoCoreMatchingApi(object):

    @property
    def match_reports(_):
        from callisto_core.delivery.models import MatchReport
        return MatchReport.objects.all()

    @property
    def transforms(self):
        return [
            self._resolve_decryptable_reports,
            self._resolve_duplicate_owners,
            self._resolve_single_report,
            self._resolve_already_matched,
            self._update_match_found,
        ]

    def find_matches(self, identifier):
        self.identifier = identifier
        match_list = self.match_reports

        logger.debug(f'all reports => match_reports:{len(match_list)}')
        for func in self.transforms:
            if match_list:
                match_list = func(match_list)
                logger.debug(f'post {func.__name__} => {match_list}')

        if match_list:
            logger.info(f"matches found => match_reports:{len(match_list)}")

        return match_list

    def _resolve_decryptable_reports(self, match_list):
        return [
            match_report
            for match_report in match_list
            if match_report.get_match(self.identifier)
        ]

    def _resolve_duplicate_owners(self, match_list):
        new_match_list = []
        report_owners = []

        for match in match_list:
            if match.report.owner not in report_owners:
                new_match_list.append(match)
                report_owners.append(match.report.owner)

        return new_match_list

    def _resolve_single_report(self, match_list):
        if len(match_list) == 1:
            return []
        else:
            return match_list

    def _resolve_already_matched(self, match_list):
        return [
            match_report
            for match_report in match_list
            if not match_report.report.match_found
        ]

    def _update_match_found(self, match_list):
        for match in match_list:
            match.report.match_found = True
            match.report.save()
        return match_list
