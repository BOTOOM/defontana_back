FROM python:3.9

RUN apt update && apt upgrade -y && apt install unixodbc-dev -y

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add 
RUN curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get -y install msodbcsql17
RUN apt-get -y install unixodbc-dev
COPY . /home/app


WORKDIR /home/app
RUN pip install --upgrade --no-cache-dir -r requirements.txt

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload","--debugger"]
