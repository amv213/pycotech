import sys
import time
import yaml
import struct
import logging
import configparser
import pandas as pd
from pathlib import Path
from typing import Union, List, Dict

# Spawn module-level logger
logger = logging.getLogger(__name__)


def fetch_metadata(fn: Union[str, Path]) -> Dict[str, Dict[str, str]]:
    """Extracts metadata information from a .PLW file.

    Args:
        fn: path to the .PLW file to parse.

    Returns:
        metadata associated with data contained in the .PLW file,
        as a single string.
    """

    metadata_bytes = 37714  # (can check opening .PLW in hex editor)

    try:

        # Open as binary stream
        with open(fn, "rb") as f:

            # go to start of metadata (metadata is at the end of the file)
            f.seek(-metadata_bytes, 2)

            # Read in binary chunk and decode
            metadata = f.read().decode('cp437')

            # Metadata is structured as a .ini file.
            # Add temporary section header at the beginning to corrupted
            # sections
            config = configparser.ConfigParser(allow_no_value=True,
                                               strict=False)
            config.read_string('[temporary_section]\n' + metadata)
            config.remove_section('temporary_section')

            # Return metadata as dict
            metadata = config._sections

    except FileNotFoundError:
        logger.exception("Could not find .PLW file")
        sys.exit()

    return metadata


def save_metadata(fn: Union[str, Path]) -> None:
    """Extracts metadata information from a .PLW file and saves it as YAML.

    Args:
        fn: path to the .PLW file to parse.
    """

    metadata = fetch_metadata(fn=fn)

    fn_meta = Path(fn).with_suffix('.yml')
    with open(fn_meta, 'w', encoding='cp437') as f:
        yaml.dump(metadata, f)


def map_channels(fn: Union[str, Path]) -> Dict[str, List[str]]:
    """Parses metadata in the .PLW file to build mapping between acquisition
    devices and associated channels. Devices and channels are mapped in same
    order as acquisition.

    Args:
        fn: path to the .PLW file to parse.

    Returns:
        dictionary mapping the serial of each acquisition device to the
        labels of its associated channels.
    """

    # Extract metadata
    metadata = fetch_metadata(fn)

    # Number of acquisition channels
    num_channels = int(metadata['General']['noofparameters'])

    # Number of converters (devices)
    num_converters = int(metadata['General']['noofconverters'])

    # Usually 4 channels per device
    channels_per_converter = num_channels // num_converters

    # keys: for each device get its serial id
    # values: get the name of each channel (parameter) for each parameter
    # associated with each device (unit)
    mapping = {metadata[f'Converter {i + 1}']['serial']:
                   [metadata[f'Parameter {j}']['name'] for j in
                    [metadata[f'Unit {i + 1} Channel {k + 1}']['paramno'] for k
                     in range(channels_per_converter)]
                    ]
               for i in range(num_converters)}

    return mapping


def read_txt(fn: Union[str, Path]) -> pd.DataFrame:
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


def read_plw(fn: Union[str, Path]) -> pd.DataFrame:
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

        # Ordered mapping between acquisition devices and associated channels
        devices_dict = map_channels(fn=fn)

        # Names of channels
        channels = [ch for chs in devices_dict.values() for ch in chs]
        num_channels = len(channels)

        column_labels = ['Time'] + channels

        # Open as binary stream
        with open(fn, "rb") as f:

            header_length = 1684  # bytes (can check with hex editor)
            f.seek(header_length)  # skip header and go to start of data

            num_fields = 1 + num_channels
            row_size = num_fields * 4  # Each field is a 32 bit float

            rows = []
            idx = 0
            # read in byte arrays for each row and convert entries
            while idx <= 99999:  # usual max number of samples in a .PLW
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

    except FileNotFoundError:
        logger.exception("Could not find .PLW file")
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

    channels_order = df.columns.values

    # Melt the dataframe and rename columns
    df = df.unstack().reset_index()
    df.columns = ['channel', 'Time', 'temp']

    # attach a categorical ordered data type to channel values so that they
    # maintain the acquisition order when sorting
    t = pd.CategoricalDtype(categories=channels_order, ordered=True)
    df['channel'] = pd.Series(df['channel'], dtype=t)

    # Sort values by time and channel order
    df.sort_values(['Time', 'channel'], inplace=True)

    # Reset `Time` index to give each entry virtual time id
    df.set_index('Time', inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def from_pico_stream(df: pd.DataFrame) -> pd.DataFrame:
    """Packs a channel-by-channel data-stream into a PicoLog PLW Player data
    dataframe, where each row has temperature measurements across
    all PicoLogger acquisition channels.

    For an input data-stream of length num_samples x num_channels, the output
    dataframe will have shape (num_samples, num_channels).

    Args:
        df: PicoLog PLW Player data-stream, where each row has a
        temperature measurement from a single PicoLogger acquisition channel.

    Returns:
        Equivalent packed-dataframe, where each row has temperature
        measurements across all PicoLogger acquisition channels.

        index:      None (enumeration of entries)
        columns:    `<channel_name>`, ... x num_channels
    """

    # Reindex timestamps with one timestamp per block of channels
    channels = df['channel'].unique().astype(str)
    df.index = df.index // len(channels)

    # Pivot table
    df = df.pivot(columns='channel', values='temp')

    return df


def build_pico_stream(rows: List[List[Union[str, float]]]) -> pd.DataFrame:
    """Packs a list of channel-by-channel data-samples into a pico-stream
    dataframe format, where each row is a temperature measurement from a
    single PicoLogger acquisition channel.

    Args:
        rows:   list of records. Each record should be a list with the
                acquisition channel name and associated measurement value.

    Returns:
        input data packed into a pico-stream dataframe.

        index:      None (enumeration of entries)
        columns:    `channel`, `temp`
    """

    # Pack all samples into dataframe
    df = pd.DataFrame(rows, columns=['channel', 'temp'])
    df.reset_index(drop=True, inplace=True)

    return df


def to_pico_txt(df: pd.DataFrame, fn: Union[str, Path]) -> None:
    """Saves the input dataframe to .TXT - mimicking the data format used by
    PicoLog PLW Player.

    Args:
        df: dataframe to save.
        fn: path to output .TXT file.
    """

    # Round digits to 3 decimal places
    df = df.round(3)

    # Fill possible missing values. Use same token as PicoLog Recorder
    df.fillna(value='******', inplace=True)

    # Add a subheader with units
    df_header = pd.DataFrame(data=[['( \u00B0C )' for i in df.columns]],
                             index=['Seconds'],
                             columns=df.columns)  # empty row
    df = pd.concat([df_header, df])

    # Give name to index
    df.index.name = 'Time'
    
    # Save to .txt
    df.to_csv(fn, sep='\t')

