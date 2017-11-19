import logging

from callisto_core.utils import api

logger = logging.getLogger(__name__)


class CallistoCoreMatchingApi(object):

    @property
    def match_reports(_):
        from callisto_core.delivery.models import MatchReport
        return MatchReport.objects.all()

    def find_matches(self, identifier, to_coordinators):
        match_list = [
            potential_match_report
            for potential_match_report in self.match_reports
            if potential_match_report.get_match(identifier)
        ]
        match_list = self._update_seen(match_list)
        match_list = self._resolve_duplicate_owners(match_list)
        match_list = self._resolve_single_report(match_list)
        return match_list

    def _update_seen(self, match_list):
        for match in match_list:
            match.seen = True
            match.save()
        return match_list

    def _resolve_duplicate_owners(self, match_list):
        new_match_list = []
        report_owners = []

        for match in match_list:
            if not match.report.owner in report_owners:
                new_match_list.append(match)
                report_owners.append(match.report.owner)

        return new_match_list

    def _resolve_single_report(self, match_list):
        if len(match_list) == 1:
            return []
        else:
            return match_list

    def _update_found_matches(self, match_list):
        for match in match_list:
            match.report.match_found = True
            match.report.save()
        return match_list

    def _process_new_matches(self, matches, identifier, to_coordinators):
        logger.info("new match found")
        for match_report in matches:
            self._notify_owner(match_report)
        self._notify_authority(matches, identifier, to_coordinators)

    def _notify_authority(self, matches, identifier, to_coordinators):
        api.NotificationApi.send_matching_report_to_authority(
            matches, identifier, to_coordinators)

    def _notify_owner(self, match_report):
        api.NotificationApi.send_match_notification(match_report)
