
"""vwkommi module init."""
import argparse
import sys
from vwkommi.request.request import DataRequest

__version__ = "1.0"

class VwKommi: # pylint: disable=too-few-public-methods
    """Entry class"""

    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            description='VW Kommi',
            usage=('vwkommi <command> [args]\n\n'
                   'The following commands are available:\n'
                   '  request - Requests data from VW and stores them into the _raw_data_ directory'
            )
        )
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        command = args.command.replace('-', '_') # convert - to _ to call function
        if not hasattr(VwKommi, command):
            print('Unrecognized command')
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
        parser = argparse.ArgumentParser(description='VW Kommi Requests')
        parser.add_argument('-f', '--find-prefix', dest='commission_number_find', default=None,
                        help='Tries to find the prefix for a specific commission number')
        parser.add_argument('-a', '--add-to-profile', dest='commission_number_add', default=None,
                        help='Tries to find the prefix for a specific commission number')
        args = parser.parse_args(sys.argv[2:])
        data_request = DataRequest()
        if args.commission_number_find is not None:
            result = data_request.find_prefix(args.commission_number_find)
            if isinstance(result, bool):
                print('No prefix year combination found!')
            else:
                prefix, year = result
                print(f'Prefix: {prefix}, year: {year}')
            return
        if args.commission_number_add is not None:
            if data_request.add_to_profile(args.commission_number_add) is True:
                print(f'{args.commission_number_add} added to profile')
            else:
                print(f'Could not add {args.commission_number_add} to profile')
            return
        data_request.do_requests()
