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

    data = get_s3().info(remote_path())
    remote_dt = data.get("LastModified")
    print(f"Remote file time : {arrow.get(remote_dt)}")
    print(
        f"Local file time  : {arrow.get(os.path.getmtime(context.get('events_data_path')))}"
    )
    if arrow.get(remote_dt) < arrow.get(
        os.path.getmtime(context.get("events_data_path"))
    ):
        print("Remote is older than local, aborting")
        raise SystemExit
    else:
        get_s3().get_file(remote_path(context), context.get("events_data_path"))
