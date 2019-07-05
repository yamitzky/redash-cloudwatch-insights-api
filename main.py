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
            rows = []
            field_orders = {}
            for row in results:
                record = {}
                rows.append(record)
                for order, col in enumerate(row):
                    if col['field'] == '@ptr':
                        continue
                    field = col['field']
                    record[field] = col['value']
                    # true order is largest one
                    field_orders[field] = max(field_orders.get(field, -1), order)
            fields = sorted(field_orders, key=lambda f: field_orders[f])
            cols = [{
                'name': f,
                'type': 'datetime' if f == '@timestamp' else 'string',
                'friendly_name': f
            } for f in fields]
            return response.json({'columns': cols, 'rows': rows})
        if elapsed > TIMEOUT:
            raise Exception('timeout')
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=DEBUG)
