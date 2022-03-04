#!/usr/bin/env python3

__copyright__ = 'Copyright (c) 2022, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import json
from traceback import print_exc

import jsonavu
from flask import Blueprint, g, jsonify, request
from opensearchpy import OpenSearch

from errors import UnauthorizedAPIAccessError

api_index_bp = Blueprint('api_index_bp', __name__)
host = 'localhost'
port = 9200


@api_index_bp.route('/query', methods=['POST'])
def _query():
    data = json.loads(request.form['data'])
    name = data['name']
    value = data['value']
    if 'from' in data:
        start = data['from']
        size = data['size']
    else:
        start = 0
        size = 500
    if 'sort' in data:
        sort = data['sort']
    else:
        sort = None
    if 'reverse' in data:
        reverse = data['reverse']
    else:
        reverse = False

    res = query(name, value, start=start, size=size, sort=sort, reverse=reverse)
    code = 200

    if res['status'] != 'ok':
        code = 400

    response = jsonify(res)
    response.status_code = code
    return response


def query(name, value, start=0, size=500, sort=None, reverse=False):
    client = OpenSearch(
        hosts=[{
            'host': host,
            'port': port
        }],
        http_compress=True
    )

    query = {
        'from': start,
        'size': size,
        'track_total_hits': True,
        'query': {
            'nested': {
                'path': 'metadataEntries',
                'query': {
                    'bool': {
                        'must': [
                            {
                                'term': {
                                    'metadataEntries.attribute.raw': name
                                }
                            }, {
                                'term': {
                                    'metadataEntries.unit.raw': 'FlatIndex'
                                }
                            }, {
                                'match': {
                                    'metadataEntries.value': value
                                }
                            }
                        ]
                    }
                }
            }
        }
    }

    if sort is not None:
        if reverse:
            order = 'desc'
        else:
            order = 'asc'
        query['sort'] = [
            {
                'metadataEntries.value.raw': {
                    'order': order,
                    'nested': {
                        'path': 'metadataEntries',
                        'filter': {
                            'term': {
                                'metadataEntries.attribute.raw': sort
                            }
                        }
                    }
                }
            }
        ]

    response = client.search(body=query, index='yoda')
    matches = []
    for hit in response['hits']['hits']:
        src = hit['_source']
        match = {
            'fileName': src['fileName'],
            'parentPath': src['parentPath']
        }
        attributes = []
        for avu in src['metadataEntries']:
            if avu['unit'] == 'FlatIndex':
                attributes.append({
                    'name': avu['attribute'],
                    'value': avu['value']
                })
        match['attributes'] = attributes
        matches.append(match)
    result = {
        'query': {
            'name': name,
            'value': value,
            'from': start,
            'size': size
        },
        'matches': matches,
        'total_matches': response['hits']['total']['value'],
        'status': 'ok'
    }
    if sort is not None:
        result['query']['sort'] = sort
        result['query']['reverse'] = reverse
    return result


@api_index_bp.route('/metadata', methods=['POST'])
def _metadata():
    data = json.loads(request.form['data'])
    uuid = data['uuid']

    # Query data package on UUID.
    res = metadata(uuid)
    code = 200

    if res['status'] != 'ok':
        code = 400

    if res['total_matches'] == 1:
        avus = res['matches'][0]
        metadata_json = jsonavu.avu2json(avus['attributes'], 'usr')
    else:
        code = 400

    response = jsonify({"metadata": metadata_json})
    response.status_code = code

    return response


def metadata(value):
    client = OpenSearch(
        hosts=[{
            'host': host,
            'port': port
        }],
        http_compress=True
    )

    query = {
        'from': 0,
        'size': 1,
        'track_total_hits': True,
        'query': {
            'nested': {
                'path': 'metadataEntries',
                'query': {
                    'bool': {
                        'must': [
                            {
                                'term': {
                                    'metadataEntries.attribute.raw': 'org_data_package_reference'
                                }
                            }, {
                                'match': {
                                    'metadataEntries.value': value
                                }
                            }
                        ]
                    }
                }
            }
        }
    }

    response = client.search(body=query, index='yoda')
    matches = []
    for hit in response['hits']['hits']:
        attributes = []
        match = {}
        src = hit['_source']
        for avu in src['metadataEntries']:
            if avu['unit'].startswith('usr_'):
                attributes.append({
                    'a': avu['attribute'],
                    'v': avu['value'],
                    'u': avu['unit'],
                })
        match['attributes'] = attributes
        matches.append(match)
    result = {
        'query': {
            'value': value,
        },
        'matches': matches,
        'total_matches': response['hits']['total']['value'],
        'status': 'ok'
    }

    return result


def authenticated():
    return g.get('user') is not None and g.get('irods') is not None


@api_index_bp.errorhandler(Exception)
def api_index_error_handler(error):
    print_exc()
    print('API Error: {}'.format(error))
    status = "internal_error"
    status_info = "Something went wrong"
    data = {}
    code = 500

    if type(error) == UnauthorizedAPIAccessError:
        status_info = "Not authorized to use the API"

    return jsonify({
        "status": status,
        "status_info": status_info,
        "data": data
    }), code
