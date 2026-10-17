import datetime
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "run_page"))

from generator import Generator
from generator.db import Activity


def remote_activity(activity_id, name="Updated ride", kind="Ride"):
    return SimpleNamespace(
        id=activity_id,
        name=name,
        type=kind,
        start_latlng=None,
        location_country="Test location",
        distance=1000.0,
        moving_time=datetime.timedelta(minutes=5),
        elapsed_time=datetime.timedelta(minutes=6),
        start_date="2026-07-14 01:00:00+00:00",
        start_date_local="2026-07-14 09:00:00",
        average_heartrate=120.0,
        average_speed=3.3,
        map=SimpleNamespace(summary_polyline=""),
    )


class StravaReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.generator = Generator(":memory:")
        self.generator.check_access = Mock()
        self.generator.client = Mock()
        self.add_local(1)
        self.add_local(2)

    def tearDown(self):
        self.generator.session.close()
        self.generator.session.bind.dispose()

    def add_local(self, activity_id, source="strava", kind="Ride", start=None):
        self.generator.session.add(
            Activity(
                run_id=activity_id,
                name="Old ride",
                type=kind,
                source=source,
                start_date=start or "2026-07-14 01:00:00+00:00",
                start_date_local="2026-07-14 09:00:00",
            )
        )
        self.generator.session.commit()

    def ids(self):
        return {a.run_id for a in self.generator.session.query(Activity)}

    def sync(self, activities, **kwargs):
        self.generator.client.get_activities.return_value = iter(activities)
        self.generator.sync(True, prune_deleted=True, **kwargs)

    def test_merged_activity_replaces_deleted_daily_records_in_map(self):
        self.sync([remote_activity(3, "Merged trip")])
        self.assertEqual(self.ids(), {3})
        exported = self.generator.loadForMapping()
        self.assertEqual([a["run_id"] for a in exported], [3])
        self.assertEqual(exported[0]["name"], "Merged trip")

    def test_retained_activity_is_updated_and_missing_one_deleted(self):
        self.sync([remote_activity(1)])
        self.assertEqual(self.ids(), {1})
        activity = self.generator.session.get(Activity, 1)
        self.assertEqual(activity.name, "Updated ride")
        self.assertEqual(activity.distance, 1000)

    def test_other_sources_are_preserved(self):
        self.add_local(4, source="gpx")
        self.add_local(5, source=None)
        self.sync([remote_activity(1)])
        self.assertEqual(self.ids(), {1, 4, 5})

    def test_partial_api_pagination_does_not_change_database(self):
        def interrupted_pages():
            yield remote_activity(1)
            raise RuntimeError("Strava rate limit")

        self.generator.client.get_activities.return_value = interrupted_pages()
        with self.assertRaisesRegex(RuntimeError, "rate limit"):
            self.generator.sync(True, prune_deleted=True)
        self.assertEqual(self.ids(), {1, 2})
        self.assertEqual(self.generator.session.get(Activity, 1).name, "Old ride")

    def test_empty_api_result_does_not_delete_everything(self):
        with self.assertRaisesRegex(ValueError, "no activities"):
            self.sync([])
        self.assertEqual(self.ids(), {1, 2})

    def test_invalid_activity_rolls_back_earlier_updates(self):
        invalid = remote_activity(3)
        invalid.average_speed = "invalid"
        with self.assertRaises(ValueError):
            self.sync([remote_activity(1), invalid])
        self.assertEqual(self.ids(), {1, 2})
        self.assertEqual(self.generator.session.get(Activity, 1).name, "Old ride")

    def test_only_run_does_not_prune_other_sports(self):
        self.add_local(3, kind="Run")
        self.add_local(4, kind="Run")
        self.generator.only_run = True
        self.sync([remote_activity(3, kind="Run")])
        self.assertEqual(self.ids(), {1, 2, 3})

    def test_incremental_fetch_cannot_prune(self):
        with self.assertRaisesRegex(ValueError, "full Strava sync"):
            self.generator.sync(False, prune_deleted=True)
        self.generator.check_access.assert_not_called()

    def test_future_activity_outside_snapshot_is_preserved(self):
        self.add_local(3, start="2099-01-01 00:00:00+00:00")
        self.sync([remote_activity(1)])
        self.assertEqual(self.ids(), {1, 3})

    def test_missing_records_are_kept_without_prune_flag(self):
        self.generator.client.get_activities.return_value = [remote_activity(1)]
        self.generator.sync(True)
        self.assertEqual(self.ids(), {1, 2})

    def test_changed_dates_are_updated(self):
        activity = remote_activity(1)
        activity.start_date = "2026-07-15 01:00:00+00:00"
        activity.start_date_local = "2026-07-15 09:00:00"
        self.sync([activity])
        saved = self.generator.session.get(Activity, 1)
        self.assertEqual(saved.start_date, activity.start_date)
        self.assertEqual(saved.start_date_local, activity.start_date_local)


if __name__ == "__main__":
    unittest.main()
