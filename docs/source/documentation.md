# 📚 Documentation

## 📔 Source pycotech Documentation

```{toctree}
   :maxdepth: 4

   Modules <modules.rst>
```

## 📃 Logging
pycotech implements logging for many of its functions via the Python standard
 library `logging` package. The loggers which have been implemented are
  named as follows:
  
  - `pycotech`
  - `pycotech.loggers`
  - `pycotech.utils`

If your using application does not use logging, then only events of severity
 `WARNING` and greater will be printed to `sys.stderr`, thanks to the
  logger's last resort handler. This is regarded as the best default behaviour.

````{note}
It is generally recommended to use logging in your applications, instead of 
abusing the `print()` command. The following code snippet will set you up 
with a nicely formatted logger:

```python
import logging

# Setup your basic logger
logging.basicConfig(
   format='[%(asctime)s] %(levelname)s | %(message)s',
   datefmt='%D %H:%M:%S'
)

# Spawn logger for current module 
logger = logging.getLogger(__name__)  
logger.setLevel("INFO")  # set default logging level

logger.info("Amazing!")
```

````