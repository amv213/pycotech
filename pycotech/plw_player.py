import sys
import logging
import argparse
from . import utils
from pathlib import Path


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
    parser.add_argument("-plw", help="input .PLW file",
                        required=True, type=str)
    parser.add_argument("-txt", help="output .TXT file",
                        required=False, type=str, default=None)

    args = parser.parse_args()

    plw_file = Path(args.plw)
    txt_file = Path(args.txt) if args.txt is not None else \
        plw_file.with_suffix('.txt')

    logger.info("Welcome to the PycoTech PLW Converter! \U0001F680 \n")

    # Check files are of the right format
    if plw_file.suffix.upper() != '.PLW':
        logger.warning("Input filename must be `.PLW`")
        sys.exit()
    elif txt_file.suffix.upper() != '.TXT':
        logger.warning("Output filename must be `.TXT`")
        sys.exit()
    # Check directories exist
    elif not plw_file.is_file():
        logger.warning("Invalid path to .PLW file: `%s`", plw_file)
        sys.exit()
    elif not txt_file.parent.is_dir():
        logger.warning("Invalid path to output .TXT file dir: `%s`",
                       txt_file.parent)
        sys.exit()

    logger.info("Input: \t %s", plw_file)
    logger.info("Output:\t %s\n", txt_file)

    logger.info("Converting .PLW file...")

    # Create dataframe from .PLW
    logger.info("\tparsing .PLW file...")
    df = utils.read_plw(fn=plw_file)

    # Save dataframe as .TXT
    logger.info("\tgenerating .TXT file...")
    df.to_csv(txt_file, sep='\t', index=False, encoding='cp437')
    logger.info("\tDONE\n")

    logger.info("ALL DONE! \U0001F44D")
