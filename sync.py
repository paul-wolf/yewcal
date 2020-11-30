import s3fs

import constants


def get_s3():
    return s3fs.S3FileSystem(key=constants.AWS_ACCESS_KEY_ID, secret=constants.AWS_SECRET_ACCESS_KEY)

def remote_path():
    return f"{constants.BUCKET}/{constants.USERNAME}/events.json"

def push_event_data():
    get_s3().put(constants.EVENTS_DATA_PATH, remote_path())

def get_event_data():
    get_s3().get_file(remote_path(), constants.EVENTS_DATA_PATH)
    
