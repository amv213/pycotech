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


def gen_txt(rows: List[List[Union[str, float]]], out_dir: Path) -> str:
    """Packs a list of channel-by-channel data-samples into a standard PicoLog
    PLW Player data dataframe format, where each row has temperature
    measurements across all PicoLogger acquisition channels. Results are
    saved in a .txt file.

    Args:
        rows:       list of records. Each record should be a list with the
                    acquisition channel name and associated measurement value.
        out_dir:    output directory where to save results

    Returns:
        name of the output file
    """

    # Pack all samples into data-stream
    df = utils.build_pico_stream(rows=rows)
    # Pack data-stream into dataframe
    df = utils.from_pico_stream(df=df)

    # Save to .txt with timestamp of creation
    file_name = out_dir / f'PycoLog {int(time.time())}.txt'
    utils.to_pico_txt(df, fn=file_name)

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

    # if found any device...
    if serials != ['']:
        serials = [serial.split(':')[1] for serial in serials]
        logger.info("Found the following devices: %s", serials)
    else:
        logger.info("Could not find any connected devices...")
        logger.info("END \U0001F440")
        sys.exit()

    # Ask user if ok with detected devices
    choice = input("Continue? [Y/n]")
    if choice not in ['', 'Y', 'y']:
        logger.info("Script has been terminated.")
        logger.info("END \U0001F6A7")
        sys.exit()

    # Ask user channel mappings
    labels = [string.ascii_uppercase[i] for i in range(len(serials))]
    choice = input("Assign custom labels? [Y/n]")
    if choice in ['', 'Y', 'y']:
        for i, serial in enumerate(serials):
            label = input(f"{serial}: ")
            labels[i] = label.upper()

    # build the mapping between devices and labels
    labels = dict(zip(serials, labels))

    # Assign an individual PT104 instance to each identifier.
    # If not you would have to call .connect() / .disconnect()
    # everytime you move to next device.
    devices = {name: loggers.PT104() for name in serials}

    rows = []
    batch_size = 28800  # entries per file, = 1 log a day (assuming 3s sampling period)
    try:

        # Connect to all devices
        logger.info("Connecting devices...")
        for name, device in devices.items():

            device.connect(name)
            logger.info("\t%s connected", name)

            # Set all channels to correct settings
            for ch_number in range(1, 5):
                device.set_channel(loggers.channel_x(ch_number),
                                   loggers.DataTypes.PT100,
                                   loggers.Wires.WIRES_4)
        logger.info("\tDONE\n")

        # Actual PT-104 Main Loop
        logger.info("Collecting data...")
        idx = 0
        while True:

            if idx >= batch_size:

                # Save dataframe as .TXT
                logger.info("\tgenerating .TXT file...")
                log_name = gen_txt(rows, out_dir=save_dir)
                logger.info("\t\tDONE [%s]", log_name)

                # Reset counters
                idx = 0
                rows = []

            # Get measurements from all channels on all devices
            for name, device in devices.items():

                for ch_number in range(1, 5):
                    value = device.get_value(loggers.channel_x(ch_number))
                    channel = labels.get(name) + str(ch_number)

                    rows.append([channel, value])

            idx += 1

    except KeyboardInterrupt:
        logger.warning("Received Keyboard Interrupt!")
    except Exception:
        logger.exception("Exception raised!")

    finally:

        logger.info("Terminating program...")

        # Disconnect devices first
        logger.info("\tdisconnecting devices...")
        for name, device in devices.items():
            device.disconnect()
            logger.info("\t\t%s disconnected", name)
        logger.info("\tDONE\n")

        # Make sure to save latest results
        logger.info("\tgenerating .TXT file...")
        log_name = gen_txt(rows, out_dir=save_dir)
        logger.info("\t\tDONE [%s]", log_name)

        logger.info("ALL DONE! \U0001F44D")


if __name__ == "__main__":

    main()
