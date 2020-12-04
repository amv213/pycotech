import sys
import time
import string
import logging
import argparse
import pandas as pd
from . import utils
from . import loggers
from typing import List, Union
from pathlib import Path


def gen_txt(rows: List[List[Union[str, float]]], outdir: Path) -> str:
    """Packs a list of channel-by-channel data-samples into a standard PicoLog
    PLW Player data dataframe format, where each row has temperature
    measurements across all PicoLogger acquisition channels. Results are
    saved in a .txt file.

    Args:
        rows:   list of records. Each record should be a list with the
                acquisition channel name and associated measurement value.
        outdir: output directory where to save results

    Returns:
        name of the output file
    """

    # Pack all samples into dataframe
    df = pd.DataFrame(rows, columns=['channel', 'temp'])
    df.reset_index(drop=True, inplace=True)
    df = utils.from_pico_stream(df)  # pack

    # Save to .txt with timestamp of creation
    file_name = outdir / f'PycoLog {int(time.time())}.txt'
    df.to_csv(file_name, sep='\t', index=False, encoding='cp437')

    return str(file_name)


def main():

    # Setup a basic logger
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s | %(message)s',
        datefmt='%D %H:%M:%S'
    )

    logger = logging.getLogger(__name__)
    logger.setLevel("INFO")

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-dir", help="output directory",
                        required=False, type=str, default=None)

    args = parser.parse_args()

    save_dir = Path(args.dir) if args.dir is not None else Path(
        __file__).parent / 'PycoLogs'

    logger.info("Welcome to the PycoTech PT104 Recorder! \U0001F680 \n")

    if not save_dir.is_dir():
        save_dir.mkdir(parents=True, exist_ok=True)

    # Sniff for devices
    serials = loggers.PT104().discover_devices()
    # Extract device serial numbers
    serials = serials.decode().split(',')
    serials = [serial.split(':')[1] for serial in serials]

    logger.info("Found the following devices: %s", serials)

    # Ask user if ok with detected devices
    choice = input("Continue? [Y/n]")
    if choice not in ['', 'Y', 'y']:
        logger.info("Script has been terminated.")
        sys.exit()

    # Ask user channel mappings
    labels = [string.ascii_uppercase[i] for i in range(len(serials))]
    choice = input("Assign custom labels? [Y/n]")
    if choice in ['', 'Y', 'y']:
        for i, serial in enumerate(serials):
            label = input(f"{serial}: ")
            labels[i] = label.upper()

    # Create mapping between devices and labels
    labels = dict(zip(serials, labels))

    # Assign an individual PT104 instance to each identifier.
    # If not you would have to call .connect() / .disconnect()
    # everytime you move to next device.
    devices = {name: loggers.PT104() for name in serials}

    rows = []
    batch_size = 99999
    try:

        # Connect to all devices

        for name, device in devices.items():

            device.connect(name)

            # Set all channels to correct settings
            for ch_number in range(1, 5):
                device.set_channel(loggers.channel_x(ch_number),
                                   loggers.DataTypes.PT100,
                                   loggers.Wires.WIRES_4)

        # Actual PT-104 Main Loop
        logger.info("Collecting data...")
        idx = 0
        while True:

            if idx > batch_size:

                # Save dataframe as .TXT
                logger.info("\tgenerating .TXT file...")
                log_name = gen_txt(rows, outdir=save_dir)
                logger.info("\t\tDONE [%s]", log_name)

                # Reset counters
                idx = 0
                rows = []

            # Get measurements from all channels on all devices
            for name, device in devices.items():

                for ch_number in range(1, 5):
                    value = device.get_value(loggers.channel_x(ch_number))
                    channel = labels.get(name) + ch_number

                    rows.append([channel, value])

            idx += 1

    except KeyboardInterrupt as e:
        logger.warning("Received Keyboard Interrupt!")

    finally:

        logger.info("Terminating program...")

        # Make sure to save latest results
        logger.info("\tgenerating .TXT file...")
        log_name = gen_txt(rows, outdir=save_dir)
        logger.info("\t\tDONE [%s]", log_name)

        # Disconnect devices
        logger.info("\tdisconnecting devices...")
        for name, device in devices.items():
            device.disconnect()
            logger.info("\t\t%s disconnected", name)
        logger.info("\tDONE\n")

        logger.info("ALL DONE! \U0001F44D")