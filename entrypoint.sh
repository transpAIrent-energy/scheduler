echo "Starting AIT scheduler webservice..."
exec fastapi run scheduler-webservice.py --port 8000 --proxy-headers
