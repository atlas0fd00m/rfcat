FROM python:3.9.10

WORKDIR /pandwarf/rfcat
COPY . .
RUN apt update && apt install -y usbutils ffmpeg && pip install -r requirements.txt
RUN python setup.py install

CMD [ "bash" ]
