sudo apt-get install postgresql postgresql-contrib
echo
sudo echo "Enter the root password for postgres"
echo
echo "\password postgres" | sudo -u postgres psql postgres
sudo -u postgres createuser --superuser elsterdev
sudo -u postgres psql -c "alter user elsterdev password 'elsterdev123'" 
