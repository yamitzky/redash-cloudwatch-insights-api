# cloudwatch-insights-api
CloudWatch Logs Insights API for [Redash](https://github.com/getredash/redash)

## Motivation

[Currently, Redash does not support](https://discuss.redash.io/t/support-for-amazon-cloudwatch-logs-insight/2895).

This API is CloudWatch Logs Insights wrapper and can be used as [Redash's URL data source](https://redash.io/help/data-sources/querying/urls/).

## TODO

Try to contribute as official CloudWatch Logs Insights data source.

## Setup

```
pipenv install
python main.py
```

Or,

```
docker run -it --rm yamitzky/redash-cloudwatch-insights-api
```

## Setup for Redash

First, deploy this API.

Then, create a [URL data source](https://redash.io/help/data-sources/querying/urls) with `https://the-deployed-api-server/query?q=`.
