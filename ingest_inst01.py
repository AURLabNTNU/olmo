import os
from datetime import datetime
from influxdb import InfluxDBClient

import config
import util_file
from ctd import CTD
# from adcp import ADCP
# from lisst_200 import Lisst_200


def main():

    print("Starting running ingest_inst01.py at "
          + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    logger = util_file.init_logger(config.main_logfile, name='ingest_inst01')
    logger.info("\n\n------ Starting sync/ingest.")

    logger.info("Fetching the influxdb clients.")
    admin_user_ntnu, admin_pwd_ntnu = util_file.get_user_pwd(os.path.join(config.secrets_dir, 'influx_admin_ntnu_credentials'))
    clients = [
#        InfluxDBClient(config.az_influx_pc, 8086, admin_user, admin_pwd, 'oceanlab'),
#        InfluxDBClient(config.sintef_influx_pc, 8086, admin_user, admin_pwd, 'test'),
        InfluxDBClient(config.ntnu_influx_pc, 8086, admin_user_ntnu, admin_pwd_ntnu, 'test'),

    ]

    ctd = CTD(influx_clients=clients)
    ctd.rsync_and_ingest()

    # lisst = Lisst_200(influx_clients=clients)
    # lisst.rsync_and_ingest()

    # adcp = ADCP()
    # adcp.rsync_and_ingest()


if __name__ == "__main__":
    main()
