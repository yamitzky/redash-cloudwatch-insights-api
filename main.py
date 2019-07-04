import json
import os

import asyncio
from botocore.exceptions import ParamValidationError
import boto3
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
    elapsed = 0
    query = request.json or json.loads(request.raw_args['q'])
    try:
        query_id = cloudwatch.start_query(**query)['queryId']
    except ParamValidationError as e:
        raise InvalidUsage(f'Error: {e}')
    except Exception as e:
        raise e
    while True:
        result = cloudwatch.get_query_results(queryId=query_id)
        if result['status'] == 'Complete':
            results = result['results']
            if results:
                cols = [{
                    'name': col['field'],
                    'type': 'datetime' if col['field'] == '@timestamp' else 'string',
                    'friendly_name': col['field']
                } for col in results[0]]
                rows = [{col['field']: col['value'] for col in row} for row in results]
                return response.json({'columns': cols, 'rows': rows})
            else:
                return response.json({'columns': [], 'rows': []})
        if elapsed > TIMEOUT:
            raise Exception('timeout')
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=DEBUG)
