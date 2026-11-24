import json
import logging


class SafeFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "level": record.levelname,
                "event": "application_diagnostic",
                "component": record.name.split(".")[0],
            }
        )
