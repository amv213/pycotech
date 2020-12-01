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

If your using application does not use logging, then only events of severity
 `WARNING` and greater will be printed to `sys.stderr`, thanks to the
  logger's last resort handler. This is regarded as the best default behaviour.