"""
Shows basic usage of the Drive v3 API.

Creates a Drive v3 API service and prints the names and ids of the last 10 files
the user has access to.
"""

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload
from apiclient.http import MediaIoBaseUpload
import io
from optparse import OptionParser

def get_service():
    # Setup the Drive v3 API
    SCOPES = 'https://www.googleapis.com/auth/drive'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))
    return service

# print(help(service.files().list))
# print()

def get_file_id(service = None, print_files = False):
    if service is None: service = get_service()
    results = service.files().list(
        q="name='fitbit_data.db'",
        orderBy="modifiedTime",
        pageSize=10,
        fields="nextPageToken, files(id, name, version, mimeType, modifiedTime)"
        ).execute()
    items = results.get('files', [])
    ret = None

    if items:
        ret = items[len(items) - 1]["id"]

    if print_files:
        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                print('{0} ({1}) -type {2} -version {3} -modTime {4}'.format(item['name'], item['id'], item['mimeType'], item['version'], item['modifiedTime']))

    return ret

def download_file():
    service = get_service()
    file_id = get_file_id(service)
    print("fetching file with id: " + file_id)
    request = service.files().get_media(fileId=file_id)
    # print(request.to_json())
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Downloaded {}%.".format(int(status.progress() * 100)))

    with open("fitbit_data_temp.db", 'wb') as f:
        f.write(fh.getvalue())

    fh.close()

def upload_file():
    service = get_service()
    file_id = get_file_id(service)
    file_content = None
    with open("fitbit_data.db", 'rb') as f:
        file_content = f.read()

    fh = io.BytesIO(file_content)
    media = MediaIoBaseUpload(fh, 'application/octet-stream', )
    request = service.files().update(fileId=file_id, media_body=media)
    response = request.execute()
    print "Uploaded"

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        '-u', '--upload',
        action="store_true", dest="upload",
        help="upload to drive", default=False)
    parser.add_option(
        '-d', '--download',
        action="store_true", dest="download",
        help="download from drive", default=False)

    (options, args) = parser.parse_args()
    if options.upload and options.download:
        parser.error("-u and -d are exclusive")

    if not options.upload and not options.download:
        print "Listing files:"
        get_file_id(print_files = True)
    elif options.download:
        print "Downloading file"
        download_file()
    elif options.upload:
        print "Uploading file"
        upload_file()
