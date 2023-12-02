import os
import re
import logging
import datetime
import paramiko
import time ## to sleep to avoid SSH error

import config

logger = logging.getLogger('olmo.util_file')


def change_dir(filepath, new_dir):
    '''
    Changes a file path to have same file name, but be in new dir

    Parameters
    ----------
    filepath : str

    Returns
    -------
    str
    '''
    filename = os.path.split(filepath)[-1]
    return os.path.join(new_dir, filename)


def add_timestring(filepath, timestring):
    '''
    Appends a time_stamp to a filename (before the extension).

    Parameters
    ----------
    filepath : str

    Returns
    -------
    str
    '''
    if '.' in filepath:
        name, ext = filepath.rsplit('.', 1)
        return name + '_' + timestring + '.' + ext
    else:
        return filepath + '_' + timestring


def remove_timestring(filepath):
    '''
    Removes a timestring from the end of a filename.
    This function is the assumed pair of the 'util_file.add_timestring()'.

    Parameters
    ----------
    filepath : str

    Returns
    -------
    str
    '''

    if '.' in filepath:
        name, ext = filepath.rsplit('.', 1)
        base_name, timestring = name.rsplit('_', 1)
        error_msg = f"Completion flag date, {timestring}, conatains non ints."
        assert not re.findall("[^0-9]", timestring, re.MULTILINE), error_msg
        return base_name + '.' + ext
    else:
        base_name, timestring = filepath.rsplit('_', 1)
        error_msg = f"Completion flag date, {timestring}, conatains non ints."
        assert not re.findall("[^0-9]", timestring, re.MULTILINE), error_msg
        return base_name


def ls_remote(user, pwd, machine, directory, port=22):     # pwd added for NTNU, but fix to make ntnu/sintef compatible.
    '''
    Perform 'ls' over ssh onto linux machine.

    Parameters
    ----------
    user : str
    machine : str
        IP address of the maching you will connect to.
    directory : str
    port : int, default 22

    Returns
    -------
    str
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(machine, user, port, "if stopping here, maybe wrong ip, user, password")
    ssh.connect(machine, username=user, password=pwd, port=port)  # todo password added for NTNU but must be fixed to be used with both ntnu and sintef.
##    ssh.connect(machine, username=user, port=port)
    print("hello3429")
##    command = f"ls {directory}"  
##    command = f"dir {directory}"  # delete
    search="rig*" ##todo this variable should be moved to json file. it should also include the word CTD.
    directory2="C:\\Users\\aurlab\\Documents\\DeleteInstRig\\" #delete
    command=f'dir /b /a-d {directory}{search}'  ## Todo, this was adopted to NTNU win machine.
    print("retreaving files from ", directory)
    stdin, stdout, stderr = ssh.exec_command(command) 
    # stdin, stdout, stderr = ssh.exec_command(command)  delete  
    stdout = stdout.read().decode(errors='ignore'), stderr.read().decode(errors='ignore')
    print('stdout', type(stdout)) # delete
    print('stdin', type(stdin))   # delete
    print('stderr', type(stderr)) # delete
    print('length of stdout ',len(stdout))    # delete

    stdout0 = stdout[0]    # added for ntnu windows. not sure if it works on linux
    stdout1 = stdout[1]      # added for ntnu windows. not sure if it works on linux
    stdoutSplit = stdout0.splitlines()      # added for ntnu windows. not sure if it works on linux
    stdout0 = "\n".join(stdoutSplit)     # added
    stdout = (stdout0, stdout1)      # added for ntnu windows. not sure if it works on linux
# print('printing stdout[2]', stdout[2])  # delete
    print('hello29')   #delete prints
    print(type(stdout))
    print("printing ls_remote output", stdout)
    print('hello30')
    return stdout

def find_remote(user, pwd, machine, directory, search, port=22):
    '''
    Perform 'find {directory} -name '{search}'"' over ssh onto linux machine.
    Note this returns the full file path, not relative to 'directory'.

    Parameters
    ----------
    user : str
    machine : str
        IP address of the maching you will connect to.
    directory : str
    search : str
    port : int, default 22

    Returns
    -------
    str
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    ssh.connect(machine, username=user, port=port)
    ssh.connect(machine, username=user, password=pwd, port=port) ## TODO NTNU password temporarily added
    print("ssh connect find_remote finished")    
# TODO check automoatically if ssh host is linux or windows.
#    command = f"find {directory} -name '{search}'"   # For linux
    search="rig*"
    directory="C:\\Users\\aurlab\\Documents\\DeleteInstRig\\test\\"  # for windows
    command=f'dir /b /a-d {directory}{search}' # for windows
    stdin, stdout, stderr = ssh.exec_command(command)
    time.sleep(1)
    stdout = stdout.read().decode(errors='ignore'), stderr.read().decode(errors='ignore')
    print(stdout)
    return stdout


def get_user_pwd(file):
    '''
    Get user and pwd from a "credentials file".

    File is expect to be formatted like this:
    USER=good_username
    PWD=12345password

    Parameters
    ----------
    file : str
        Full path to credential file.

    Returns
    -------
    str, str
    '''
    with open(file, 'r') as f:
        user_line = f.readline().rstrip('\n')
        pwd_line = f.readline().rstrip('\n')
    assert user_line[:5] == 'USER=', f"Credentials file {file} not correct format."
    assert pwd_line[:4] == 'PWD=', f"Credentials file {file} not correct format."
    user = user_line[5:]
    pwd = pwd_line[4:]
    return user, pwd


def init_logger(logfile, name='olmo'):
    '''
    Define the logger object for logging.

    Parameters
    ----------
    logfile : str
        Full path of the output log file.
    name : str
        Name of the logger, used by the logging library.

    Returns
    -------
        logger."logging-object"
    '''

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(os.path.join(
        config.output_dir, logfile + datetime.datetime.now().strftime('%Y%m%d')), 'a+')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    return logger
