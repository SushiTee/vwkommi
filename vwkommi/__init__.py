"""vwkommi module init."""
import argparse
import sys
from vwkommi.request.request import DataRequest
from vwkommi.settings import (
    BASE_DIR,
    WORKER_COUNT,
    VW_USERNAME,
    VW_PASSWORD,
    PREFIX_LIST,
    SKIP_VIN_DETAILS,
    COMMISSION_NUMBER_RANGE,
    Settings,
)

__version__ = "1.0"


class VwKommi:  # pylint: disable=too-few-public-methods
    """Entry class"""

    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            description="VW Kommi",
            usage=(
                "vwkommi <command> [args]\n\n"
                "The following commands are available:\n"
                "  request - Requests data from VW and stores them into the _raw_data_ directory"
            ),
        )
        parser.add_argument("command", help="Subcommand to run")
        args = parser.parse_args(sys.argv[1:2])
        command = args.command.replace("-", "_")  # convert - to _ to call function
        if not hasattr(VwKommi, command) or command.startswith("_"):
            print("Unrecognized command")
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(VwKommi, command)()

    @staticmethod
    def request() -> None:
        """Starts requesting data from the VW server.

        The data is somewhat filtered and stored into the _raw_data_ subdirectory.

        There are no arguments except for the default _-h_ for help.
        """
        parser = argparse.ArgumentParser(description="VW Kommi Requests")
        parser.add_argument(
            "-b",
            "--base-dir",
            dest="base_dir",
            default=None,
            help="Directory to store downloaded data to",
        )
        parser.add_argument(
            "-w",
            "--worker-count",
            dest="worker_count",
            type=int,
            default=None,
            help="Number of workers to use for requests.",
        )
        parser.add_argument(
            "-u",
            "--username",
            dest="username",
            default=None,
            help="Username to make requests with",
        )
        parser.add_argument(
            "-p",
            "--password",
            dest="password",
            default=None,
            help="Password for username",
        )
        parser.add_argument(
            "-P",
            "--prefix-list",
            dest="prefix_list",
            default=None,
            help="List of prefix numbers to try",
        )
        parser.add_argument(
            "-s",
            "--skip-fin-details",
            dest="skip_fin_details",
            default=None,
            help="Weather fin details should be skipped or not",
        )
        parser.add_argument(
            "-c",
            "--commission-number-range",
            dest="commission_number_range",
            default=None,
            help='Commission number range (e.g. [("AF", 5000, 9999, 4),("AG", 0, 9999, 4)])',
        )
        parser.add_argument(
            "-f",
            "--find-prefix",
            dest="commission_number_find",
            default=None,
            help="Tries to find the prefix for a specific commission number",
        )
        parser.add_argument(
            "-a",
            "--add-to-profile",
            dest="commission_number_add",
            default=None,
            help="Tries to find the prefix for a specific commission number",
        )
        args = parser.parse_args(sys.argv[2:])
        if VwKommi.__override_default_settings(args) is False:
            print("There was an error while overwriting the settings values.")
            return
        data_request = DataRequest()
        if args.commission_number_find is not None:
            result = data_request.find_prefix(args.commission_number_find)
            if isinstance(result, bool):
                print("No prefix year combination found!")
            else:
                prefix, year = result
                print(f"Prefix: {prefix}, year: {year}")
            return
        if args.commission_number_add is not None:
            if data_request.add_to_profile(args.commission_number_add) is True:
                print(f"{args.commission_number_add} added to profile")
            else:
                print(f"Could not add {args.commission_number_add} to profile")
            return
        data_request.do_requests()

    @staticmethod
    def __override_default_settings(args) -> bool:
        settings = Settings(
            BASE_DIR,
            WORKER_COUNT,
            VW_USERNAME,
            VW_PASSWORD,
            PREFIX_LIST,
            SKIP_VIN_DETAILS,
            COMMISSION_NUMBER_RANGE,
        )
        return settings.update_settings(
            base_dir=args.base_dir,
            worker_count=args.worker_count,
            username=args.username,
            password=args.password,
            prefix_list=args.prefix_list,
            skip_fin_details=args.skip_fin_details,
            commission_number_range=args.commission_number_range,
        )
