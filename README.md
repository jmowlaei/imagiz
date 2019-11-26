# imagiz
Fast and none blocking live video streaming over network with OpenCV and ZMQ.


# Install
```
pip3 install imagiz
```

# Client

```
import imagiz
import cv2


client=imagiz.Client("cc1",server_ip="localhost")
vid=cv2.VideoCapture(0)
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

while True:
    r,frame=vid.read()
    if r:
        r, image = cv2.imencode('.jpg', frame, encode_param)
        client.send(image)
    else:
        break

```

# Server
```
import imagiz
import cv2

server=imagiz.Server()
while True:
    message=server.recive()
    frame=cv2.imdecode(message.image,1)
    cv2.imshow("",frame)
    cv2.waitKey(1)
```


# Client Options
| Name | Description |
| --- | --- |
| `client_name` | Name of client |
| `server_ip` | Ip of server default value is localhost  |
| `server_port` | Port of server default value is 5555 |
| `request_timeout` | how many milliseconds wait to resend image again |
| `request_retries` | how many time retries to send an image before client exit  |
| `generate_image_id` | image_id is unique and ordered id that you can use for save data on disk or db also it is show time of image sended by client  |

# Server Options
| Name | Description |
| --- | --- |
| `Port` | Port of server |
| `listener` | Number of listening threads.default value is 10 |

# Message Class
| Name | Description |
| --- | --- |
| `image` | Byte of image |
| `client_name` | Name of client |
| `image_id` | If disable generate_image_id it will be 0  |
