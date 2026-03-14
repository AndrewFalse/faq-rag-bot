from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from rag_bot.config import settings

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "application/vnd.google-apps.document",
}

FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_DOCS_MIME = "application/vnd.google-apps.document"

TMP_DIR = Path("/tmp/rag_docs")

# Русские названия папок -> внутренние коды тем
_FOLDER_NAME_TO_TOPIC: dict[str, str] = {
    "РПД": "RPD",
    "ГИА": "GEA",
}


class GoogleDriveClient:
    def __init__(self) -> None:
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_JSON,
            scopes=SCOPES,
        )
        self._service = build("drive", "v3", credentials=creds)

    def list_files_in_folder(self, folder_id: str) -> list[dict]:
        query = (
            f"'{folder_id}' in parents"
            f" and mimeType != '{FOLDER_MIME}'"
            " and trashed = false"
        )
        files: list[dict] = []
        page_token: str | None = None

        while True:
            resp = (
                self._service.files()
                .list(
                    q=query,
                    fields="nextPageToken, files(id, name, modifiedTime, mimeType)",
                    pageSize=1000,
                    pageToken=page_token,
                )
                .execute()
            )

            for f in resp.get("files", []):
                if f["mimeType"] in ALLOWED_MIME_TYPES:
                    files.append(
                        {
                            "id": f["id"],
                            "name": f["name"],
                            "modifiedTime": f["modifiedTime"],
                            "mimeType": f["mimeType"],
                        }
                    )

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return files

    def get_topic_folders(self) -> dict[str, str]:
        root = settings.GOOGLE_DRIVE_ROOT_FOLDER_ID
        query = (
            f"'{root}' in parents"
            f" and mimeType = '{FOLDER_MIME}'"
            " and trashed = false"
        )
        resp = (
            self._service.files()
            .list(q=query, fields="files(id, name)", pageSize=100)
            .execute()
        )

        result: dict[str, str] = {}
        for folder in resp.get("files", []):
            topic = _FOLDER_NAME_TO_TOPIC.get(folder["name"])
            if topic:
                result[topic] = folder["id"]

        return result

    def download_file(self, file_id: str, filename: str, mime_type: str) -> str:
        TMP_DIR.mkdir(parents=True, exist_ok=True)

        if mime_type == GOOGLE_DOCS_MIME:
            request = self._service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            out_path = TMP_DIR / f"{file_id}.docx"
        else:
            request = self._service.files().get_media(fileId=file_id)
            out_path = TMP_DIR / filename

        with open(out_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        return str(out_path)

    @staticmethod
    def delete_local_file(path: str) -> None:
        p = Path(path)
        if p.exists():
            p.unlink()
