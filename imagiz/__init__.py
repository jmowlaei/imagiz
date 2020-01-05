import datetime
import pickle
import zmq
import threading
import queue
import sys
import datetime
import socket
import struct
import time


class message():
    image: None
    client_name: None
    image_id = 0

    def __init__(self, image, client_name, generate_image_id=True):
        self.image = image
        self.client_name = client_name
        if generate_image_id:
            self.image_id = int(
                datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"))


class Server():
    port = 0
    listener = 0
    qu = queue.Queue()

    def __init__(self, port=5555, listener=10):
        self.port = port
        self.listener = listener
        self.qu = queue.Queue()
        thread = threading.Thread(target=self.start)
        thread.start()

    def __del__(self):
        print('Destructor called.')

    def worker_routine(self, worker_url, context: zmq.Context = None):
        context = context or zmq.Context.instance()
        socket = context.socket(zmq.REP)
        socket.connect(worker_url)

        while True:
            message = socket.recv_pyobj()
            socket.send_string("ok")
            self.qu.put(message)

    def receive(self):
        while True:
            message = self.qu.get()
            return message

    def start(self):
        url_worker = "inproc://workers"
        url_client = "tcp://*:"+str(self.port)

        # Prepare our context and sockets
        context = zmq.Context.instance()

        # Socket to talk to clients
        clients = context.socket(zmq.ROUTER)
        clients.bind(url_client)

        # Socket to talk to workers
        workers = context.socket(zmq.DEALER)
        workers.bind(url_worker)

        # Launch pool of worker threads
        for i in range(self.listener):
            thread = threading.Thread(
                target=self.worker_routine, args=(url_worker,))
            thread.start()

        zmq.proxy(clients, workers)


class Client():
    server_ip = ""
    server_port = 0
    request_timeout = 0
    request_retries = 0
    client_name = ""
    context = None
    client = None
    server_endpoint = ""
    poll = None
    generate_image_id = False

    def __init__(self, client_name="", server_ip="localhost", server_port=5555, request_timeout=3000, request_retries=3, generate_image_id=True):
        self.server_ip = server_ip
        self.server_port = server_port
        self.request_retries = request_retries
        self.request_timeout = request_timeout
        self.client_name = client_name
        self.server_endpoint = "tcp://%s:%d" % (server_ip, server_port)
        self.context = zmq.Context(1)
        self.client = self.context.socket(zmq.REQ)
        self.client.connect(self.server_endpoint)
        self.poll = zmq.Poller()
        self.poll.register(self.client, zmq.POLLIN)
        self.generate_image_id = generate_image_id

    def __del__(self):
        self.poll.unregister(self.client)
        self.context.term()

    def send(self, image):
        retries_left = self.request_retries
        new_message = message(image, self.client_name, self.generate_image_id)
        # pickle_message = pickle.dumps(new_message)
        self.client.send_pyobj(new_message)
        expect_reply = True
        while expect_reply:
            socks = dict(self.poll.poll(self.request_timeout))
            if socks.get(self.client) == zmq.POLLIN:
                reply = self.client.recv()
                if not reply:
                    break
                else:
                    # print("I: Server replied OK (%s)" % reply,flush=True)
                    retries_left = self.request_retries
                    expect_reply = False

            else:

                print("W: No response from server, retrying…", flush=True)
                # Socket is confused. Close and remove it.
                self.client.setsockopt(zmq.LINGER, 0)
                self.client.close()
                self.poll.unregister(self.client)
                retries_left -= 1
                if retries_left == 0:
                    print("E: Server seems to be offline, abandoning", flush=True)
                    raise "Server seems to be offline, abandoning"
                print("I: Reconnecting and resending ", flush=True)
                # Create new connection
                self.client = self.context.socket(zmq.REQ)
                self.client.connect(self.server_endpoint)
                self.poll.register(self.client, zmq.POLLIN)
                self.client.send_pyobj(new_message)

class Client_Thread(threading.Thread):
    qu = queue.Queue()
    client_address = ("0.0.0.0", 0)
    client_socket = None

    def __init__(self, client_address, client_socket,qu):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        self.qu = qu
        print("New connection added: ", self.client_address)

    def run(self):
        print("Connection from : ", self.client_address)
        while True:
            data = b""
            payload_size = struct.calcsize(">L")
            while len(data) < payload_size:
                data += self.client_socket.recv(4096)
                if data == b'':
                    break
            if data == b'':
                break
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]

            while len(data) < msg_size:
                data += self.client_socket.recv(4096)

            frame_data = data[:msg_size]
            data = data[msg_size:]
            message = pickle.loads(frame_data)

            self.qu.put(message)
            self.client_socket.sendall(b"ok")

        print("Client at ", self.client_address, " disconnected...")

class TCP_Server():
    port = 0
    listener = 0
    ip = "0.0.0.0"
    qu = queue.Queue()

    def __init__(self, port=5555, ip="0.0.0.0"):

        self.port = port
        self.ip = ip

    def __start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.ip, self.port))
        print("Server started")
        print("Waiting for client request..")
        while True:
            server.listen()
            client_socket, client_address = server.accept()
            new_thread = Client_Thread(client_address, client_socket,self.qu)
            new_thread.start()


    def start(self):
        thread = threading.Thread(target=self.__start)
        thread.start()



    def receive(self):
        while True:
            message = self.qu.get()
            return message




class TCP_Client():
    server_ip = ""
    server_port = 0
    request_timeout = 0
    request_retries = 0
    time_between_retries = 0
    client_name = ""
    generate_image_id = False
    socket = None

    def __init__(self, client_name="", server_ip="localhost", server_port=5555, request_timeout=3000, request_retries=3, time_between_retries=4000, generate_image_id=True):
        self.server_ip = server_ip
        self.server_port = server_port
        self.request_retries = request_retries
        self.request_timeout = request_timeout
        self.client_name = client_name
        self.generate_image_id = generate_image_id
        self.time_between_retries = time_between_retries/1000
        self.socket=self.__connect()

    def __connect(self):
        retries_left = self.request_retries
        while True:
            try:
                print("I: Reconnecting  ", flush=True)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.request_timeout/1000)
                sock.connect((self.server_ip, self.server_port))
                return sock

            except Exception as ex:
                print("W: No response from server, retrying…", flush=True)
                print(ex)
                retries_left -= 1
                if retries_left == 0:
                    print("E: Server seems to be offline, abandoning", flush=True)
                    raise "Server seems to be offline, abandoning"
                time.sleep(self.time_between_retries)
    def __sending(self,data):
        retries_left = self.request_retries
        size = len(data)
        while True:
            try:
                

                self.socket.sendall(struct.pack(">L", size) +data)
                return True

            except Exception as ex:
                
                print("W: No response from server, retrying…", flush=True)
                print(ex)
                retries_left -= 1
                if retries_left == 0:
                    print("E: Server seems to be offline, abandoning", flush=True)
                    raise "Server seems to be offline, abandoning"
                time.sleep(self.time_between_retries)
    def __del__(self):
        pass

    def send(self, image):
        new_message = message(image, self.client_name, self.generate_image_id)
        data = pickle.dumps(new_message)
        self.__sending(data)           
        try:
            response = str(self.socket.recv(10))
            return response
        except Exception as ex:
            print(ex)
            self.socket=self.__connect()
