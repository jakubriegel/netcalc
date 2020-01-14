# netcalc
A connective binary protocol for sending calculations with sample server-client app. This is a project for our studies.

## datagram structure
Each datagram size is 248 bits (31 bytes)

data | bits | type
-----|------|-----
operation | 2 | uint
number a | 64 | IEEE-754
number b | 64 | IEEE-754
status | 2 | uint
session id | 16 | uint
mode | 3 | uint
result | 64 | IEEE-754
result id | 32 | uint
last flag | 1 | boolean

## build
 > It is recommended to build and run this script in virtual environment. Instructions for configuring it can be found in official Python [documentation](https://docs.python-guide.org/dev/virtualenvs/#lower-level-virtualenv).

To get all dependencies type: `pip install -r requirements.txt`.

After making changes in dependencies remember to do: `pip freeze > requirements.txt`


## run
To run as server type: `python netcalc_server.py server_ip server_port` <br>
To run as client type: `python netcalc_client.py server_ip server_port`

If flags `server_ip` ale `server_port` are not supplied, the values used are respectively `127.0.0.1`(localhost) and `1500`
