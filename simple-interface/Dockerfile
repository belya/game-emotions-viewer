FROM nikolaik/python-nodejs:python3.8-nodejs14

WORKDIR /opt/emotions-dashboard

COPY ./requirements.txt ./ 
RUN pip install --no-cache-dir -r ./requirements.txt

COPY ./start-interface.sh ./

WORKDIR /opt/emotions-dashboard

CMD ./start-interface.sh