from flask import Flask
from flask import Response
from flask import request
from flask import stream_with_context
from werkzeug.datastructures import Headers
import boto3
from botocore.client import Config
import yaml
import os
import re

BUFFER_SIZE = 8192

app = Flask(__name__)

# load AWS credentials and bucket
config_path = os.path.expanduser('~/.s3proxy')
config = yaml.load(open(config_path, 'r'))
s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

# Load the rewrite rules:
for name, rule in config.get("rewrite_rules", {}).iteritems():
    config["rewrite_rules"][name]["r"] = re.compile(rule["from"])


def apply_rewrite_rules(input_str):
    for name, rule in config.get("rewrite_rules", {}).iteritems():
        input_str = rule["r"].sub(rule["to"], input_str)
        print "applied rule", name
        print "new url", input_str
    return input_str


def get_S3Key(url):
    S3Key = s3.Object(config['bucket_name'], url)
    try:
        size = S3Key.content_length
    except:
        return None
    return S3Key


@app.route('/files/<path:url>', methods=["HEAD"])
def head_file(url):
    url = apply_rewrite_rules(url)
    headers = Headers()
    S3Key = get_S3Key(url)
    try:
        size = S3Key.content_length
    except:
        return Response(None, 404)
    headers.add("Content-Length", size)
    return Response(headers=headers, direct_passthrough=True)


@app.route('/files/<path:url>', methods=["GET"])
def get_file(url):
    url = apply_rewrite_rules(url)
    range_header = request.headers.get('Range', None)
    return_headers = Headers()
    S3Key = get_S3Key(url)
    try:
        size = S3Key.content_length
    except:
        return Response(None, 404)

    if range_header:
        print "%s: %s (size=%d)" % (url, range_header, size)
        start_range_str, end_range_str = range_header.split("=")[1].split("-")
        start_range = int(start_range_str)
        end_range = size - 1 if end_range_str == '' else int(end_range_str)
        get_range = "bytes=%d-%d" % (start_range, end_range)

        return_headers.add('Accept-Ranges', 'bytes')
        return_headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start_range, end_range, size))
        return_headers.add('Content-Length', end_range-start_range+1)
        #return_headers.add('Content-Type', 'application/x-gzip')
        
        return_code = 206
        response = S3Key.get(Range=get_range)
    else:
        print "%s: all data (size=%d)" % (url, size)
        return_code = 200
        response = S3Key.get()

    body = response['Body']

    def stream(S3Key):
        while True:
            data = body.read(BUFFER_SIZE)
            if data:
                yield data
            else:
                raise StopIteration
    return Response(stream_with_context(stream(S3Key)), return_code, headers=return_headers, direct_passthrough=True)

if __name__ == '__main__':
    app.run(debug=True)
