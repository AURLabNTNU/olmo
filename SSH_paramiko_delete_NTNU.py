import paramiko
import config
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh.connect(machine, username=user, port=port)
# ssh.connect("10.53.59.94", username= "aurlab", port=22)
# error: paramiko.ssh_exception.SSHException: No authentication methods available
ssh.connect("10.53.59.94", username= "aurlab", password="AURlab2010!", port=22)
search="rig*"
directory="C:\\Users\\aurlab\\Documents\\DeleteInstRig\\"
command=f'dir /b /a-d {directory}{search}'
# command = f"find {directory} -name '{search}'"
# rig01Trd-NTNU-20230423-114150.txt
stdin, stdout, stderr = ssh.exec_command(command)
stdout = stdout.read().decode(errors='ignore'), stderr.read().decode(errors='ignore')
stdout

# stdout
# ('', 'FIND: Parameter format not correct\r\n')
# stdout
# ('', "File not found - 'rig*'\r\n")
# dir /s C:\Users\aurlab\Documents\DeleteInstRig\rig*
