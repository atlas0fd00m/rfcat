FROM python:3.9.10

WORKDIR /pandwarf

COPY . ./rfcat

RUN apt update && apt install -y usbutils

RUN cd rfcat && python setup.py install

CMD [ "bash" ]
