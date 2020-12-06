# 📑 Welcome to Pycotech!

Pycotech offers tools and wrappers to interface with PT-104 PicoLog® Data
 Loggers and files, allowing you to easily build an end-to-end data processing
  pipeline in pure python.
  
This work would not have been possible without *Martin Schröder*'s
 amazing wrapper around the usbpt104 c library for the Pico PT-104A RTD Data 
 Acquisition Module. Don't hesitate to head over to his 
 [PT_104 Github repo](https://github.com/trombastic/Pico_PT104) to check out
  the original project and to drop a star! 🌟

## 🔥 Features

Pycotech's suite of utility functions provides seamless integration of
 `.PLW` and `.TXT` files generated by traditional PicoTechnology® 
 software - allowing you to handle, visualise, and convert between 
 data-formats at will. 
  
Pycotech also provides python command line alternatives to most of the 
 principal PicoLog® software components. Namely, pycotech's 
 `plw-recorder` allows you to bypass the PLW Recorder® data acquisition
  software and gather data directly from a number of PT-104 Data 
  Loggers. Pycotech's `plw-player` substitutes instead the PicoLog® Player
   software, allowing you to read, convert, and extract data from existing
    `.PLW` files.

## 🚀 Quick Start

1. 📚 Install pycotech like any other python package, using pip to download it
 from PyPI:

    ```cmd
        $ pip install pycotech
    ```

2. 🐍 Test your installation running the following minimal script:
    
    ```python
         import pycotech
    
         df = pycotech.utils.read_plw("my_plw_file.PLW")
   
         print(df)
    ```
  
## 📟 CLI Tools

To use pycotech's command line tools, install pycotech as described above
 and then run any of the following:

1. `plw-player`: converts `.PLW` files to `.TXT`
 
    ```cmd
    $ plw-player -plw "my_plw_file"
    ```
    
    ```txt
    usage: plw-player [-h] -plw PLW [-txt TXT]
    
    optional arguments:
      -h, --help  show this help message and exit
      -plw PLW    input .PLW file
      -txt TXT    output .TXT file
    ```

2. `plw-recorder`: continuous data acquisition from connected PT-104 Loggers:

    ```cmd
    $ plw-recorder
    ```
    
    ```txt
    usage: plw-recorder [-h] [-dir DIR]
    
    optional arguments:
      -h, --help  show this help message and exit
      -dir DIR    output directory
    ```

## 📚 Documentation

To learn more about the package head over to the [official documentation
](https://amv213.gitlab.io/pycotech/)!