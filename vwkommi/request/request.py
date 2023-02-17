"""Module performing requests and storing data"""
from datetime import datetime
from typing import Union
from concurrent.futures import as_completed, ThreadPoolExecutor
import json
import os
import requests
import secrets
import time
from vwkommi.request.auth import Auth
from vwkommi.settings import Settings


class DataRequest:  # pylint: disable=too-few-public-methods
    """Class performing requests.

    The requested data is stored within the _raw_data_ subdirectory
    """

    DETAILS_URL = "https://myvw-gvf-proxy-prod.apps.mega.cariad.cloud/vehicleDetails/de-DE/"
    DATA_URL = "https://myvw-gvf-proxy-prod.apps.mega.cariad.cloud/vehicleData/de-DE/"
    VIN_URL = "https://production.emea.vdbs.cariad.digital/v1/vehicles/"
    IMAGE_URL = "https://myvw-vilma-proxy-prod.apps.mega.cariad.cloud/vehicleimages/exterior/"

    PROFILE_URL = (
        "https://apps.emea.vum.cariad.digital/v2/users/me/relations"
    )

    YEAR = 2020
    TRY_YEARS = [2020, 2021, 2022, 2023]

    def __init__(self) -> None:
        self.settings = Settings()
        self.auth = Auth()
        self.headers = {
            "Authorization": self.auth.get_token(),
            "User-Agent": 'Chrome v22.2 Linux Ubuntu'
        }
        self.year = 2020
        self.num_404 = 0
        self.commission_number_count = 0
        self.session = requests.session()
        for kommi_item in self.settings.commission_number_range:
            self.commission_number_count += (kommi_item[2] - kommi_item[1]) + 1

    def do_requests(self) -> None:
        """Performs all requests and stores the results to the file system.

        There will be one file for each range. The files will be stores within the subdirectory
        _raw_data_.
        """
        handled_kommis = 0
        time_str = datetime.now().strftime(
            "%Y-%m-%dT%H.%M.%S"
        )  # use the same time for all requests

        # create output directory
        if not os.path.exists(os.path.join(self.settings.base_dir, "raw_data")):
            os.mkdir(os.path.join(self.settings.base_dir, "raw_data"))
        for (
            kommi_item
        ) in self.settings.commission_number_range:  # loop over every range
            with ThreadPoolExecutor(
                max_workers=self.settings.worker_count
            ) as executor:  # self.settings.worker_count threads
                map_args = [
                    [
                        kommi_item[0],
                        kommi_item[3] if len(kommi_item) >= 4 else 4,
                        arg,
                        self,
                    ]
                    for arg in range(kommi_item[1], kommi_item[2] + 1)
                ]
                data_dict = {}
                futures = []
                for args in map_args:
                    futures.append(executor.submit(DataRequest.__requests_worker, args))
                for future in as_completed(futures):
                    result = future.result()
                    handled_kommis += 1

                    # check result for bool value
                    if result is True:
                        executor.shutdown(cancel_futures=True)
                        break
                    if result is False:
                        print(
                            (
                                "Progress: "
                                f"{((handled_kommis/self.commission_number_count)*100):.2f}"
                            ),
                            end="\r",
                        )
                        self.num_404 += 1
                        if self.num_404 >= 500:
                            print("Reached end of data!")
                            break
                        continue

                    # data is valid
                    # reset num_404 as soon as we have valid data
                    self.num_404 = 0

                    # get results from threads
                    (
                        year,
                        kommi,
                        data_response,
                        details_response,
                        production_response,
                        image_response,
                    ) = result

                    # store latest successful year for next requests to lower 404 requests
                    # this is not perfect due to the threads but better than nothing
                    if year != DataRequest.YEAR:
                        DataRequest.YEAR = year

                    data_dict[kommi] = (
                        "["
                        + data_response
                        + ","
                        + details_response
                        + ","
                        + production_response
                        + ","
                        + image_response
                        + "]"
                    )
                    print(
                        (
                            "Progress: "
                            f"{((handled_kommis/self.commission_number_count)*100):.2f}%"
                        ),
                        end="\r",
                    )
                # set file name
                filename = f"output_{kommi_item[0]}_{kommi_item[1]}-{kommi_item[2]}_{time_str}.json"
                with open(
                    os.path.join(self.settings.base_dir, "raw_data", filename),
                    "w",
                    encoding="utf-8",
                ) as file:
                    file.write("{\n")  # first line

                    first = True  # just to put all the commas correctly
                    for kommi_key in sorted(data_dict):
                        if first is False:
                            file.write(",\n")
                        first = False
                        file.write('"' + kommi_key + '":' + data_dict[kommi_key])

                    file.write("\n}\n")  # last line

    def find_prefix(self, commission_number: str) -> Union[bool, tuple]:
        """Finds the prefix of a certain commission number."""
        print("Start looking for car.")
        map_args = [
            [commission_number, arg, self.headers, self.session] for arg in range(1000)
        ]
        with ThreadPoolExecutor(max_workers=30) as executor:  # 30 threads
            for result in executor.map(
                DataRequest.__find_commission_number_worker, map_args
            ):
                if not isinstance(result, bool):
                    return result
        return False

    def add_to_profile(self, commission_number: str) -> bool:
        """Tries to add a commission number to the profile."""
        result = self.find_prefix(commission_number=commission_number)
        if isinstance(result, bool):
            print("No car seems to match the commission number.")
            return False
        else:
            prefix, year = result
            response = self.session.get(
                f"{DataRequest.DATA_URL}{prefix}{year}{commission_number}",
                headers=self.headers,
            )
            if response.status_code != 200:
                return False
            response = response.json()
            if not "modelName" in response:
                print("Model name not within vehicle data")
                return False
            model_name = response["modelName"]
            headers = self.headers
            headers["traceId"] = (
                f"{secrets.token_hex(4)}-{secrets.token_hex(2)}-"
                f"{secrets.token_hex(2)}-{secrets.token_hex(2)}-"
                f"{secrets.token_hex(6)}"
            )
            headers["Content-Type"] = "application/json"
            json_data = {
                "vehicleNickname": f"{model_name}",
                "vehicle": {"commissionId": f"{commission_number}-{prefix}-{year}"},
            }
            response = self.session.post(
                DataRequest.PROFILE_URL, headers=headers, json=json_data
            )
            if response.status_code == 422:
                print("Car already added to profile")
                return False
            if response.status_code != 201:
                print("Request to add car failed.", response.status_code)
                return False
            print(f"Added car: {model_name} (year: {year}, prefix: {prefix})")
            return True

    def reset_login(self):
        self.auth.reset_token()
        self.headers = {"Authorization": self.auth.get_token()}

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    @staticmethod
    def __requests_worker(args) -> Union[bool, tuple]:
        """worker thread"""

        # inner function to handle actual request including relogin once
        def __data_request(_url: str):
            response = self.session.get(
                _url,
                headers=self.headers,
            )
            # try request once again
            if response.status_code == 401 or response.status_code == 502:
                self.reset_login()
                response = requests.get(
                    _url,
                    headers=self.headers,
                )
            return response

        def __busy_wait() -> bool:
            wait_count = 0
            while not self.auth.is_authenticated():
                time.sleep(1)
                wait_count += 1
                if wait_count == 9:
                    return False
            return True

        # basic data for request
        year = DataRequest.YEAR
        kommi_pre, number_length, index, self = args  # args for the worker
        prefix_list = self.settings.prefix_list  # possible prefixes
        shutdown = False  # variable to stop worker
        url_append = (
            f"{kommi_pre}{index:0{number_length}d}"  # commission number (e.g. AF1234)
        )

        # request general car data
        # to store prefix for future requests with this worker once found by the following loop
        response = None
        prefix = 0
        # build list with years to check beginning with the "most" likely
        years = [year]
        years.extend([_year for _year in DataRequest.TRY_YEARS if _year != year])
        for _prefix in prefix_list:  # try all prefixes
            success = False
            for _year in years:

                # simply wait some time until the next login or give up after 10s
                if not __busy_wait():
                    return True

                response = __data_request(
                    f"{DataRequest.DATA_URL}{_prefix}{_year}{url_append}"
                )
                if response.status_code != 200:
                    if response.status_code == 404:
                        continue
                    if response.status_code == 401 or response.status_code == 502:
                        shutdown = True
                    return shutdown
                prefix = _prefix
                year = _year
                success = True
                break
            if success is True:
                break

        # store data response
        data_response = response.json()

        # get production data and line drawing if VIN or store some default values
        production_status = [
            {"codeText": "Produktionsstatus: keine FIN"},
            {"codeText": "FIN verbunden: nein"},
        ]
        production_json = None
        image_status = {"codeText": "Bild: keine FIN"}
        image_json = None
        if self.settings.skip_fin_details is False and "vin" in data_response:
            vin = data_response["vin"]  # store VIN

            # simply wait some time until the next login or give up after 10s
            if not __busy_wait():
                return True

            # request production data
            response = __data_request(f"{DataRequest.VIN_URL}{vin}/device-platform")
            if response.status_code != 200:
                if response.status_code == 401:
                    shutdown = True
                return shutdown

            # set the data
            production_json = response.json()
            production_status = [
                {"codeText": f'Produktionsstatus: {production_json["stage"]}'},
                {"codeText": f'FIN verbunden: {production_json["connected"]}'},
            ]
            production_json = {
                "stage": production_json["stage"],
                "connected": production_json["connected"],
            }

            # simply wait some time until the next login or give up after 10s
            if not __busy_wait():
                return True

            # request line drawing
            response = __data_request(f"{DataRequest.IMAGE_URL}{vin}")
            if response.status_code != 200:
                if response.status_code == 401:
                    shutdown = True
                return shutdown

            # set the data
            image_json = response.json()
            has_images = len(image_json["imageUrls"]) > 1
            image_status_str = "Strichzeichnung" if has_images is False else "Normal"
            image_status = {"codeText": f"Bild: {image_status_str}"}
            image_json = {"hasImages": has_images}

        # simply wait some time until the next login or give up after 10s
        if not __busy_wait():
            return True

        # request detailed car data
        response = __data_request(
            f"{DataRequest.DETAILS_URL}{prefix}{year}{url_append}"
        )
        if response.status_code != 200:
            if response.status_code == 401:
                shutdown = True
            return shutdown
        details_response = response.json()

        # filter data
        if (
            not "specifications" in details_response
        ):  # some commission numbers are without specs
            details_response["specifications"] = []
        model_name = data_response["modelName"] if "modelName" in data_response else ""
        if model_name == "ID.3 Pro S":
            model_name = "ID.3 Pro S (4-Sitzer)"
        if model_name == "ID.3 Pro S (4-Sitzer)":
            for spec in details_response["specifications"]:
                if spec["codeText"][:11] == "3 Rücksitze":
                    model_name = "ID.3 Pro S (5-Sitzer)"
                    break
        elif model_name == "ID.4":
            model_name = "ID.4 GTX"
        elif model_name == "ID.5":
            model_name = "ID.5 GTX"
        if "modelName" in data_response:
            data_response["modelName"] = model_name

        # apply some theories
        pedal_spec = False
        service_spec = False
        for spec in details_response["specifications"]:
            if service_spec is True:
                if spec["codeText"].startswith("Umweltbonus"):
                    details_response["specifications"].append(
                        {"codeText": "eGolf-lu: A", "origin": ""}
                    )
                else:
                    details_response["specifications"].append(
                        {"codeText": "eGolf-lu: B", "origin": ""}
                    )
                break
            if pedal_spec is True:
                if spec["codeText"].startswith("Serviceanzeige"):
                    service_spec = True
                else:
                    details_response["specifications"].append(
                        {"codeText": "eGolf-lu: B", "origin": ""}
                    )
                    break
            pedal_spec = spec["codeText"].startswith("Fußhebelwerk") or spec[
                "codeText"
            ].startswith("Pedale")
        details_response["specifications"].extend(production_status)
        details_response["specifications"].append(image_status)

        # return everything including used year as we want to use that for all new requests
        return (
            year,
            url_append,
            json.dumps(data_response, separators=(",", ":"), ensure_ascii=False),
            json.dumps(details_response, separators=(",", ":"), ensure_ascii=False),
            json.dumps(production_json, separators=(",", ":"), ensure_ascii=False),
            json.dumps(image_json, separators=(",", ":"), ensure_ascii=False),
        )

    @staticmethod
    def __find_commission_number_worker(args) -> Union[bool, tuple]:
        commission_number, prefix, headers, session = args
        for _year in DataRequest.TRY_YEARS:
            response = session.get(
                f"{DataRequest.DATA_URL}{prefix}{_year}{commission_number}",
                headers=headers,
            )
            if response.status_code == 200:
                return (prefix, _year)
        return False
