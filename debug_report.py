import sys
import traceback

try:
    from ecust_electricity_monitor.cli import report

    report(days=7, threshold=30.0, output_dir=None, output_filename=None, no_open=True)
except Exception:
    traceback.print_exc()
    sys.exit(1)
