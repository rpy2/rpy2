python3 -m pip --no-cache-dir install pip --upgrade
python3 -m pip --no-cache-dir install setuptools --upgrade
python3 -m pip --no-cache-dir install wheel --upgrade
python3 -m pip --no-cache-dir install \
	jinja2 \
	numpy \
	pandas \
	pytest \
	sphinx \
	tzlocal
rm -rf /root/.cache
