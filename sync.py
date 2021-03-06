import os

import s3fs
import arrow

import constants


def get_s3(context):
    return s3fs.S3FileSystem(
        key=context.get("AWS_ACCESS_KEY_ID"),
        secret=context.get("AWS_SECRET_ACCESS_KEY"),
    )


def remote_path(context):
    return (
        f"{context.get('BUCKET')}/{context.get('USERNAME')}/{constants.EVENTS_FILENAME}"
    )


def push_event_data(context):
    get_s3(context).put(context.get("events_data_path"), remote_path(context))


def get_event_data(context):

    data = get_s3(context).info(remote_path(context))
    remote_dt = data.get("LastModified")
    local_events_path = context.get("events_data_path")
    print(f"Remote file time : {arrow.get(remote_dt)}")
    if os.path.exists(local_events_path):
        print(f"Local file time  : {arrow.get(os.path.getmtime(local_events_path))}")
        if not arrow.get(remote_dt) < arrow.get(
            os.path.getmtime(context.get("events_data_path"))
        ):
            print("Remote is older than local, aborting")
            return

    get_s3(context).get_file(remote_path(context), context.get("events_data_path"))
