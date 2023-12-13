"""
Install this script on Romi's Raspberry Pi, to maintain tunnels for Limelight camera.
Three steps to install:
  1. modify the constants below, if needed (for example, if team number is not 7.14)
  2. copy this script to /home/pi/limelight_proxy.py on Pi and test by running `python3 /home/pi/limelight_proxy.py`
  3. if no errors in test, add line `/usr/bin/python3 /home/pi/limelight_proxy.py &` right before `exit 0` in your Pi's /etc/rc.local
"""

import atexit
import traceback
import subprocess
import socket
import logging
import glob

# important!!! make sure this matches the settings in the camera
LIMELIGHT_ADDRESS = "10.7.14.11"

# Limelight manual says to forward these ports (but 5802, 5803, 5804 are not used in Limelight 2)
LIMELIGHT_PORTS = ["5800", "5801", "5802", "5803", "5804", "5805", "5806", "5807"]

# Limelight wants to connect to NetworkTables server on port 1735 (and will switch to 5810 in future)
NT_TUNNEL_PORT = "1735"

# on which port this Pi will listen for incoming registration from WPI Robot Simulator?
# (make sure this matches the Java code of the robot!)
WPI_NT_REGISTRATION_PORT = "5899"

# we expect socat to be installed here on Pi
SOCAT = glob.glob("/usr/bin/socat") or glob.glob("/home/pi/socat")
assert SOCAT, "cannot find /usr/bin/socat or /home/pi/socat"
SOCAT = SOCAT[0]


tunnels = []

def main():
    # 1. check if socat is working
    socat_missing = subprocess.call([SOCAT, "-V"])
    assert not socat_missing, "socat is not found or not allowed to execute ({}), try running this:\n\nsudo apt-get install socat".format(socat_missing)

    # 2. setup permanent tunnels for connections into Limelight
    atexit.register(stop_tunnels)
    for port in LIMELIGHT_PORTS:
        start_tunnel(port, "{}:{}".format(LIMELIGHT_ADDRESS, port))

    # 3. wait for WPI simulator to say "I am here at this address", then start the network tables tunnel to simulator
    nt_tunnel = None
    try:
        registration = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        registration.bind(("0.0.0.0", int(WPI_NT_REGISTRATION_PORT)))
        registration.listen(5)
        while True:
            connection, (ip, port) = registration.accept()
            with connection:
                if nt_tunnel is not None:
                    logging.info("stopping the previous NT tunnel...")
                    stop_one_tunnel(nt_tunnel)
                nt_tunnel = register_nt_server(ip, connection)
    finally:
        registration.close()

def start_tunnel(listen_on, connect_to):
    command = [SOCAT, "tcp-listen:{},fork,reuseaddr".format(listen_on), "tcp:{}".format(connect_to)]
    logging.info("connections to port {} will be forwarded to {}:\n\t{}".format(
        listen_on, connect_to, " ".join(command)))
    p = subprocess.Popen(command)
    tunnels.append(p)
    return p

def stop_one_tunnel(p):
    tunnels.remove(p)
    p.terminate()
    p.wait()

def stop_tunnels():
    logging.info("stopping tunnels")
    for t in tunnels:
        t.terminate()
    for t in tunnels:
        t.wait()
    logging.info("tunnels stopped")

def register_nt_server(ip, connection):
    logging.info("registering NetworkTables server located at {}".format(ip))
    nt_tunnel = None

    # start the new NT tunnel
    try:
        response = b"0"
        nt_tunnel = start_tunnel(NT_TUNNEL_PORT, "{}:{}".format(ip, NT_TUNNEL_PORT))
    except:
        msg = str("!: {}".format(traceback.format_stack()))
        logging.error("Failed to start the network tables tunnel" + msg)
        response = bytes(msg.encode("utf-8"))

    # respond to say if this was a success or not ("0" will mean "success")
    try:
        connection.sendall(response)
    except:
        pass
    return nt_tunnel

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    main()
