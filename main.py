import json
import os

import asyncio
from botocore.exceptions import ParamValidationError
import boto3
import dateparser
import datetime
from sanic import Sanic, response
from sanic.exceptions import InvalidUsage

app = Sanic()
cloudwatch = boto3.client('logs')
DEBUG = os.environ.get('DEBUG') in {'1', 'true', 'TRUE'}
POLL_INTERVAL = float(os.environ.get('POLL_INTERVAL', 3.0))
TIMEOUT = float(os.environ.get('TIMEOUT', 60.0))


@app.route('/')
async def health(request):
    return response.json({'status': 'ok!'})


@app.route('/query', methods=['GET', 'POST'])
async def query(request):
    query = request.json or json.loads(request.raw_args['q'])
    for timeKey in ['startTime', 'endTime']:
        if isinstance(query.get(timeKey), str):
            query[timeKey] = int(dateparser.parse(query[timeKey]).timestamp())
    if not query.get('endTime'):
        query['endTime'] = int(datetime.datetime.now().timestamp())

    try:
        query_id = cloudwatch.start_query(**query)['queryId']
    except ParamValidationError as e:
        raise InvalidUsage(f'Error: {e}')
    except Exception as e:
        raise e

    elapsed = 0
    while True:
        result = cloudwatch.get_query_results(queryId=query_id)
        if result['status'] == 'Complete':
            results = result['results']
            cols = []
            rows = []
            for i, row in enumerate(results):
                if i == 0:  # get columns from 1st row
                    cols = [{
                        'name': col['field'],
                        'type': 'datetime' if col['field'] == '@timestamp' else 'string',
                        'friendly_name': col['field']
                    } for col in row if col['field'] != '@ptr']
                rows.append({col['field']: col['value'] for col in row if col['field'] != '@ptr'})
            return response.json({'columns': cols, 'rows': rows})
        if elapsed > TIMEOUT:
            raise Exception('timeout')
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=DEBUG)
