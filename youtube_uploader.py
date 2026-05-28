import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    def __init__(self, credentials_dir="data/credentials"):
        self.credentials_dir = credentials_dir
        if not os.path.exists(credentials_dir):
            os.makedirs(credentials_dir)
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    def get_service(self, channel_id):
        creds = None
        token_path = os.path.join(self.credentials_dir, f"token_{channel_id}.pickle")

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Nota: En un entorno de servidor real, esto debería manejar el flujo OAuth web
                # Para la app Streamlit, facilitaremos el proceso de login
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', self.scopes)
                creds = flow.run_local_server(port=0)

            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        return build("youtube", "v3", credentials=creds)

    def upload_video(self, channel_id, file_path, title, description, tags=None, category_id="22", privacy_status="private"):
        youtube = self.get_service(channel_id)

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or [],
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }

        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
        )

        response = insert_request.execute()
        return response.get('id')
