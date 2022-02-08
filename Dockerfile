FROM python:3.9.10

WORKDIR /pandwarf

RUN apt update && apt install -y usbutils ffmpeg && pip install pyside2

COPY . ./rfcat
RUN cd rfcat && python setup.py install

CMD [ "bash" ]
