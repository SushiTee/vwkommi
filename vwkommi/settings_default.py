"""Module containing the default settings."""
import json
import os

# Base path for module
BASE_DIR = os.path.dirname(__file__)

# worker count
WORKER_COUNT = 30

# VW user data (make sure to change it to correct data)
VW_USERNAME = "example_user"
VW_PASSWORD = "example_password"

# known request prefixes
PREFIX_LIST = [185, 900, 877, 902]  # known prefixes for ID.3/4/5

# skip requesting extra details for cars with VIN like line drawings
SKIP_VIN_DETAILS = True

# commission number range
COMMISSION_NUMBER_RANGE = [
    ("AF", 5000, 9999, 4),
    ("AG", 0, 9999, 4),
    ("AH", 0, 9999, 4),
    ("AI", 0, 9999, 4),
    ("AJ", 0, 9999, 4),
    ("AK", 0, 9999, 4),
    ("AL", 0, 9999, 4),
    ("AM", 0, 9999, 4),
    ("AN", 0, 9999, 4),
    ("AO", 0, 9999, 4),
    ("AP", 0, 9999, 4),
    ("AQ", 0, 9999, 4),
]


class Settings(object):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(
        self,
        base_dir: str,
        worker_count: int,
        username: str,
        password: str,
        prefix_list: list,
        skip_fin_details: bool,
        commission_number_range: list,
    ):
        self.base_dir = base_dir
        self.worker_count = worker_count
        self.username = username
        self.password = password
        self.prefix_list = prefix_list
        self.skip_fin_details = skip_fin_details
        self.commission_number_range = commission_number_range

    def update_settings(
        self,
        base_dir: str = None,
        worker_count: str = None,
        username: str = None,
        password: str = None,
        prefix_list: str = None,
        skip_fin_details: str = None,
        commission_number_range: str = None,
    ) -> bool:
        """Overrides settings variables."""
        return_value = True
        if base_dir is not None:
            if not os.path.isdir(base_dir):
                print(f"{base_dir} is not a valid directory.")
                return_value = False
            else:
                self.base_dir = base_dir
        if worker_count is not None:
            try:
                self.worker_count = int(worker_count)
            except ValueError:
                print(f"{worker_count} is not a valid integer.")
                return_value = False
        if username is not None:
            print(username)
            self.username = username
        if password is not None:
            self.password = password
        if prefix_list is not None:
            try:
                prefix_list = json.loads(prefix_list)
                list_valid = False
                if isinstance(prefix_list, list):
                    list_valid = True
                    for entry in prefix_list:
                        if not isinstance(entry, int):
                            list_valid = False
                            break
                if list_valid is True:
                    self.prefix_list = prefix_list
                else:
                    print("The prefix list must contain integers only.")
                    return_value = False
            except json.decoder.JSONDecodeError:
                print("The value of the prefix list parameter could not be parsed.")
                return_value = False
        if skip_fin_details is not None:
            self.skip_fin_details = False
            if skip_fin_details.lower() in [
                "true",
                "1",
                "t",
                "y",
                "yes",
                "yeah",
                "yup",
                "certainly",
                "uh-huh",
            ]:
                self.skip_fin_details = True
        if commission_number_range is not None:
            try:
                commission_number_range = json.loads(commission_number_range)
                if not isinstance(commission_number_range, list):
                    print("commission number range parameter must be a list.")
                    return_value = False
                    return return_value
                type_list = [str, int, int, int]
                list_valid = True
                for _range in commission_number_range:
                    if len(_range) != 4:
                        list_valid = False
                        break
                    entries_valid = True
                    for index, entry in enumerate(_range):
                        if not isinstance(entry, type_list[index]):
                            entries_valid = False
                            break
                    if entries_valid is False:
                        list_valid = False
                        break
                if list_valid is True:
                    self.commission_number_range = commission_number_range
            except json.decoder.JSONDecodeError:
                print(
                    "The value of the commission number range parameter could not be parsed."
                )
                return_value = False
        return return_value
