import sys
import re
import yaml
from pathlib import Path
from datetime import datetime, timezone


def time_in_seconds(time_string: str):
    """Converts times given as string in the form <Value><Unit> to seconds"""
    pattern = re.compile(r"^(?P<value>\d+)(?P<unit>[a-zA-Z])?$")
    match = pattern.match(time_string)
    if not match:
        raise ValueError("Unable to parse given time String {t}.\
            ".format(t=time_string))
    if match.group('unit'):
        unit = match.group('unit').upper()
    else:
        unit = 'S'
    multiplier = {
        'S': 1,
        'M': 60,
        'H': 3600,
        'D': 86400,
    }
    if unit in multiplier:
        return int(match.group('value')) * multiplier[unit]
    else:
        raise ValueError("Unsupported time unit {u}".format(u=unit))


def open_configfile(filepath):
    """returns yaml config from file if file exists and is valid yaml"""
    try:
        Path(filepath).resolve(strict=True)
    except FileNotFoundError as e:
        print("Unable to access configfile {f}:\
            ".format(f=filepath), file=sys.stderr)
        print(e, file=sys.stderr)
        exit(2)

    with open(filepath) as configfile:
        try:
            config = yaml.load(configfile, Loader=yaml.FullLoader)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
            print("Unable to parse {f} as YAML:\
                ".format(f=filepath), file=sys.stderr)
            print(e, file=sys.stderr)
            exit(3)

        required_config_keys = [
            'repository_name',
            'repository',
            'retention_time'
        ]
        for key in required_config_keys:
            if key not in config:
                raise ValueError("Could not find required paramter {k} in {f}.\
                    ".format(k=key, f=filepath))
        return config


def snapshot_name():
    snapshot_timestamp = datetime.utcnow()
    timestamp_string = snapshot_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    snapshot_name = "essnapshot_{d}".format(d=timestamp_string)
    return snapshot_name


def check_snapshots_in_progress(snapshots: list):
    """Checks the list of snapshots for shit"""
    if len([s['id'] for s in snapshots if s['status'] == 'IN_PROGRESS']) > 0:
        return True
    else:
        return False


def find_delete_eligible_snapshots(
        snapshots: list,
        retention_time: str,
        from_time=datetime.utcnow()):
    delete_eligible_snapshots = []
    for snapshot in snapshots:
        snapshot_timestamp = datetime.fromtimestamp(int(snapshot['end_epoch']),
                                                    tz=timezone.utc)
        snapshot_age_seconds = (from_time - snapshot_timestamp).total_seconds()
        if int(snapshot_age_seconds) > time_in_seconds(retention_time):
            delete_eligible_snapshots.append(snapshot['id'])
            print("Marked snapshot {s} as eligible for deletion.\
                ".format(s=snapshot['id']))
    return delete_eligible_snapshots
