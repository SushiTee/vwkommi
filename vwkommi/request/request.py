"""Module performing requests and storing data"""
from datetime import datetime
from typing import Union
from concurrent.futures import ThreadPoolExecutor
import json
import os
import requests
import secrets
import time
from vwkommi.request.auth import Auth
from vwkommi.settings import BASE_DIR, COMMISSION_NUMBER_RANGE, PREFIX_LIST, SKIP_VIN_DETAILS

class DataRequest: # pylint: disable=too-few-public-methods
    """Class performing requests.

    The requested data is stored within the _raw_data_ subdirectory
    """
    DETAILS_URL = 'https://myvw-gvf-proxy.apps.emea.vwapps.io/vehicleDetails/de-DE/'
    DATA_URL = 'https://myvw-gvf-proxy.apps.emea.vwapps.io/vehicleData/de-DE/'
    VIN_URL = 'https://vdbs.apps.emea.vwapps.io/v1/vehicles/'
    IMAGE_URL = 'https://vehicle-image.apps.emea.vwapps.io/vehicleimages/exterior/'
    PROFILE_URL = 'https://vum.apps.emea.vwapps.io/v1/dataStorageManagement/users/me/relations'

    YEAR = 2020
    TRY_YEARS = [2020, 2021, 2022, 2023]

    def __init__(self) -> None:
        auth = Auth()
        self.headers = {
            'Authorization': auth.get_token()
        }
        self.year = 2020
        self.num_404 = 0
        self.commission_number_count = 0
        for kommi_item in COMMISSION_NUMBER_RANGE:
            self.commission_number_count += (kommi_item[2] - kommi_item[1]) + 1

    def do_requests(self) -> None:
        """Performs all requests and stores the results to the file system.

        There will be one file for each range. The files will be stores within the subdirectory
        _raw_data_.
        """
        handled_kommis = 0
        time_str = datetime.now().strftime("%Y-%m-%dT%H.%M.%S") # use the same time for all requests

        # create output directory
        if not os.path.exists(os.path.join(BASE_DIR, 'raw_data')):
            os.mkdir(os.path.join(BASE_DIR, 'raw_data'))
        for kommi_item in COMMISSION_NUMBER_RANGE: # loop over every range
            with ThreadPoolExecutor(max_workers=30) as executor: # 30 threads
                # set file name
                filename = f'output_{kommi_item[0]}_{kommi_item[1]}-{kommi_item[2]}_{time_str}.json'
                with open(os.path.join(BASE_DIR, 'raw_data', filename), 'w',
                          encoding='utf-8') as file:
                    file.write('{\n') # first line

                    first = True # just to put all the commas correctly
                    map_args = [
                        [
                            kommi_item[0],
                            kommi_item[3] if len(kommi_item) >= 4 else 4,
                            arg,
                            self.headers
                        ]
                        for arg in range(kommi_item[1], kommi_item[2] + 1)
                    ]
                    for result in executor.map(DataRequest.__requests_worker, map_args):
                        handled_kommis += 1

                        # check result for bool value
                        if result is True:
                            executor.shutdown(cancel_futures=True)
                            break
                        if result is False:
                            print(('Progress: '
                                   f'{((handled_kommis/self.commission_number_count)*100):.2f}'),
                                  end='\r')
                            self.num_404 += 1
                            if self.num_404 >= 500:
                                print('Reached end of data!')
                                break
                            continue

                        # data is valid
                        # reset num_404 as soon as we have valid data
                        self.num_404 = 0
                        if first is False:
                            file.write(',\n')
                        first = False

                        # get results from threads
                        (year, kommi, data_response, details_response, production_response,
                         image_response) = result

                        # store latest successful year for next requests to lower 404 requests
                        # this is not perfect due to the threads but better than nothing
                        if year != DataRequest.YEAR:
                            DataRequest.YEAR = year

                        # write to file
                        file.write('"' + kommi + '": [' + data_response + ',' +  details_response +
                                   ',' +  production_response + ',' +  image_response + ']')
                        print(('Progress: '
                               f'{((handled_kommis/self.commission_number_count)*100):.2f}%')
                              , end='\r')

                    file.write('\n}\n') # last line

    def find_prefix(self, commission_number: str) -> Union[bool, tuple]:
        """Finds the prefix of a certain commission number."""
        print('Start looking for car.')
        map_args = [
            [commission_number, arg, self.headers]
            for arg in range(1000)
        ]
        with ThreadPoolExecutor(max_workers=30) as executor: # 30 threads
            for result in executor.map(DataRequest.__find_commission_number_worker, map_args):
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
            response = requests.get(f'{DataRequest.DATA_URL}{prefix}{year}{commission_number}',
                                        headers=self.headers)
            if response.status_code != 200:
                return False
            response = response.json()
            if not 'modelName' in response:
                print('Model name not within vehicle data')
                return False
            model_name = response["modelName"]
            headers = self.headers
            headers['traceId'] = (f'{secrets.token_hex(4)}-{secrets.token_hex(2)}-'
                                  f'{secrets.token_hex(2)}-{secrets.token_hex(2)}-'
                                  f'{secrets.token_hex(6)}')
            headers['Content-Type'] = 'application/json'
            json_data = {
                'vehicleNickname': f'{model_name}',
                'vehicle': {
                    'commissionId': f'{commission_number}-{prefix}-{year}'
                }
            }
            response = requests.post(DataRequest.PROFILE_URL, headers=headers, json=json_data)
            if response.status_code == 422:
                print('Car already added to profile')
                return False
            if response.status_code != 201:
                print('Request to add car failed.', response.status_code)
                return False
            print(f'Added car: {model_name} (year: {year}, prefix: {prefix})')
            return True

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    @staticmethod
    def __requests_worker(args) -> Union[bool, tuple]:
        """worker thread"""
        # basic data for request
        prefix_list = PREFIX_LIST # possible prefixes
        year = DataRequest.YEAR
        kommi_pre, number_length, index, headers = args # args for the worker
        shutdown = False # variable to stop worker
        url_append = f'{kommi_pre}{index:0{number_length}d}' # commission number (e.g. AF1234)

        # request general car data
        # to store prefix for future requests with this worker once found by the following loop
        response = None
        prefix = 0
        # build list with years to check beginning with the "most" likely
        years = [year]
        years.extend([_year for _year in DataRequest.TRY_YEARS if _year != year])
        for _prefix in prefix_list: # try all prefixes
            success = False
            for _year in years:
                response = requests.get(f'{DataRequest.DATA_URL}{_prefix}{_year}{url_append}',
                                        headers=headers)
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
        production_status = [{'codeText':'Produktionsstatus: keine FIN'},
                             {'codeText':'FIN verbunden: nein'}]
        production_json = None
        image_status = {'codeText':'Bild: keine FIN'}
        image_json = None
        if SKIP_VIN_DETAILS is False and 'vin' in data_response:
            vin = data_response['vin'] # store VIN

            # request production data
            response = requests.get(f'{DataRequest.VIN_URL}{vin}/device-platform', headers=headers)
            if response.status_code != 200:
                if response.status_code == 401:
                    shutdown = True
                return shutdown

            # set the data
            production_json = response.json()
            production_status = [{'codeText': f'Produktionsstatus: {production_json["stage"]}'},
                                 {'codeText': f'FIN verbunden: {production_json["connected"]}'}]
            production_json = {'stage': production_json["stage"],
                               'connected': production_json["connected"]}

            # request line drawing
            response = requests.get(f'{DataRequest.IMAGE_URL}{vin}', headers=headers)
            if response.status_code != 200:
                if response.status_code == 401:
                    shutdown = True
                return shutdown

            # set the data
            image_json = response.json()
            has_images = len(image_json['imageUrls']) > 1
            image_status_str = 'Strichzeichnung' if has_images is False else 'Normal'
            image_status = {'codeText': f'Bild: {image_status_str}'}
            image_json = {'hasImages': has_images}

        # request detailed car data
        response = requests.get(f'{DataRequest.DETAILS_URL}{prefix}{year}{url_append}',
                                headers=headers)
        if response.status_code != 200:
            if response.status_code == 401:
                shutdown = True
            return shutdown
        details_response = response.json()

        # filter data
        if not 'specifications' in details_response: # some commission numbers are without specs
            details_response['specifications'] = []
        model_name = data_response['modelName'] if 'modelName' in data_response else ''
        if model_name == 'ID.3 Pro S':
            model_name = 'ID.3 Pro S (4-Sitzer)'
        if model_name == 'ID.3 Pro S (4-Sitzer)':
            for spec in details_response['specifications']:
                if spec['codeText'][:11] == '3 Rücksitze':
                    model_name = 'ID.3 Pro S (5-Sitzer)'
                    break
        elif model_name == 'ID.4':
            model_name = 'ID.4 GTX'
        elif model_name == 'ID.5':
            model_name = 'ID.5 GTX'
        if 'modelName' in data_response:
            data_response['modelName'] = model_name

        # apply some theories
        pedal_spec = False
        service_spec = False
        for spec in details_response['specifications']:
            if service_spec is True:
                if spec['codeText'].startswith('Umweltbonus'):
                    details_response['specifications'].append(
                        {"codeText":"eGolf-lu: A","origin":""}
                    )
                else:
                    details_response['specifications'].append(
                        {"codeText":"eGolf-lu: B","origin":""}
                    )
                break
            if pedal_spec is True:
                if spec['codeText'].startswith('Serviceanzeige'):
                    service_spec = True
                else:
                    details_response['specifications'].append(
                        {"codeText":"eGolf-lu: B","origin":""}
                    )
                    break
            pedal_spec = (spec['codeText'].startswith('Fußhebelwerk')
                            or spec['codeText'].startswith('Pedale'))
        details_response['specifications'].extend(production_status)
        details_response['specifications'].append(image_status)

        # return everything including used year as we want to use that for all new requests
        return (year, url_append,
                json.dumps(data_response, separators=(',', ':'), ensure_ascii=False),
                json.dumps(details_response, separators=(',', ':'), ensure_ascii=False),
                json.dumps(production_json, separators=(',', ':'), ensure_ascii=False),
                json.dumps(image_json, separators=(',', ':'), ensure_ascii=False))

    @staticmethod
    def __find_commission_number_worker(args) -> Union[bool, tuple]:
        commission_number, prefix, headers = args
        for _year in DataRequest.TRY_YEARS:
            response = requests.get(f'{DataRequest.DATA_URL}{prefix}{_year}{commission_number}',
                                            headers=headers)
            if response.status_code == 200:
                return (prefix, _year)
        return False
