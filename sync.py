import os

import s3fs
import arrow

import constants


def get_s3():
    return s3fs.S3FileSystem(
        key=constants.AWS_ACCESS_KEY_ID, secret=constants.AWS_SECRET_ACCESS_KEY
    )


def remote_path():
    return f"{constants.BUCKET}/{constants.USERNAME}/{constants.EVENTS_FILENAME}"


def push_event_data():
    get_s3().put(constants.EVENTS_DATA_PATH, remote_path())


def get_event_data():

    data = get_s3().info(remote_path())
    remote_dt = data.get("LastModified")
    print(f"Remote file time : {arrow.get(remote_dt)}")
    print(
        f"Local file time  : {arrow.get(os.path.getmtime(constants.EVENTS_DATA_PATH))}"
    )
    if arrow.get(remote_dt) < arrow.get(os.path.getmtime(constants.EVENTS_DATA_PATH)):
        print("Remote is older than local, aborting")
        raise SystemExit
    else:
        get_s3().get_file(remote_path(), constants.EVENTS_DATA_PATH)
