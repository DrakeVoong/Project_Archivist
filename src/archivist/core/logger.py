import logging
import sys

# Get-Content -Path data\logs\archivist.log -Wait -Tail 50

def setup_logging(level=logging.INFO, logfile=None) -> None:
    root = logging.getLogger("archivist")  # parent of every archivist.* logger
    root.setLevel(level)
    if root.handlers:
        return

    format = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(format)
    # root.addHandler(console)

    if logfile:
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setFormatter(format)
        root.addHandler(fh)