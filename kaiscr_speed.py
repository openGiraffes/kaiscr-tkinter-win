#!/usr/bin/python3
import socket
import base64
import json
import sys
import threading
import time
import asyncio
  
from asyncio import Future
from typing import (
    Awaitable,
)


class IOStream():
    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket
        self.socket.setblocking(False)
        self.io_loop = asyncio.get_event_loop()

    def connect(self, address: tuple) -> None:
        future = Future()
        try:
            self.socket.connect(address)
        except BlockingIOError:
            pass

        def _handle_connect():
            self.io_loop.remove_writer(self.socket)
            future.set_result(None)
        self.io_loop.add_writer(self.socket, _handle_connect)
        return future

    def write(self, data: bytes) -> None:
        future = Future()

        def _handle_write():
            self.io_loop.remove_writer(self.socket)
            # 正常流程里，这里是要根据缓冲区大小来陆续send的
            self.socket.sendall(data)
            future.set_result(None)
        self.io_loop.add_writer(self.socket, _handle_write)
        return future

    def read_bytes(self, num_bytes: int) -> Awaitable[bytes]:
        future = Future()

        def _handle_read():
            self.io_loop.remove_reader(self.socket)
            data = self.socket.recv(num_bytes)
            future.set_result(data)
        self.io_loop.add_reader(self.socket, _handle_read)
        return future

    def close(self) -> None:
        if self.socket:
            self.socket.close()
        self.socket = None
        
class TakeScreenshot:
    def __init__(self, host="127.0.0.1", port=6000,delay=0.01):
        self.delay=delay
        self.screenshot_cmd = '{"type":"screenshotToDataURL","to":"%s"}'
        self.listTabs_cmd = '{"to":"root","type":"listTabs"}'
        self.substring_cmd='{"type":"substring","start":%d,"end":%d,"to":"%s"}'
        self.sock = socket.socket()
        self.sock.connect((host, port)) 
        self.buffersize = 1024
        self.callback=None

        buffer = b""
        while not buffer.endswith(b":"):
            buffer += self.sock.recv(1)
        size = int(buffer.replace(b":", b""))
        buffer = b""
        while len(buffer) < size:
            buffer += self.sock.recv(1)
        # Do something with it if you want.

        self.sock.send(self.__with_len(self.listTabs_cmd))
        buffer = b""
        while not buffer.endswith(b":"):
            buffer += self.sock.recv(1)
        size = int(buffer[:-1].decode())
        self.deviceActor = json.loads(self.sock.recv(size))["deviceActor"]        
        self.sendScreenShotCmd = self.__with_len(self.screenshot_cmd % self.deviceActor) 
        self.sockasync = IOStream(self.sock)

    def __with_len(self, command):
        return f'{len(command)}:{command}'.encode()
    
    async def __receive(self, size): 
        buffer = b""
        while len(buffer) < size:
            buffer += await self.sockasync.read_bytes(self.buffersize)
        return buffer
        
    def getMiddle(self,data,startstr,endstr):
        startindex = data.find(startstr)
        endindex = data.rfind(endstr)
        return data[startindex+len(startstr):endindex]
         
    async def screenshotSpeed(self):
        starttime = time.time()
        try:
            self.sockasync.write(self.sendScreenShotCmd)
            buffer = b""
            while not buffer.endswith(b":"):
                buffer += await self.sockasync.read_bytes(1)
            size = int(buffer[:-1])
            buffer = await self.__receive(size) 
            #print(buffer)
            image = json.loads(buffer)["value"] 
            #print(image)
            if type(image) == str:
                return base64.b64decode(image.split(",")[1])
            image_len = image["length"]
            actor = image["actor"] 
            cmd = self.substring_cmd % (0, image_len, actor)
            self.sockasync.write(self.__with_len(cmd))

            buffer = b""
            while not buffer.endswith(b":"):
                buffer += await self.sockasync.read_bytes(1)
            bufcount=int(buffer[:-1])
            
            #print(bufcount)
            buffer = self.__receive(bufcount)
            #print(buffer)
            #print(buffer)
            imgstart = b'"data:image/png;base64,'
            imgend = b'","from":"'
            #image = image['initial'].split(",")[1] 
            image = self.getMiddle(await buffer,imgstart,imgend)
            #image = json.loads(buffer)["substring"].split(",")[1].encode()
            #image += b"=" * (-len(image) % 4)
            return base64.b64decode(image)
        finally:
            print(time.time() - starttime )
     
    def close(self):
        self.sock.close()

if __name__ == "__main__":
    import time
    from argparse import ArgumentParser
    d = "Take screenshot(s) from a KaiOS/FFOS device"
    parser = ArgumentParser(description = d)
    parser.add_argument("--host",
        metavar = "host",
        type = str,
        default = "127.0.0.1",
        help = "The host to connect to")

    parser.add_argument("--port",
        metavar = "port",
        type = int,
        default = 6000,
        help = "The port to connect to")
    parser.add_argument("--prefix",
        metavar = "prefix",
        type = str,
        default = "out",
        help = "The prefix for naming files")
    parser.add_argument("--count",
        metavar = "count",
        type = int,
        default = 1,
        help = "How many times should I take screenshot? 0 does nothing and negative values take screenshot forever")

    args = parser.parse_args()
    if args.count == 0:
        sys.exit(0)
    
    takeScreenshot = TakeScreenshot(args.host, args.port) 
    print(takeScreenshot)
 
    async def main():  #封装多任务的入口函数
        while(1):
            img = await takeScreenshot.screenshotSpeed() 
            
    loop = asyncio.get_event_loop()               
    results = loop.run_until_complete(main())
     
    loop.close()     

