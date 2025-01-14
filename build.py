#!/usr/bin/python3

import logging
import re
import shutil

from datetime import datetime
from enum import Enum
from zipfile import ZipFile

from matrix_runner import main, matrix_axis, matrix_action, matrix_command


def timestamp(t: datetime = datetime.now()):
    return t.strftime("%Y%m%d%H%M%S")


@matrix_axis("target", "t", "The project target(s) to build")
class TargetAxis(Enum):
    CM7 = ('CM7', 'VHT_MPS2_Cortex-M7')
    IMXRT = ('IMXRT', 'IMXRT1050-EVKB_ESP8266')


@matrix_action
def build(config, results):
    """Build the config(s) with CMSIS-Build"""
    yield run_cbuild(config)
    if not results[0].success:
        return

    file = f"aws_mqtt-{config.target[0].lower()}-{timestamp()}.zip"
    logging.info(f"Archiving build output to {file}...")
    with ZipFile(file, "w") as archive:
        archive.write(f"Objects/image.axf")
        archive.write(f"Objects/image.axf.map")
        archive.write(f"Objects/AWS_MQTT_MutualAuth.{config.target[1]}.clog")


@matrix_action
def run(config, results):
    """Run the config(s) with fast model"""
    if config.target not in [TargetAxis.CM7]:
        raise NotImplementedError(f"Action 'run' is not implemented for target {config.target[1]}!")
        
    yield run_vht(config)
    if results[0].success:
        msgs = re.findall(r'Incoming Publish Message : Hello World!', results[0].output.getvalue())
        assert(msgs and len(msgs) == 15)
 

@matrix_command(needs_shell=False)
def run_cbuild(config):
    return ["bash", "-c", f"cbuild.sh AWS_MQTT_MutualAuth.{config.target[1]}.cprj"]


@matrix_command()
def run_vht(config):
    return ["VHT_MPS2_Cortex-M7", "--stat", "--simlimit", "850", "-f", "vht_config.txt", "Objects/image.axf"]


if __name__ == "__main__":
    main()
