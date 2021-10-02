import shows_db
import updates
from tvmaze import TvMazeApi


def handle(event, context):
    tvmaze_api = TvMazeApi()
    tvmaze_updates = tvmaze_api.get_day_updates()

    for tvmaze_id in tvmaze_updates:
        try:
            shows_db.get_show_by_api_id("tvmaze", tvmaze_id)
        except shows_db.NotFoundError:
            # Show not present in db, exclude it from updates
            continue

        # Post to SNS topic
        updates.publish_show_update("tvmaze", tvmaze_id)


