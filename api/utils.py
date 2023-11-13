import os
from google.cloud.exceptions import NotFound

ALLOWED_EXTENSIONS = {"MP4", "WEBM", "AVI", "MPEG", "WMV"}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_user_folder(bucket, user):
    folder_path = f'{user}/'
    if not validate_folder_exists(bucket, folder_path):
        blob = bucket.blob(folder_path)
        blob.upload_from_string('')
    return folder_path

def validate_folder_exists(bucket, carpeta_path):
    try:
        blob = bucket.blob(carpeta_path)
        blob.reload()
        return True
    except NotFound:
        return False

def delete_file_cloud_storage(archivo_path, bucket):
    blob = bucket.blob(archivo_path)

    try:
        blob.delete()
        return True
    except Exception as e:
        print(f"Error al eliminar el archivo {archivo_path}: {e}")
        return False