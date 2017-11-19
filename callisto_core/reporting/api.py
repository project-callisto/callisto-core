import logging

from callisto_core.utils import api

logger = logging.getLogger(__name__)


class CallistoCoreMatchingApi(object):

    @property
    def match_reports(_):
        from callisto_core.delivery.models import MatchReport
        return MatchReport.objects.all()

    def find_matches(self, match_report, identifier, to_coordinators):
        """Finds sets of matching records that haven't been identified yet. For a match to count as new, there must be
        associated Reports from at least 2 different users and at least one MatchReport must be newly created since
        we last checked for matches.

        Args:
          match_reports_to_check (list of MatchReports): the MatchReports to check for matches
        """
        match_list = [
            potential_match_report
            for potential_match_report in self.match_reports
            if potential_match_report.get_match(identifier)
        ]
        if len(match_list) > 1:
            self._filter_match_list(match_list, identifier, to_coordinators)
        for match in match_list:
            match.seen = True
            match.save()

    def _filter_match_list(match_list, identifier, to_coordinators):
        seen_match_owners = [
            match.report.owner for match in match_list
            if match.seen
        ]
        new_match_owners = [
            match.report.owner for match in match_list
            if not match.seen
        ]
        # filter out multiple reports made by the same person
        if len(set(seen_match_owners + new_match_owners)) > 1:
            # only send notifications if new matches are submitted by
            # owners we don't know about
            if not set(new_match_owners).issubset(
                    set(seen_match_owners)):
                self._process_new_matches(
                    match_list, identifier, to_coordinators)
            for matched_report in match_list:
                matched_report.report.match_found = True
                matched_report.report.save()

    def _process_new_matches(self, matches, identifier, to_coordinators):
        logger.info("new match found")
        owners_notified = []
        for match_report in matches:
            owner = match_report.report.owner
            # dont notify report owners twice for a single match
            if owner not in owners_notified:
                self._notify_owner(owner, match_report)
                owners_notified.append(owner)
        self._notify_authority(matches, identifier, to_coordinators)

    def _notify_authority(self, matches, identifier, to_coordinators):
        api.NotificationApi.send_matching_report_to_authority(
            matches, identifier, to_coordinators)

    def _notify_owner(self, owner, match_report):
        api.NotificationApi.send_match_notification(owner, match_report)
