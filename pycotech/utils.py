import re
import struct
import logging
import pandas as pd
from pathlib import Path
from typing import Union, Dict

# Spawn module-level logger
logger = logging.getLogger(__name__)


def read_pico_txt(fn: Union[str, Path]) -> pd.DataFrame:
    """Saves contents of a PicoLog PLW Player .TXT file into a properly
    formatted dataframe.

    Args:
        fn: path to the .TXT file to parse.

    Returns:
        dataframe where each row has temperature measurements (°C) across
        PicoLogger acquisition channels.

        index:      None (enumeration of entries)
        columns:    `<channel_name>`, ... x num_channels
    """

    # use cp437 decoding or similar to make it work nicely
    df = pd.read_csv(fn, delimiter='\t', encoding='cp437', dtype='unicode',
                     header=0)

    df.drop(df.index[0], inplace=True)  # drop first row (with units)
    df.set_index('Time', inplace=True)  # set index on the `Time` column

    # Some PicoLog entries are assigned duplicate `Time` ids - so reset to
    # unique values:
    df.reset_index(drop=True, inplace=True)

    # Convert entries to numeric, coercing PicoLog '******' values to np.NaNs
    df = df.apply(pd.to_numeric, errors='coerce')

    return df


def read_pico_plw(fn: Union[str, Path]) -> pd.DataFrame:
    """Saves contents of a PicoLog PLW Player .PLW file into a properly
    formatted dataframe.

    Args:
        fn: path to the .PLW file to parse.

    Returns:
        dataframe where each row has temperature measurements (°C) across
        PicoLogger acquisition channels.

        index:      None (enumeration of entries)
        columns:    `<channel_name>`, ... x num_channels
    """

    # Try opening file
    try:

        # Open as binary stream
        with open(fn, "rb") as f:

            # bytes (can check with hex editor and open PLW file)
            metadata_length = 37714

            f.seek(-metadata_length, 2)  # go to start of metadata
            metadata = f.read().decode('cp437')

            # Now can use regex to extract any wanted metadata:

            # Number of acquisition channels
            num_channels = re.findall(r'NoOfParameters=([0-9]+)', metadata)
            num_channels = int(num_channels[0])

            # Name of acquisition channels
            channels = re.findall(r'Name=(\w+)', metadata)
            # `Names` are not unique in metadata, so only take from end
            channels = channels[-num_channels:]

            column_labels = ['Time'] + channels

            # ----

            header_length = 1684  # bytes (can check with hex editor)
            f.seek(header_length)  # skip header and go to start of data

            num_fields = 1 + num_channels
            num_bytes_float = 4  # 32 bit float
            row_size = num_fields * num_bytes_float

            rows = []
            idx = 0
            # read in byte arrays for each row and convert entries
            while idx <= 99999:
                byte_array = f.read(row_size)

                # convert first 4 bytes to int (little endian format)
                idx = struct.unpack('<i', byte_array[:4])[0]

                # convert rest of byte_array (column values) to float32 (little
                # endian format)
                # Convert 4-byte hex to IEEE-754 floating point
                # https://www.h-schmidt.net/FloatConverter/IEEE754.html
                vals = struct.unpack(f'<{num_channels}f', byte_array[4:])

                results = [idx] + list(vals)

                rows.append(results)

        # The algorithm will glob one more line (especially if PLW not filled
        # to max capacity) [extra line is from metadata section]
        del rows[-1]

        # ------

        # Build dataframe:
        df = pd.DataFrame(rows, columns=column_labels)
        df = df.set_index('Time').reset_index(drop=True)

    except FileNotFoundError as e:
        logger.warning(f"Could not find .PLW file: {e}")
        df = pd.DataFrame()

    return df


def to_pico_stream(df: pd.DataFrame) -> pd.DataFrame:
    """Flattens a PicoLog PLW Player data dataframe to a virtual
    data-stream - simulating sequential acquisition of data channel-by-channel.

    For an input dataframe of shape (num_samples, num_channels), the output
    data-stream will have length num_samples x num_channels.

    Args:
        df: PicoLog PLW Player dataframe, where each row has temperature
            measurements across PicoLogger acquisition channels.

    Returns:
        Equivalent flattened data-stream dataframe, where each row has a
        temperature measurement from a single PicoLogger acquisition channel.

        index:      None (enumeration of entries)
        columns:    `channel`, `temp`
    """

    # Melt the dataframe
    df = df.unstack().reset_index()

    # Rename columns and sort them chronologically by original time id
    df.columns = ['channel', 'Time', 'temp']
    df.sort_values(['Time', 'channel'], inplace=True)

    # Reset `Time` index to give each entry virtual time id
    df.set_index('Time', inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def map_channels(fn: Union[str, Path]) -> Dict[str, str]:
    """Parses metadata in the .PLW file to build mapping between channel
    labels and name of corresponding acquisition device.

    Args:
        fn: path to the .PLW file to parse.

    Returns:
        dictionary mapping acquisition channel label stumps (X*) to the id of
        the device they are associated to.
    """

    # Try opening file
    try:

        # Open as binary stream
        with open(fn, "rb") as f:

            # bytes (can check with hex editor and open PLW file)
            metadata_length = 37714

            f.seek(-metadata_length, 2)  # go to start of metadata
            metadata = f.read().decode('cp437')

            # Now can use regex to extract any wanted metadata:

            # Number of acquisition channels
            num_channels = re.findall(r'NoOfParameters=([0-9]+)', metadata)
            num_channels = int(num_channels[0])

            # Name of acquisition channels
            channels = re.findall(r'Name=(\w+)', metadata)
            # `Names` are not unique in metadata, so only take from end
            channels = channels[-num_channels:]

            # Label of acquisition devices
            devices = re.findall(r'Serial=([\w/]+)', metadata)

            stumps = pd.unique([x[0] + '*' for x in channels])
            chs_to_serial = {
                key: value for (key, value) in zip(stumps, devices)}

    except FileNotFoundError as e:
        logger.warning(f"Could not find .PLW file: {e}")
        chs_to_serial = {}

    return chs_to_serial
