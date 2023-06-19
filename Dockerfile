FROM docker-pull.rwasp.intra.rakuten-it.com/pitari/py2-flask-ghp-restful-api:v2.1.0

COPY ./ /flask-demo-api
WORKDIR /flask-demo-api
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/rh/python27/root/usr/lib64:/opt/rh/rh-nodejs8/root/usr/lib64:/opt/rh/httpd24/root/usr/lib64
USER root
RUN pip install --proxy=stb-dev-proxy.db.rakuten.co.jp:9501 --upgrade pip && pip --proxy=stb-dev-proxy.db.rakuten.co.jp:9501 install -r requirements.txt
EXPOSE 5000
ENTRYPOINT python manage.py runserver --host 0.0.0.0 --port 5000