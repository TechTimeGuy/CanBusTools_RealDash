"""
picanplayback.py

This program reads a  CAN log file and streams the CAN frames from log
to RealDash.  Assumes the following format in the log  "(1700779116.165776) can0 411#FD143FFFFFFFFFFF"

Usage:
- Start the picanplayback program
$ python3 picanplayback.py <path to log file>

- Start RealDash and create 'RealDash CAN' connection
- Configure connection to IP address and port shown by the picanplayback program
********************
- Addition 12/23
- Altered for CanHat and Pi streaming/ playback by : Blazetamer
- Original file found at RealDash.net GitHub
- Script will ask for log file selection, and
    filter/frame (#) will stream all frames (ie:"2e1#" will only stream 2e1 frames)

"""

import socket
import csv
import time
from tkinter import filedialog

port = 35000 # standard RealDash port


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('192.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def ask_for_log_file():
    # Ask user for the log file path using filedialog
    log_file_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log"), ("All files", "*.*")])
    return log_file_path


def get_next_line(csvfile):
    line = csvfile.readline()
    if not line:
        csvfile.seek(0)
        _ = csvfile.readline()
        line = csvfile.readline()
    return line


def send_next_frame(client, csvfile,frame):
    line = get_next_line(csvfile)
    if line:
            if frame in line:
    
                values = next(csv.reader([line], delimiter = ' ', skipinitialspace=True))
                newvalues = values[2].split('#') # <<This allows reading of Canhat formatted logs/streams
                print("sending:", newvalues[0]+"#", newvalues[1])
                frame_id = int("0x"+newvalues[0],16)
                client.sendall(bytes([0x44, 0x33, 0x22, 0x11]))
                client.sendall(frame_id.to_bytes(4, 'little'))
                splitframe = (" ".join(newvalues[1][i:i + 2] for i in range(0, len(newvalues[1]), 2)))
                frame_data = [int(value, 16) for value in splitframe.split(' ') if value != 'x|']
                frame_data.extend([0] * (8 - len(frame_data)))
                client.sendall(bytes(frame_data))
                time.sleep(0.005)  # comment this line out to run at max speed (0.01-0.005 is near realtime)
              

def main():
    filename = ask_for_log_file()
    # Asking for text input
    frame = input("Please enter filter: (ie: # or 2E1# etc etc )" )
    with open(filename) as csvfile:
        _ = csvfile.readline()
        print(_)
        my_address = get_local_ip()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((my_address, port))   # <<You can manually override "my_address" if needed>>
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.listen(2)
        print("Listening at", server.getsockname())

        try:
            while True:
                client, address = server.accept()
                print("Connected to ", address)
                
                try:
                    while True:
                        send_next_frame(client, csvfile,frame)
                
                except Exception as e:
                    print(e)
                    client.close()
                    csvfile.seek(0)
                    _ = csvfile.readline()
                print("Listening for connection at", server.getsockname())
            
        except (KeyboardInterrupt, Exception):
            server.close()
            

if __name__ == "__main__":
    main()

