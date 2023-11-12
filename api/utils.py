import os
from google.cloud.exceptions import NotFound

ALLOWED_EXTENSIONS = {"MP4", "WEBM", "AVI", "MPEG", "WMV"}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_user_folder(path_root, user):
    path_filename = os.path.join(path_root, user)
    if not os.path.exists(path_filename):
        os.makedirs(path_filename)
    return path_filename