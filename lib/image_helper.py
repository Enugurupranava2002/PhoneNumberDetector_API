import os
import re
import traceback
from typing import Union
from werkzeug.datastructures import FileStorage
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from flask_uploads import UploadSet, IMAGES

IMAGE_SET = UploadSet('images', IMAGES) 

def save_image(image: FileStorage, folder: str = None, name: str = None) -> str:
    """Takes a filestorage andd saves in to a folder"""
    return IMAGE_SET.save(image, folder, name) # this will be saved in the disk

def get_path(filename: str = None, folder: str = None) -> str:
    """Take image name and folder and return full path"""
    return IMAGE_SET.path(filename, folder)

def find_image_any_format(filename: str, folder: str) -> Union[str, None]:
    """Take a filename and return an image on any of the accepted formats."""
    for _format in IMAGES:
        image = f"{filename}.{_format}"
        image_path = IMAGE_SET.path(filename=image, folder=folder)
        if os.path.isfile(image_path): # checks wether given path there exits file or not.
            return image_path
    return None

def _retriew_filename(file: Union[str, FileStorage]) -> str:
    """Take filestorage and return the file name."""
    if isinstance(file, FileStorage):
        return file.filename
    return file

def is_filename_safe(file: Union[str, FileStorage]) -> bool:
    """Check our regex and return wether the string 
    matches or not."""
    filename = _retriew_filename(file)
    allowed_format = "|".join(IMAGES)
    regex = f"^[A-Za-z0-9][A-Za-z0-9_()-\.]*\.({allowed_format})$" 
    return re.match(regex, filename) is not None

def get_basename(file: Union[str, FileStorage]) -> str:
    """Return full name of image in the path 
    get_basename('some/folder/image.jpg') 
    returns 'image.py'"""
    filename = _retriew_filename(file)
    return os.path.split(filename)[1]

def get_extension(file: Union[str, FileStorage]) -> str:
    """Return file extension 
    get_extension('image.jpg') returns '.jpg'"""
    filename = _retriew_filename(file)
    return os.path.split(filename)[0]

def upload_to_gd(filename: str, file_path: str, user_id: int):
    settings_path = 'settings.yaml'
    guth = GoogleAuth(settings_file=settings_path)
    # guth.LocalWebserverAuth()

    drive = GoogleDrive(guth)

    folder = f"user_data_{user_id}"
    folder_id = ""
    file_list = drive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()
    for file in file_list:
        if file['title'] == folder:
            folder_id = file["id"]
    if folder_id == "":
        file = drive.CreateFile({
            'title': folder,
            'mimeType' : 'application/vnd.google-apps.folder'
        })
        file.Upload()
        folder_id = file['id']
    try:
        file = drive.CreateFile({'title': filename, 'mimeType': 'image/jpeg', "parents":  [{"id": folder_id}]})
        file.SetContentFile(f"app/static/images/user_data_{user_id}/{filename}")
        file.Upload()
    except:
        traceback.print_exc()
        return {"message": "failed to upload."}