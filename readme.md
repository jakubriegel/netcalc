# netcalc

## build
 > It is recommended to build and run this script in virtual environment. Instructions for configuring it can be found in official Python [documentation](https://docs.python-guide.org/dev/virtualenvs/#lower-level-virtualenv).

To get all dependencies type: `pip install -r requirements.txt`.

After making changes in dependencies remember to do: `pip freeze > requirements.txt`


## run
To run as server type: `python netcalc_server.py server_ip server_port` <br>
To run as client type: `python netcalc_client.py server_ip server_port`

If flags `server_ip` ale `server_port` are not supplied, the values used are respectively `127.0.0.1`(localhost) and `1500`
