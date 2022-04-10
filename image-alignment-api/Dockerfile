FROM python:3.8
RUN mkdir /usr/src/app/
COPY . /usr/src/app/
WORKDIR /usr/src/app/

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

EXPOSE 5000
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
