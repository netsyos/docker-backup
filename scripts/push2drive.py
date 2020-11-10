from __future__ import print_function
import sys
import os
import time
import gc
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaFileUpload
import datetime;
import json


# If modifying these scopes, delete the file token.json.
# full scope : https://www.googleapis.com/auth/drive
SCOPES = 'https://www.googleapis.com/auth/drive.file'

class BackupManager:
    now = datetime.datetime.now()
    scopes = 'https://www.googleapis.com/auth/drive.file'
    config_path = 'push2drive_config/config.json'
    credentials_path = 'push2drive_config/credentials.json'
    token_path = 'push2drive_config/token.json'
    config = 0
    drive_service = 0


    backup_number = 0
    main_folder_id = 0
    destination_folder_id = 0
    backup_folder_id = 0

    def __init__(self, path):
        self.config_path = os.path.join(path, 'push2drive_config/config.json')
        self.credentials_path = os.path.join(path, 'push2drive_config/credentials.json')

    def read_config(self):
        with open(self.config_path) as json_data_file:
            self.config = json.load(json_data_file)
        return self.config

    def connect_drive(self):
        store = file.Storage(self.config['token_path'])
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(self.credentials_path, SCOPES)
            creds = tools.run_flow(flow, store)
        self.drive_service = build('drive', 'v3', http=creds.authorize(Http()))

    def check_main_folder(self):
        # Search main backup folder in drive
        main_folder_name = self.config['main_folder_name']
        print('Search main backup folder in drive (name:%s)' % main_folder_name)
        results = self.drive_service.files().list(q="name='%s' and mimeType='application/vnd.google-apps.folder'" % main_folder_name,
                                            orderBy='createdTime asc',
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name)'
                                            ).execute()
        items = results.get('files', [])

        if not items:
            # No Backup folder found by name
            print('Create main folder')
            file_metadata = {
                'name': main_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            main_folder = self.drive_service.files().create(body=file_metadata,
                                                fields='id').execute()
            self.main_folder_id = main_folder.get('id')
            print('Folder ID: %s' % self.main_folder_id)
        else:
            # Backup folder ok
            for item in items:
                if item['name'] == main_folder_name:
                    self.main_folder_id = item['id']
                else:
                    print(u'{0} ({1})'.format(item['name'], item['id']))
            
            print('Main folder found (id:%s)' % self.main_folder_id)
        
        if self.main_folder_id == 0:
            raise BaseException('No main folder')
        return 1

    def check_destination_folder(self):
        destination_folder_name = self.config['destination_folder_name']
        print('Search destination folder in drive (name:%s)' % destination_folder_name)
        # Backup folder ok
        if self.main_folder_id == 0:
            raise BaseException('No main folder')
        else:
            # Search sub folders
            results = self.drive_service.files().list(q="'{0}' in parents and mimeType='application/vnd.google-apps.folder'".format(self.main_folder_id),
                                                orderBy='createdTime asc',
                                                spaces='drive',
                                                pageSize=100,
                                                fields='nextPageToken, files(id, name)'
                                                ).execute()
            items = results.get('files', [])

            # Search folder for existing folder
            if items:
                for item in items:
                    if item['name']==destination_folder_name:
                        self.destination_folder_id =  item['id']
            
            # Create eventually
            if self.destination_folder_id == 0:
                print('Create destination folder')
                file_metadata = {
                    'name': destination_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.main_folder_id]
                }

                destination_folder = self.drive_service.files().create(body=file_metadata,
                                                    fields='id').execute()
                self.destination_folder_id = destination_folder.get('id')
            
            if self.destination_folder_id == 0:
                raise BaseException('No destination folder')
            else:
                print('Destination folder found (id:%s)' % self.destination_folder_id)
        return 1

    def get_backup_number(self):
        data = self.drive_service.files().get(fileId=self.destination_folder_id, fields="appProperties").execute()
        print(data)
        if 'appProperties' in data and 'backup_number' in data['appProperties']:
            self.backup_number = int(data['appProperties']['backup_number']) + 1
            print('This is backup number %s' % self.backup_number)
        else:
            print('WARNING : No backup number found in folder metadata')

    def save_backup_number(self):
        properties= {
            'appProperties': {
                'backup_number': self.backup_number
            }
        }
        data = self.drive_service.files().update(body=properties, fileId=self.destination_folder_id, fields="id, appProperties").execute()
        print('New backup number saved (%s)' % self.backup_number)
        
    def create_backup_folder(self,backup_number):
        backup_folder_name = '{0} - {1}'.format(self.backup_number, self.now.isoformat())
        print('Create backup folder')

        file_metadata = {
            'name': backup_folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.destination_folder_id],
            'appProperties': {
                'backup_number': self.backup_number
            }
        }

        backup_folder = self.drive_service.files().create(body=file_metadata,
                                            fields='id, appProperties').execute()
        self.backup_folder_id = backup_folder.get('id')
        
        if self.backup_folder_id == 0:
            raise BaseException('No backup folder')
        else:
            print('Backup folder found (id:%s)' % self.backup_folder_id)
        return 1

    def upload_file(self, file):
        print('Upload file : %s' % file)

        if not os.path.isfile(file):
            raise BaseException('Backup file not found')

        # Upload backup file
        file_metadata = {
            'name': '{0}.{1}'.format(self.now.isoformat(),file),
            'parents': [self.backup_folder_id]
        }
        media = MediaFileUpload(file)
        drive_file = self.drive_service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        print('File saved (id:%s)' % drive_file.get('id'))

    def slack_notification(self, file):
        payload = "{\"text\":\"Backup finished (%s)\"}" % file
        (resp, content) = Http().request(self.config['slack_url'],
                                "POST", body=payload,
                                headers={'content-type':'application/json'})

    def clean(self):
        # Search sub folders
        results = self.drive_service.files().list(q="'{0}' in parents and mimeType='application/vnd.google-apps.folder'".format(self.destination_folder_id),
                                            orderBy='createdTime asc',
                                            spaces='drive',
                                            pageSize=100,
                                            fields='nextPageToken, files(id, name, appProperties)'
                                            ).execute()
        items = results.get('files', [])

        # Search folder for existing folder
        keep = []
        oldest_number = self.backup_number - self.config['rotation']['last'] + 1
        if items:
            for item in items:
                # print(item['name'])
                if 'appProperties' in item and 'backup_number' in item['appProperties']:
                    old_backup_number = int(item['appProperties']['backup_number'])
                    if old_backup_number >= oldest_number:
                        print('Keep %s' % item['name'])
                        keep.append(item['id'])
                    for modulo in self.config['rotation']['modulo']:
                        if old_backup_number%modulo == 0 and (old_backup_number//modulo >= ((self.backup_number//modulo)-1)):
                            print('Keep %s' % item['name'])
                            keep.append(item['id'])
            for item in items:
                if 'appProperties' in item and 'backup_number' in item['appProperties']:
                    delete=True
                    for k in keep:
                        if item['id'] == k:
                            delete = False
                            break
                    if delete:
                        print('Delete %s' % item['name'])
                        data = self.drive_service.files().delete(fileId=item['id'], fields="id").execute()

    def backup(self, files_to_backup):
        print(self.config_path)
        print(self.credentials_path)
        self.check_main_folder()
        self.check_destination_folder()
        self.get_backup_number()
        self.create_backup_folder(self.backup_number)
        print('Start Backup')
        for file in files_to_backup:
            self.upload_file(file)
            gc.collect()
        self.slack_notification('{0} - {1}'.format(self.config['destination_folder_name'], self.backup_number))
        self.save_backup_number()
        self.clean()
        time.sleep(3)
        return 1

def main():
    script_path = os.path.realpath(sys.path[0])
    files_to_backup = []

    if len(sys.argv) == 1:
        raise BaseException('Missing Arguments')
    else:
        i=1
        while i < len(sys.argv):
            files_to_backup.append(sys.argv[i])
            i += 1

    backup_manager = BackupManager(script_path)
    backup_manager.read_config()
    backup_manager.connect_drive()
    backup_manager.backup(files_to_backup)

if __name__ == '__main__':
    main()
