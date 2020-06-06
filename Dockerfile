FROM python:latest
WORKDIR /src
COPY . /src
RUN pip3 install flask pymongo bcrypt bigchaindb_driver
EXPOSE 5000