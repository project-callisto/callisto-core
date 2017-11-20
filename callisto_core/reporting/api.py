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
            self._resolve_duplicate_owners,
            self._resolve_single_report,
            self._update_match_found,
        ]

    def find_matches(self, identifier):
        match_list = [
            potential_match_report
            for potential_match_report in self.match_reports
            if potential_match_report.get_match(identifier)
        ]
        for func in self.transforms:
            match_list = func(match_list)
        if match_list:
            logger.info(f"new matches({len(match_list)}) found")
        return match_list

    def _resolve_duplicate_owners(self, match_list):
        new_match_list = []
        report_owners = []

        for match in match_list:
            if match.report.owner not in report_owners:
                new_match_list.append(match)
                report_owners.append(match.report.owner)
            else:
                logger.debug("duplicate report owner")

        return new_match_list

    def _resolve_single_report(self, match_list):
        if len(match_list) == 1:
            logger.debug("no valid matches found")
            return []
        else:
            return match_list

    def _update_match_found(self, match_list):
        for match in match_list:
            match.report.match_found = True
            match.report.save()
        return match_list
