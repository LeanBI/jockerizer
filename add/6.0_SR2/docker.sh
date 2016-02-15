#!/usr/bin/env bash

BASEDIR=$(dirname $0)

function stop { 
	echo "stopping jedox"
	bash /etc/init.d/jedox_olap stop
	bash /etc/init.d/jedox_core stop
	bash /tomcat/jedox_tomcat.sh stop
	bash /etc/init.d/httpd stop
	exit 
 } 

trap stop SIGTERM SIGHUP SIGINT SIGQUIT
 
echo "starting jedox"
ulimit -S unlimited -c unlimited
echo "starting olap"
bash /etc/init.d/jedox_olap start
echo "starting core"
bash /etc/init.d/jedox_core start
echo "starting tomcat"
bash /tomcat/jedox_tomcat.sh start
echo "starting apache"
bash /etc/init.d/httpd start

if [ ! -f /log/olap_server.log ]; then
		touch /log/olap_server.log
fi

if [ ! -f /log/olap_server.log ]; then
		touch /log/olap_server.log
fi

tail -f /log/*.log /log/tomcat/*.log
