import os
import json

# General:
print("hello test 888")
if (base_dir := os.getenv("OLMO_BASE_DIRECTORY")) is None:
    print("Warning. Env var OLMO_BASE_DIRECTORY not set correctly.")

output_dir = os.path.join(base_dir, 'Output')
secrets_dir = os.path.join(base_dir, 'Secrets')

with open(os.path.join(secrets_dir, 'config_secrets.json')) as f:
    data = json.load(f)
loggernet_pc = data['loggernet_pc']
loggernet_user = data['loggernet_user']
munkholmen_pc = data['munkholmen_pc']
munkholmen_ssh_port = int(data['munkholmen_ssh_port'])
munkholmen_user = data['munkholmen_user']
sintef_influx_pc = data['sintef_influx_pc']
az_influx_pc = data['az_influx_pc']
inst01_pc = data['inst01_pc']
inst01_ssh_port = int(data['inst01_ssh_port'])
inst01_user = data['inst01_user']
inst01_pwd = data['inst01_pwd']
NTNU_influx_pc = data['NTNU_influx_pc']

# Sync munkholmen (main):
# rsync_inbox = os.path.join(base_dir, 'Rsync_inbox')
# rsync_inbox_adcp = os.path.join(base_dir, 'Rsync_inbox_adcp')
# main_logfile = "log_munkholmen_ingest_"
# gas_logfile = "log_gasanalyser_ingest_"

# Sync Instrument rig 01 topside pc (main):
rsync_inbox = os.path.join(base_dir, 'Rsync_inbox')
# rsync_inbox_adcp = os.path.join(base_dir, 'Rsync_inbox_adcp')
main_logfile = "log_inst01_ingest_"
############## add main_logfile = "log_instrumentRigTrd01_ingest"

# Sync loggernet: NOT IN USE AT THE MOMENT AT NTNU DB
# loggernet_outbox = f"c:\\Users\{loggernet_user}\LoggerNet_output"
# loggernet_inbox = os.path.join(base_dir, 'Loggernet_inbox')
# loggernet_files_basenames = [
#     "CR6_EOL2p0_meteo_ais_",
#     "CR6_EOL2p0_Power_",  # instr.: solar_regulator
#     "CR6_EOL2p0_Meteo_avgd_",
#     "CR6_EOL2p0_Current_",  # intr.: signature_100
#     "CR6_EOL2p0_Wave_sensor_",  # instr.: seaview
#     # "CR6_EOL2p0_Winch_log_",  # none
#     "IngdalenCR6_victron_",
#     "IngdalenCR6_SUNA_",
#     "IngdalenCR6_System_",
#     "IngdalenCR6_signatureRecord_",
#     "IngdalenCR6_signatureCurrentProf_",
#     "IngdalenCR6_Seabird_",
#     "IngdalenCR6_Power_",
#     "IngdalenCR6_PAR_",
#     "IngdalenCR6_MetData_",
#     "IngdalenCR6_Hydrocat_",
#     "IngdalenCR6_GPSData_",
#     "IngdalenCR6_Debug_",
#     "IngdalenCR6_CFluor_",
#     "IngdalenCR6_Wave_",
# ]
loggernet_logfile = "log_loggernet_ingest_"
logpc_ssh_max_attempts = 3


# Backup files:
backup_dir = os.path.join(base_dir, 'backups')
bu_logfile_basename = "log_influx_backup_"
backup_basename = 'influxbackup_'
az_backups_folder = 'influx_backups'

# Website figures
webfigs_dir = os.path.join(output_dir, 'Website_figures')

# Node 2 ingestion: NOT IN USE AT THE MOMENT AT NTNU DB
# with open(os.path.join(secrets_dir, 'node2_password'), 'r') as f:
#     node2_pwd = f.read()[:-1]
# with open(os.path.join(secrets_dir, 'node2_secrets.json'), 'r') as f:
#     data = json.load(f)
# node2_dbname = data['dbname']
# node2_user = data['user']
# node2_host = data['host']
# node2_port = data['port']
# node2_sslmode = data['sslmode']
# node2_logfile = "log_node2_ingest_"

# Silcam ingestion:

###################### NTNU: make instruementrigTrd01 ingestion here (copy and change from above)  node1, see down.
#### add node1 to secrets json file
with open(os.path.join(secrets_dir, 'influx_node1_credentials'), 'r') as f:
    node1_pwd = f.read()[:-1]
with open(os.path.join(secrets_dir, 'node1_secrets.json'), 'r') as f:
    data = json.load(f)
node1_dbname = data['dbname']
node1_user = data['user']
node1_host = data['host']
node1_port = data['port']
node1_sslmode = data['sslmode']
node1_logfile = "log_node1_ingest_"


# Custom data ingestion:
custom_data_folder = "Custom_Data"
