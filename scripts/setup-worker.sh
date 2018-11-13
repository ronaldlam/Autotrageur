# This is a selection of useful commands to be used during server setup.
# DO NOT RUN HAPHAZARDLY: Inteded for reference use only.

# Create autotrageur group and set /home/rnd with correct permissions.
sudo groupadd autotrageur
sudo usermod -a -G autotrageur ronaldctlam
sudo usermod -a -G autotrageur drewngui
sudo chgrp -R autotrageur /home/rnd
sudo chmod g+w /home/rnd
newgrp autotrageur

# Set up SSH access.
eval `ssh-agent -s`
ssh-add <private-key-path>

# Install mariadb 10.3
# https://downloads.mariadb.org/mariadb/repositories/#mirror=globotech&distro=Ubuntu&distro_release=bionic--ubuntu_bionic&version=10.3
# https://stackoverflow.com/questions/22949654/mysql-config-not-found-when-installing-mysqldb-python-interface-for-mariadb-10-u
# https://stackoverflow.com/questions/25979525/cannot-find-lssl-cannot-find-lcrypto-when-installing-mysql-python-using-mar
sudo apt-get install software-properties-common
sudo apt-key adv --recv-keys --keyserver hkp://keyserver.ubuntu.com:80 0xF1656F24C74CD1D8
sudo add-apt-repository 'deb [arch=amd64,arm64,ppc64el] http://mariadb.mirror.globo.tech/repo/10.3/ubuntu bionic main'
sudo apt update
sudo apt install mariadb-server
sudo apt install libmariadb-dev-compat
sudo apt install libssl-dev

# For db:
# Yes you need the sudo.
sudo mysql -u root -p

# Run files in mysql interactive client:
source dml_fcf.sql
source dml_fcf_staging.sql

# Create the user
CREATE USER 'worker1'@'localhost' IDENTIFIED BY '<password>';
GRANT ALL privileges ON `fcf_trade_history_staging`.* TO 'worker1'@'localhost';
GRANT ALL privileges ON `fcf_trade_history`.* TO 'worker1'@'localhost';
GRANT ALL privileges ON `minute`.* TO 'worker1'@'localhost';

# The minimum running bot:
cd /home/rnd
mkdir Autotrageur
cd Autotrageur
python3 -m venv venv
source venv/bin/activate
pip install git+ssh://git@github.com/ronaldlam/Autotrageur.git@<branch/release>
post_install
mv configs/twilio/twilio_sample.yaml configs/twilio/twilio.yaml
touch encrypted-blank-secret.txt

# Final step before running is to copy valid .env file into project directory.

run_autotrageur encrypted-blank-secret.txt configs/staging/dryrun/kraken_bithumb_btc.yaml configs/staging/db_staging.yaml

# Notable additional steps necessary for production
# - Overwrite configs/twilio/twilio.yaml with valid numbers
# - API keys
