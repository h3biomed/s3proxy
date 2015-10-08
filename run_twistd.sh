export AWS_PROFILE=h3pipelines
export AWS_DEFAULT_PROFILE=h3pipelines
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
twistd web --port 8080 --wsgi s3proxy.app.app
