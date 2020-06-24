import shutil
from typing import Dict, Tuple, Any, Callable
from dateparser import parse

from CommonServerPython import *


# Disable insecure warnings
requests.packages.urllib3.disable_warnings()

# CONSTANTS
DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class Client(BaseClient):
    """
    Client to use in the Zimperium integration. Overrides BaseClient
    """

    def __init__(self, base_url: str, api_key: str, verify: bool):
        super().__init__(base_url=base_url, verify=verify)
        self._headers = {'api_key': api_key, 'Accept': 'application/json'}
        self._proxies = handle_proxy()

    def users_search_request(self, query: str, size: str, page: str) -> dict:
        """Search users by sending a GET request.

        Args:
            query: users search query.
            size: response size.
            page: response page.
        Returns:
            Response from API.
        """
        params = {
            'rsql': query,
            'size': size,
            'page': page,
        }
        return self._http_request(method='GET', url_suffix='/users/public/search', headers=self._headers, params=params)

    def user_get_by_id_request(self, object_id: str) -> dict:
        """Retrieve user details by sending a GET request.

        Args:
            object_id: object ID.
        Returns:
            Response from API.
        """
        return self._http_request(method='GET', url_suffix=f'/users/public/{object_id}', headers=self._headers)

    def devices_search_request(self, query: str, size: str, page: str) -> dict:
        """Search devices by sending a GET request.

        Args:
            query: devices search query.
            size: response size.
            page: response page.
        Returns:
            Response from API.
        """
        params = {
            'rsql': query,
            'size': size,
            'page': page,
        }
        return self._http_request(method='GET', url_suffix='/devices/public/search', headers=self._headers,
                                  params=params)

    def device_get_by_id_request(self, zdid: str, device_id: str) -> dict:
        """Retrieve device details by sending a GET request.

        Args:
            zdid: zimperium ID.
            device_id: device ID.
        Returns:
            Response from API.
        """
        if (zdid and device_id) or (not zdid and not device_id):
            raise Exception("To get device by ID, use the zdid or the device_id argument.")

        if zdid:
            url_suffix = f'/devices/public/{zdid}'
        else:
            url_suffix = f'/devices/public/deviceId/{device_id}'

        return self._http_request(method='GET', url_suffix=url_suffix, headers=self._headers)

    def devices_get_last_updated_request(self, last_updated: str, exclude_deleted: bool, size: str, page: str)\
            -> dict:
        """Search last updated devices by sending a GET request.

        Args:
            last_updated: Last updated devices time frame.
            exclude_deleted: whether to exclude deleted devices.
            size: response size.
            page: response page.
        Returns:
            Response from API.
        """
        params = {
            'fromLastUpdate': last_updated,
            'excludeDeleted': exclude_deleted,
            'size': size,
            'page': page,
        }
        return self._http_request(method='GET', url_suffix='/devices/public/device_updates', headers=self._headers,
                                  params=params)

    def app_classification_get_request(self, app_hash: str, app_name: str) -> dict:
        """Retrieve device details by sending a GET request.

        Args:
            app_hash: application hash.
            app_name: application name.
        Returns:
            Response from API.
        """
        if (app_hash and app_name) or (not app_hash and not app_name):
            raise Exception("To get application classification, use the app_hash or the app_name argument.")

        if app_hash:
            url_suffix = f'/malware/public/classify/hash/{app_hash}'
        else:
            url_suffix = f'/malware/public/classify/name/{app_name}'

        return self._http_request(method='GET', url_suffix=url_suffix, headers=self._headers)

    def report_get_request(self, bundle_id: str, itunes_id: str, app_hash: str, platform: str) -> dict:
        """Retrieve device details by sending a GET request.

        Args:
            bundle_id: bundle ID.
            itunes_id: itunes ID.
            app_hash: application hash.
            platform: app platform
        Returns:
            Response from API.
        """
        if not bundle_id and not itunes_id and not app_hash:
            raise Exception("To get a report, use the bundle_id or the itunes_id or the app_hash argument.")
        if (bundle_id and itunes_id) or (bundle_id and app_hash) or (itunes_id and app_hash):
            raise Exception("To get a report, use exactly one of the arguments: bundle_id, itunes_id, app_hash.")

        params = {}
        if bundle_id:
            url_suffix = f'/malware/public/reports/bundle/{bundle_id}'
            params['platform'] = platform
        elif itunes_id:
            url_suffix = f'/malware/public/reports/itunes/{itunes_id}'
        else:
            url_suffix = f'/malware/public/reports/hash/{app_hash}'
            params['platform'] = platform

        return self._http_request(method='GET', url_suffix=url_suffix, headers=self._headers,
                                  params=params)

    def app_upload_for_analysis_request(self, entry_id: str) -> dict:
        """Upload an application for analysis by sending a POST request.

        Args:
            entry_id: entry ID.
        Returns:
            Response from API.
        """

        file_path = demisto.getFilePath(entry_id)['path']
        file_name = demisto.getFilePath(entry_id)['name']

        try:
            shutil.copy(file_path, file_name)
        except Exception:
            raise Exception('Failed to prepare application for upload.')

        try:
            with open(file_path, 'rb') as file:
                self._headers.update({'Content-Type': 'multipart/form-data'})
                result = self._http_request(method='POST', url_suffix='/malware/public/upload/app',
                                            headers=self._headers, files={'file1': file.read()}, timeout=240)
        except Exception as err:
            raise Exception(str(err))
        finally:
            shutil.rmtree(file_name, ignore_errors=True)

        return result

    def events_search_request(self, query: str, size: str, page: str, verbose: bool):
        """Search events by sending a GET request.

        Args:
            query: devices search query.
            size: response size.
            page: response page.
            verbose: whether to include full event details.
        Returns:
            Response from API.
        """
        params = {
            'rsql': query,
            'size': size,
            'page': page,
            'sort': 'deviceTime,asc',
            'includeFullEventDetail': verbose,
        }

        return self._http_request(method='GET', url_suffix=f'/events/public/search', headers=self._headers,
                                  params=params)


def test_module(client: Client, *_) -> Tuple[str, Dict, Dict]:
    """
    Performs basic get request to get incident samples
    """
    client.users_search_request(query='objectId==*', size='10', page='0')
    if demisto.params().get('isFetch'):
        client.events_search_request(query='eventId==*', size='10', page='0', verbose=False)
    return 'ok', {}, {}


def users_search(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Search users

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    query = str(args.get('query', 'objectId==*'))
    size = str(args.get('size', '10'))
    page = str(args.get('page', '0'))

    users = client.users_search_request(query, size, page)

    users_data = users.get('content')
    table_name = ''
    if not users.get('last'):
        table_name = f' (To get the next users, run the command with the next page)'
    headers = ['objectId', 'alias', 'firstName', 'middleName', 'lastName', 'email']
    human_readable = tableToMarkdown(name=f"Users{table_name}:", t=users_data, headers=headers, removeNull=True)
    entry_context = {f'Zimperium.Users(val.objectId === obj.objectId)': users_data}

    return human_readable, entry_context, users


def user_get_by_id(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Retrieve details for a single user.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    object_id = str(args.get('object_id', ''))

    user = client.user_get_by_id_request(object_id)

    headers = ['objectId', 'alias', 'firstName', 'middleName', 'lastName', 'email']
    human_readable = tableToMarkdown(name=f"User:", t=user, headers=headers, removeNull=True)
    entry_context = {f'Zimperium.Users(val.objectId === obj.objectId)': user}

    return human_readable, entry_context, user


def devices_search(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Search devices

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    query = str(args.get('query', 'deviceId==*'))
    size = str(args.get('size', '10'))
    page = str(args.get('page', '0'))

    devices = client.devices_search_request(query, size, page)

    devices_data = devices.get('content')
    table_name = ''
    if not devices.get('last'):
        table_name = f' (To get the next devices, run the command with the next page)'
    headers = ['deviceId', 'zdid', 'deviceHash', 'model', 'osType', 'osVersion', 'updatedDate']
    human_readable = tableToMarkdown(name=f"Devices{table_name}:", t=devices_data, headers=headers, removeNull=True)
    entry_context = {f'Zimperium.Devices(val.deviceId === obj.deviceId)': devices_data}

    return human_readable, entry_context, devices


def device_get_by_id(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Retrieve details for a single device.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    zdid = str(args.get('zdid', ''))
    device_id = str(args.get('device_id', ''))

    device = client.device_get_by_id_request(zdid, device_id)

    headers = ['deviceId', 'zdid', 'model', 'osType', 'osVersion', 'updatedDate', 'deviceHash']
    human_readable = tableToMarkdown(name=f"Device {device_id}:", t=device, headers=headers, removeNull=True)
    entry_context = {f'Zimperium.Devices(val.deviceId === obj.deviceId)': device}

    return human_readable, entry_context, device


def devices_get_last_updated(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Retrieve last updated devices

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    timestamp_format = '%Y-%m-%d'
    from_last_update = str(args.get('from_last_update', '1 day'))
    last_updated = parse_date_range(from_last_update, date_format=timestamp_format)[0]
    exclude_deleted = args.get('exclude_deleted') == 'false'
    size = str(args.get('size', '10'))
    page = str(args.get('page', '0'))

    devices = client.devices_get_last_updated_request(last_updated, exclude_deleted, size, page)

    devices_data = devices.get('content')
    table_name = ''
    if not devices.get('last'):
        table_name = f' (To get the next devices, run the command with the next page)'
    headers = ['deviceId', 'zdid', 'model', 'osType', 'osVersion', 'updatedDate', 'deviceHash']
    human_readable = tableToMarkdown(name=f"Last updated devices{table_name}:", t=devices_data, headers=headers,
                                     removeNull=True)
    entry_context = {f'Zimperium.Devices(val.deviceId === obj.deviceId)': devices_data}

    return human_readable, entry_context, devices


def app_classification_get(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Retrieve application classification.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    app_hash = str(args.get('app_hash', ''))
    app_name = str(args.get('app_name', ''))

    application = client.app_classification_get_request(app_hash, app_name)

    if isinstance(application, dict):  # an app name can have multiple results due to different versions.
        application_data = application.get('content')
    else:  # or it can have only one result, if queried using a hash or if it has only one version.
        application_data = application[0]
    headers = ['objectId', 'hash', 'name', 'version', 'classification', 'score', 'privacyEnum', 'securityEnum']
    human_readable = tableToMarkdown(name=f"Application:", t=application_data, headers=headers, removeNull=True)
    entry_context = {f'Zimperium.Application(val.objectId: === obj.objectId)': application_data}

    return human_readable, entry_context, application


def report_get(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Retrieve a report.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    bundle_id = str(args.get('bundle_id', ''))
    itunes_id = str(args.get('itunes_id', ''))
    app_hash = str(args.get('app_hash', ''))
    platform = str(args.get('platform', 'ios'))

    report = client.report_get_request(bundle_id, itunes_id, app_hash, platform).get('report', {})
    report_data = report.get('report')
    if not report_data:
        return 'A report was not found.', {}, {}

    # deleting analysis metadata to not load the context
    app_analysis = report_data.get('app_analysis')
    if app_analysis and app_analysis.get('application_type') == 'Android':
        analysis = app_analysis.get('analysis')
        if analysis:
            report_data['app_analysis']['analysis'] = list(analysis.keys())

    app_md5 = report.get('md5') if 'md5' in report else report_data.get('app_analysis', {}).get('md5_hash')
    if app_md5:
        report_data.update({'md5': app_md5})
    human_readable = tableToMarkdown(name=f"Report:", t=report_data, removeNull=True)
    entry_context = {f'Zimperium.Reports(val.app_md5: === obj.app_md5)': report_data}

    return human_readable, entry_context, report


def app_upload_for_analysis(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Upload an application for analysis.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    entry_id = str(args.get('entry_id', ''))

    upload = client.app_upload_for_analysis_request(entry_id)

    # headers = ['objectId', 'hash', 'name', 'classification', 'score', 'privacyEnum', 'SecurityEnum']
    human_readable = tableToMarkdown(name=f"Upload:", t=upload, removeNull=True)
    entry_context = {f'Zimperium.Analysis(val.objectId: === obj.objectId)': upload}

    return human_readable, entry_context, upload


def events_search(client: Client, args: Dict) -> Tuple[str, Dict, Dict]:
    """Search events.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    query = str(args.get('query', 'eventId==*'))
    size = str(args.get('size', '10'))
    page = str(args.get('page', '0'))
    verbose = str(args.get('verbose')) == 'true'

    events = client.events_search_request(query, size, page, verbose)
    events_data = events.get('content')

    if not verbose:
        for event_data in events_data:
            event_data.pop('eventDetail', None)

    table_name = ''
    if not events.get('last'):
        table_name = f' (To get the next events, run the command with the next page)'
    headers = ['eventId', 'eventName', 'eventState', 'incidentSummary', 'severity', 'persistedTime']
    human_readable = tableToMarkdown(name=f"Users{table_name}:", t=events_data, headers=headers, removeNull=True)
    entry_context = {f'Zimperium.Events(val.eventId === obj.eventId)': events_data}

    return human_readable, entry_context, events


def fetch_incidents(client: Client, last_run: dict, first_fetch_time: str, max_fetch: str = '50'):
    """
    This function will execute each interval (default is 1 minute).

    Args:
        client (Client): Zimperium client
        last_run (dateparser.time): The greatest incident created_time we fetched from last fetch
        first_fetch_time (dateparser.time): If last_run is None then fetch all incidents since first_fetch_time
        max_fetch: max events to fetch

    Returns:
        next_run: This will be last_run in the next fetch-incidents
        incidents: Incidents that will be created in Demisto
    """
    timestamp_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    if not last_run:  # if first time fetching
        next_run = {
            'time': parse_date_range(first_fetch_time, date_format=timestamp_format)[0],
            'last_event_ids': []
        }
    else:
        next_run = last_run

    incidents = []

    events = client.events_search_request(query=f"persistedTime=gt={next_run.get('time')}",
                                          size=max_fetch, page='0', verbose=False)
    events_data = events.get('content')

    if events_data:
        last_event_ids = last_run.get('last_event_ids', [])
        for event_data in events_data:
            event_data.pop('eventDetail', None)  # deleting eventDetail to not load the context
            event_id = event_data.get('eventId')
            if event_id not in last_event_ids:  # check that event was not fetched in the last fetch
                event_created_time = parse(event_data.get('persistedTime'))
                incident = {
                    'name': event_data.get('incidentSummary'),
                    'occurred': event_created_time.strftime(timestamp_format),
                    'severity': event_severity_to_dbot_score(event_data.get('severity')),
                    'rawJSON': json.dumps(event_data)
                }
                incidents.extend([incident])
                last_event_ids.extend([event_id])

                next_run = {
                    'time': event_created_time.strftime(timestamp_format),
                    'last_event_ids': json.dumps(last_event_ids)  # save the event IDs from the last fetch
                }

    demisto.debug(f'Zimperium last fetch data: {str(next_run)}')
    return next_run, incidents


def event_severity_to_dbot_score(severity_str: str):
    """Converts an severity string to DBot score representation
        alert severity. Can be one of:
        Low    ->  1
        Medium ->  2
        High   ->  3

    Args:
        severity_str: String representation of severity.

    Returns:
        Dbot representation of severity
    """
    severity = severity_str.lower()
    if severity == 'low':
        return 1
    if severity == 'important':
        return 2
    if severity == 'critical':
        return 3
    demisto.info(f'Zimperium incident severity: {severity} is not known. Setting as unknown(DBotScore of 0).')
    return 0


def main():
    """
        PARSE AND VALIDATE INTEGRATION PARAMS
    """
    params = demisto.params()
    api_key = params.get('api_key')
    base_url = urljoin(params.get('url'), '/api/v1/')
    verify = not params.get('insecure', False)

    # fetch params
    first_fetch_time = params.get('fetch_time', '3 days').strip()
    max_fetch = min('50', params.get('max_fetch', '50'))

    command = demisto.command()
    LOG(f'Command being called is {demisto.command()}')
    try:
        client = Client(base_url=base_url, api_key=api_key, verify=verify)
        commands: Dict[str, Callable[[Client, Dict[str, str]], Tuple[str, Dict[Any, Any], Dict[Any, Any]]]] = {
            'test-module': test_module,
            'zimperium-events-search': events_search,
            'zimperium-users-search': users_search,
            'zimperium-user-get-by-id': user_get_by_id,
            'zimperium-devices-search': devices_search,
            'zimperium-device-get-by-id': device_get_by_id,
            'zimperium-devices-get-last-updated': devices_get_last_updated,
            'zimperium-app-classification-get': app_classification_get,
            'zimperium-report-get': report_get,
            'zimperium-app-upload-for-analysis': app_upload_for_analysis,
        }
        if demisto.command() == 'fetch-incidents':
            next_run, incidents = fetch_incidents(
                client=client,
                last_run=demisto.getLastRun(),
                first_fetch_time=first_fetch_time,
                max_fetch=max_fetch,
            )
            demisto.setLastRun(next_run)
            demisto.incidents(incidents)
        elif command in commands:
            return_outputs(*commands[command](client, demisto.args()))
        else:
            raise NotImplementedError(f'Command "{command}" is not implemented.')

    except Exception as err:
        return_error(str(err), err)


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()