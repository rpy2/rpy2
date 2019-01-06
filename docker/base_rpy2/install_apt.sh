apt-get update -qq
apt-get install -y \
        apt-utils \
        apt-transport-https \
	dirmngr \
        gnupg \
	libcurl4-openssl-dev \
	libnlopt-dev \
        lsb-release
echo "deb ${CRAN_MIRROR}/bin/linux/ubuntu $(lsb_release -c -s)${CRAN_MIRROR_TAG}/" \
     >> /etc/apt/sources.list.d/added_repos.list
apt-key adv --no-tty --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
apt-get update -qq
apt-get install -y \
        aptdaemon \
        ed \
        git \
	mercurial \
	libcairo-dev \
	libedit-dev \
	libxml2-dev \
	python3 \
	python3-pip \
	python3-venv \
	r-base \
	r-base-dev \
	sudo \
	wget
rm -rf /var/lib/apt/lists/*
