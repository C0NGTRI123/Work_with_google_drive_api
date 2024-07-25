import pickle
import os.path
import io
import shutil
import time
from mimetypes import MimeTypes
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']


class DriveAPI:
    def __init__(self):
        self.creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('drive', 'v3', credentials=self.creds)

    def get_items(self):
        results = self.service.files().list(
            pageSize=100, fields="files(id, name)").execute()
        items = results.get('files', [])
        return items

    def ListFiles(self):
        items = self.get_items()
        print("Here's a list of files: \n")
        print(*items, sep="\n", end="\n\n")
        return items

    def FileDownload(self, file_id, folder_path):
        file_metadata = self.service.files().get(fileId=file_id, fields='size').execute()
        file_size = int(file_metadata.get('size', 0))

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        # Initialise a downloader object to download the file
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        try:
            start_time = time.time()  # Record start time
            while not done:
                status, done = downloader.next_chunk()
                total_bytes_downloaded = status.resumable_progress
                elapsed_time = time.time() - start_time
                download_speed = total_bytes_downloaded / elapsed_time if elapsed_time > 0 else 0
                estimated_time = (file_size - total_bytes_downloaded) / download_speed if download_speed > 0 else 0
                print(f"Downloaded {total_bytes_downloaded} bytes out of {file_size} bytes. Download Speed: {download_speed:.2f} bytes/sec")
                print(f"Download {int(status.progress() * 100)}%. Estimated time remaining: {estimated_time:.2f} sec")

            fh.seek(0)
            if folder_path == "":
                folder_path = os.getcwd()
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            items = self.get_items()
            file_name = [item['name'] for item in items if item['id'] == file_id][0]
            file_name = os.path.join(folder_path, file_name)
            with open(file_name, 'wb') as f:
                shutil.copyfileobj(fh, f)
            print("File Downloaded")
            return True
        except:
            print("Something went wrong.")
            return False

    def FileUpload(self, filepath):
        name = filepath.split('/')[-1]
        mimetype = MimeTypes().guess_type(name)[0]

        # create file metadata
        file_metadata = {'name': name}
        start_all_time = time.time()

        try:
            file_size = os.path.getsize(filepath)
            start_time = time.time()
            media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)
            request = self.service.files().create(body=file_metadata, media_body=media, fields='id')
            response = None

            while response is None:
                status, response = request.next_chunk()
                if status:
                    total_bytes_uploaded = status.resumable_progress
                    elapsed_time = (time.time() - start_time)  # Calculate elapsed time in hours
                    upload_speed = (total_bytes_uploaded / elapsed_time) if elapsed_time > 0 else 0  # Calculate upload speed in MB/sec
                    estimated_time = (file_size - total_bytes_uploaded) / upload_speed if upload_speed > 0 else 0  # Calculate estimated time remaining in seconds
                    print(f"Uploaded {total_bytes_uploaded} bytes out of {file_size} bytes. Upload Speed: {upload_speed:.2f} bytes/sec. Estimated time remaining: {estimated_time:.2f} sec")
                    print(f"Upload {int(status.progress() * 100)}% complete.")
            end_all_time = time.time()
            print(f"Total time taken: {end_all_time - start_all_time} sec")
        except Exception as e:
            raise Exception(f"UploadError: {e}")

    def FileDelete(self, file_id):
        try:
            self.service.files().delete(fileId=file_id).execute()
            print("File deleted successfully.")
        except Exception as e:
            raise Exception(f"DeleteError: {e}")


if __name__ == "__main__":
    obj = DriveAPI()
    while True:
        i = int(input("Enter your choice:\n1. Download file \n2. Upload File \n3. Delete File \n4. List file \n5. Exit\n"))

        if i == 1:
            f_id = input("Enter file id: ")
            f_name = input("Enter folder path: ")
            obj.FileDownload(f_id, f_name)

        elif i == 2:
            f_path = input("Enter full file path: ")
            obj.FileUpload(f_path)

        elif i == 3:
            f_id = input("Enter file id: ")
            obj.FileDelete(f_id)

        elif i == 4:
            obj.ListFiles()

        elif i == 5:
            exit()

        else:
            print("Invalid choice. Please try again.")
