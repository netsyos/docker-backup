from __future__ import print_function
import sys
import os
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaFileUpload
import datetime;
import json


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/drive.file'
def main():
    folder_to_backup = sys.argv[1]
    file_to_backup = sys.argv[2]
    now = datetime.datetime.now()
    print(now.isoformat())
    path = os.path.realpath(sys.path[0])
    config_path = os.path.join(path, 'push2drive_config/config.json')
    credentials_path = os.path.join(path, 'push2drive_config/credentials.json')
    print(config_path)
    print(credentials_path)
    with open(config_path) as json_data_file:
        config = json.load(json_data_file)
    store = file.Storage(config['token_path'])
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(credentials_path, SCOPES)
        creds = tools.run_flow(flow, store)

    drive_service = build('drive', 'v3', http=creds.authorize(Http()))

    results = drive_service.files().list(q="name='%s' and mimeType='application/vnd.google-apps.folder'" % config['main_folder_name'],
                                          orderBy='createdTime asc',
                                          spaces='drive',
                                          fields='nextPageToken, files(id, name)'
                                          ).execute()
    items = results.get('files', [])


    main_folder_id = 0
    backup_folder_id = 0

    if not items:# Call the Drive v3 API
        print('Create main folder')
        file_metadata = {
            'name': config['main_folder_name'],
            'mimeType': 'application/vnd.google-apps.folder'
        }

        main_folder = drive_service.files().create(body=file_metadata,
                                            fields='id').execute()
        main_folder_id = main_folder.get('id')
        print('Folder ID: %s' % main_folder_id)
    else:
        for item in items:
            if item['name'] == config['main_folder_name']:
                main_folder_id = item['id']
            else:
                print(u'{0} ({1})'.format(item['name'], item['id']))

    if main_folder_id != 0:
        print('Main folder %s' % main_folder_id)
        results = drive_service.files().list(q="'{0}' in parents and mimeType='application/vnd.google-apps.folder'".format(main_folder_id),
                                              orderBy='createdTime asc',
                                              spaces='drive',
                                              pageSize=100,
                                              fields='nextPageToken, files(id, name)'
                                              ).execute()
        items = results.get('files', [])
        if items:
            for item in items:
                if item['name']==folder_to_backup:
                    backup_folder_id =  item['id']
        if backup_folder_id == 0:
            file_metadata = {
                'name': folder_to_backup,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [main_folder_id]
            }

            backup_folder = drive_service.files().create(body=file_metadata,
                                                fields='id').execute()
            backup_folder_id = backup_folder.get('id')
            print('Folder ID: %s' % backup_folder_id)
        else:
            print('Backup folder %s' % backup_folder_id)

        file_metadata = {
            'name': '{0}.{1}'.format(now.isoformat(),file_to_backup),
            'parents': [backup_folder_id]
        }
        media = MediaFileUpload(file_to_backup)
        backup_file = drive_service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        payload = "{\"text\":\"Backup finished (%s)\"}" % file_to_backup
        (resp, content) = Http().request(config['slack_url'],
                                "POST", body=payload,
                                headers={'content-type':'application/json'})
        print('File ID: %s' % backup_file.get('id'))
    else:
        print('No main folder error')



if __name__ == '__main__':
    main()
