import os
import logging
import re
import paramiko

import util_file
import config

logger = logging.getLogger('olmo.sensor')

# This line is only to test a commit push. Delete it. 
class Sensor:
    '''Base sensor class that non-loggernet sensors should inherit from.'''
    def __init__(self):
        self.data_dir = None
        self.recursive_file_search_l0 = False
        self.recursive_file_search_l1 = False
        self.recursive_file_search_l2 = False
        self.recursive_file_search_l3 = False
        self.file_search_l0 = None
        self.file_search_l1 = None
        self.file_search_l2 = None
        self.file_search_l3 = None
        self.drop_recent_files_l0 = 1
        self.drop_recent_files_l1 = 1
        self.drop_recent_files_l2 = 1
        self.drop_recent_files_l3 = 1
        self.remove_remote_files_l0 = False
        self.remove_remote_files_l1 = False
        self.remove_remote_files_l2 = False
        self.remove_remote_files_l3 = False
        self.max_files_l0 = None
        self.max_files_l1 = None
        self.max_files_l2 = None
        self.max_files_l3 = None
        self.measurement_name_l0 = None
        self.measurement_name_l1 = None
        self.measurement_name_l2 = None
        self.measurement_name_l3 = None

    def fetch_files_list(self, file_regex, recursive_file_search, drop_recent_files):
        '''Use regex to find all files up to self.drop_recent_files

        Will match all files from the remote data_dir using the file_regex
        pattern, and dropping the final (most recent) drop_recent_files files.

        Note that currently the most recent files are simpy those listed
        last in the ls_string

        Parameters
        ----------
        file_regex : str
        recursive_file_search : bool
            If the file_regex is to be interpreted as the input to a linux 'find' query, not regex
        drop_recent_files : int
            Number of latest files to ignore.

        Returns
        -------
        list
        '''
        drop_recent_files=1
        print(drop_recent_files)
        numberOfMatches=0
        print(f"regex file search word:  {file_regex}")
        print(f"recursive_file_search:  {recursive_file_search}")
        if (self.data_dir is None) or (file_regex is None):
            raise ValueError("fetch_files_list() requires 'data_dir' and 'file_regex' are set.")

        # TODO: Need to handle the ls_err (below in both statements) in some way.
        if recursive_file_search:
            ls_out, ls_err = util_file.find_remote(
                config.inst01_user, config.inst01_pwd, config.inst01_pc,   ## NTNU added password. todo adopt to sintef
                self.data_dir, file_regex, port=config.inst01_ssh_port) ## todo adopt to sintef
#                config.munkholmen_user, config.munkholmen_pc,
#                self.data_dir, file_regex, port=config.munkholmen_ssh_port)
            # Using find_remote() it should already filter. Thus just split up string:
            files = ls_out.split('\n')
            if files[-1] == '':
                files = files[:-1]
            # Remove the 'self.data_dir' from the file path, so consistet with below
            for i, f in enumerate(files):
                files[i] = f[len(self.data_dir) + 1:]
            files.sort()
        else:
            ls_out, ls_err = util_file.ls_remote(
                config.inst01_user, config.inst01_pwd, config.inst01_pc,
                self.data_dir_rsync_source, port=config.inst01_ssh_port)   ## NTNU added pwd. todo: make compatible for ntnu/sintef
            print('looking for files in: ', self.data_dir_rsync_source, 'with user name: ', config.inst01_user)
#                config.munkholmen_user, config.munkholmen_pc,
#                self.data_dir, port=config.munkholmen_ssh_port)
            files = []
            while True:
#                print('ls_out ', ls_out)
#                print('file_regex ', file_regex)
#                print('type ls_out: ', type(ls_out))
#                print('type file_regex: ', type(file_regex))
#                print('searching for file match ')
                match = re.search(file_regex, ls_out)
#                print('match is: ', match)
                if match is None:
                    print('match is none ')
                    break
                else:
                    recursive_file_search += 1
                    files.append(match.group())
                    ls_out = ls_out[match.span()[1]:]
                    print(f'Appending nr {recursive_file_search}')

        if len(files) <= drop_recent_files:
            logger.info(f"No new files found matching regex pattern: {file_regex}")
            print(f"No new files found matching regex pattern: {file_regex}")
            return None
        elif drop_recent_files == 0:
            return files
        else:
            return files[:-drop_recent_files]

    def rsync(self):
        '''rsync's files from munkholmen to the controller PC.

        Parameters
        ----------
        self.remove_remote_files : bool
            If rsynced files are deleted using '--remove-source-files' flag
        self.max_files : int
            If not None: maximum number of files to transfer
        ## should tripple quotes end here? YES
        '''

        def rsync_file_level(files, remove_remote_files, max_files): 

            if files is None:
                return

            if max_files is not None:
                if max_files >= len(files):
                    logger.warning(f"max_files {max_files} >= len(files), rsyncing all appropriate files")
                else:
                    files = files[:max_files]

            if remove_remote_files:
                remove_flag = ' --remove-source-files'
            else:
                remove_flag = ''

            rsynced_files = []
            print("rsynced_files in def sync def rsync file level: ", rsynced_files)   # delete
            for f in files:
                print("todo: change for ntnu might needs to be done here")
#                rsync_path = f"{config.munkholmen_user}@{config.munkholmen_pc}:{os.path.join(self.data_dir, f)}"
#                exit_code = os.system(f'rsync -a{remove_flag} --rsh="ssh -p {config.munkholmen_ssh_port}" {rsync_path} {config.rsync_inbox_adcp}')
                print('self.data_dir is: ', self.data_dir_rsync_source)
                print('file to rsync is: ', f)
                self.data_dir_rsync_source = self.data_dir_rsync_source.replace("\\", "/")    #convert slash from win to linux (still for use in windows)
                print('self.data_dir_rsync_source is: ', self.data_dir_rsync_source)
#                rsync_path = f"{config.inst01_user}@{config.inst01_pc}:{os.path.join(self.data_dir, f)}"   # adopting to NTNU
#aurlab@10.53.59.94:C:/Users/aurlab/Documents/DeleteInstRig/test/rig01Trd-NTNU-20230423-114345.txt
#                rsync_path = "aurlab-local@10.53.59.94:'C:/Documents/DeleteInstRig/test/rig01Trd-NTNU-20230423-114345.txt'"
#                print("rsync_path with windows should look like this: aurlab-local@xx.xx.xx.94:'Documents/DeleteInstRig/test/rig01Trd-NTNU-20230423-114345.txt'")
                rsync_path = f"{config.inst01_user}@{config.inst01_pc}:{os.path.join(self.data_dir_rsync_source, f)}"   ## adopting to NTNU
#                print('rsync_path is: ', rsync_path) ## delete
                logger.info(f'remove_flag is ', {remove_flag} )
                logger.info(f'If files are fetched from windows computer, rsync can be installed on WSL on Windows.')
                logger.info(f'config.rsync_inbox_adcp is:  {config.rsync_inbox_adcp}')
                logger.info(f'config.inst01_ssh_port is: {config.inst01_ssh_port}') # not used with windows
#               consider that WSL and windows might (and probably should) use unequal ssh port.
#               we are using windows ssh port and use WSL and linux commands through that.
#                command = f'rsync -avhP -e ssh {rsync_path} {config.rsync_inbox_adcp} --rsync-path="wsl rsync"'  # NTNU testing wsl on windows, wsl crashed.
#                command = f'rsync -a{remove_flag} --rsh="ssh -p {config.munkholmen_ssh_port}" {rsync_path} {config.rsync_inbox_adcp}')   # SINTEF version
                command = f' sshpass -p {config.inst01_pwd} scp {config.inst01_user}@{config.inst01_pc}:{os.path.join(self.data_dir_rsync_source, f)} {config.rsync_inbox_adcp}'  # NTNU/ windows.
# delete                command = f' sshpass -p psw scp aurlab@10.53.59.94:Documents/delete1/Notes.txt /home/deletersync/'   # NTNU / WINDOWS
                print('running this command: ',  command)
#                exit_code = os.system(f'rsync -a{remove_flag} --rsh="ssh -p {config.inst01_ssh_port}" {rsync_path} {config.rsync_inbox_adcp})
                exit_code = os.system(command)   #adpoting to ntnu
                if exit_code != 0:
                    logger.error(f"Rsync or scp for file {f} didn't work, output sent to stdout, (probably the log from the cronjob).")
                    return rsynced_files
                else:
                    logger.info(f"rsync'ed or copied file: {os.path.join(config.rsync_inbox_adcp, os.path.basename(f))}")
                    rsynced_files.append(os.path.join(config.rsync_inbox_adcp, os.path.basename(f)))
###             Delete file after scp
###             ALSO, DONT SCP NEWEST FILE !!!!!!!!!!
                ssh = paramiko.SSHClient()   #ntnu win
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  #ntnu win
                ssh.connect(config.inst01_pc, username=config.inst01_user, password=config.inst01_pwd, port=22) ## TODO NTNU password temporarily a> TODO move port variable 22.
# backing up locally on remote topside pc
                commandBack1 = f'copy /Y ' # ntnu win
                commandBack2 = f'{os.path.join(self.data_dir_rsync_source, f)} {self.data_dir_rsync_back}'  # ntnu win
                commandBack2 = commandBack2.replace("/", "\\")     #convert slash from win to linux (for use>
                commandBack = commandBack1 + commandBack2 
                print('running this command: ', commandBack)  # ntnu win
                logger.info('running this command: ', commandBack) # ntnu win
                stdin, stdout, stderr = ssh.exec_command(commandBack)
                # add output to logger ?
                # if there is a way to check that copying went well, is great. also ctd logger copies so the 2 backups will overwrite each other.
# delete file
#                directory example: ="C:\\Users\\aurlab\\Documents\\DeleteInstRig\\test\\"  # for windows NB: this vairable also might exist in ctd.py or util_file 
                commandDel = f'del {os.path.join(self.data_dir_rsync_source, f)}'  # ntnu win
                commandDel = commandDel.replace("/", "\\")     #convert slash from win to linux (for use in windows)
                print('running this command: ', commandDel)  # ntnu win
                logger.info('running this command: ', commandDel) # ntnu win
#                command=f'del {directory}{f}' # for windows
                stdin, stdout, stderr = ssh.exec_command(commandDel)
            return rsynced_files

        def fetch_and_sync(file_regex, recursive_file_search, drop_recent_files, remove_remote_files, max_files):
            files = self.fetch_files_list(file_regex, recursive_file_search, drop_recent_files)
            files = rsync_file_level(files, remove_remote_files, max_files)
            return files

        rsynced_files = {'l0': None, 'l1': None, 'l2': None, 'l3': None}
        if isinstance(self.file_search_l0, str):
            rsynced_files['l0'] = fetch_and_sync(
                self.file_search_l0, self.recursive_file_search_l0, self.drop_recent_files_l0,
                self.remove_remote_files_l0, self.max_files_l0)
        if isinstance(self.file_search_l1, str):
            rsynced_files['l1'] = fetch_and_sync(
                self.file_search_l1, self.recursive_file_search_l1, self.drop_recent_files_l1,
                self.remove_remote_files_l1, self.max_files_l1)
        if isinstance(self.file_search_l2, str):
            rsynced_files['l2'] = fetch_and_sync(
                self.file_search_l2, self.recursive_file_search_l2, self.drop_recent_files_l2,
                self.remove_remote_files_l2, self.max_files_l2)
        if isinstance(self.file_search_l3, str):
            rsynced_files['l3'] = fetch_and_sync(
                self.file_search_l3, self.recursive_file_search_l3, self.drop_recent_files_l3,
                self.remove_remote_files_l3, self.max_files_l3)
        return rsynced_files

    def get_influx_user(self, file=os.path.join(config.secrets_dir, 'influx_admin_credentials')):
        admin_user, _ = util_file.get_user_pwd(file)
        return admin_user

    def get_influx_pwd(self, file=os.path.join(config.secrets_dir, 'influx_admin_credentials')):
        _, admin_pwd = util_file.get_user_pwd(file)
        return admin_pwd

    def get_azure_token(self, file=os.path.join(config.secrets_dir, 'azure_token_datalake')):
        with open(file, 'r') as f:
            az_token = f.read()  # This token to run out end of 2021
        return az_token

    def ingest(self):
        raise NotImplementedError("This method should be implemented in sensor subclass.")

    def rsync_and_ingest(self):
        raise NotImplementedError("This method should be implemented in sensor subclass.")
