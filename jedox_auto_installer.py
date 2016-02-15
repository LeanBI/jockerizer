import logging
import argparse
import wget
import sys
import tarfile
import os
import pexpect
import subprocess
import shutil

class default_logger:
    def __init__(self,name,**kwargs):
        logger=logging.getLogger(name)
        level=kwargs.get("level","DEBUG")
        logger.setLevel(getattr(logging,level))
        formater=logging.Formatter("%(asctime)15s %(name)5s %(levelname)8s %(lineno)3d %(funcName)15s %(message)s")
        sh=logging.StreamHandler()
        sh.setFormatter(formater)
        logger.addHandler(sh)
        self.logger=logger



class jedox_installer(default_logger):
    def __init__(self,args):
        default_logger.__init__(self,"jedox_installer")
        self.args=args
        self.download_directory=self.args["installer_directory"]
        self.installer_directory=self.args["installer_directory"] + "/" + self.args["jedox_version"] + "/"

        if args["installer_download"]!=False:
            self.installer=self.download()
            self.uncompress()

        self.sign_eula()
        self.install()

    def remove_old_install(self):
        install_dir="/opt/jedox/ps"
        if os.path.isdir(install_dir):
            self.logger.warn("older installation detected : stopping and deleting...")
            try:
                self.stop()
            except Exception:
                self.logger.info("Could not stop jedox, probably not running")
            shutil.rmtree(install_dir)


    def download(self):

        url=self.args["installer_download"]
        self.logger.info("start downloading installer at : %s" % url)

        if not os.path.isdir(self.download_directory):
            os.mkdir(self.download_directory)
        installer_file = wget.download(url,self.download_directory)
        self.logger.info("saved as : %s" % installer_file)
        return installer_file

    def uncompress(self):
        """
        # delete directory content if not empty
        if os.path.isdir(self.installer_directory):
        """
        if not os.path.isdir(self.installer_directory):
            os.mkdir(self.installer_directory)
        self.logger.info("uncompress file %s to %s " % (self.installer,self.installer_directory))
        os.chdir(self.installer_directory)
        tar=tarfile.open(self.installer)
        tar.extractall()
        tar.close()

    def install(self):
        self.remove_old_install()
        os.chdir(self.installer_directory)
        install_script=os.path.join(self.installer_directory,"install.sh")
        self.logger.info("starting install script : %s" % install_script)
        if not os.path.isfile(install_script):
            self.logger.critical("installer not found, aborting")
            sys.exit(1)

        else :
            answers=[
                {"expect":"Default.*", "answer":"", "description":"jedox_home [/opt/jedox/ps]"},
                {"expect":"The directory.*", "answer":"y", "description":"create jedox_home directory [Y]"},
                {"expect":"Default.*", "answer":"jedoxweb", "description":"user for jedox-suite [jedoxweb]"},
                {"expect":"Default.*", "answer":"jedoxweb", "description":"group for jedox-suite [jedoxweb]"},
                {"expect":"What is this servers name ?.*", "answer":"jedox_ps", "description":"servers name", "timeout":60 },
                {"expect":"What is this servers IP-Address ? .*", "answer":"", "description":"servers IP-Address"},
                {"expect":"Who should get administrative e-mails regarding this server ?.*", "answer":"webmaster@email.com", "description":"admin email"},
                {"expect":"Which IP-address should the OLAP server run on.*", "answer":"all", "description":"olap ip"},
                {"expect":"Which port should the OLAP server run on ?.*", "answer":"7777", "description":"olap port"},
                {"expect":"Which IP-address should the HTTP server listen on.*", "answer": "all", "description":"http ip"},
                {"expect":"Which port should the HTTP server run on ?.*", "answer":"80", "description":"http port"},
                {"expect":"Which IP-address should the Spreadsheet server run on.*", "answer":"127.0.0.1", "description":"spreadsheet server ip"},
                {"expect":"Which port should the Spreadsheet server run on ?.*", "answer":"8193", "description":"spreadsheet server port"},
                {"expect":"Which AJP-address should the Tomcat server run on ?.*", "answer":"127.0.0.1", "description":"tomcat ajp ip"},
                {"expect":"Which AJP port should the Tomcat server run on ?.*", "answer":"8010", "description":"tomcat ajp port"},
                {"expect":"Which HTTP-address should the Tomcat server run on ?.*", "answer":"127.0.0.1", "description":"tomcat http ip"},
                {"expect":"Which HTTP port should the Tomcat server run on ?.*", "answer":"7775", "description":"tomcat http port"},
                     ]


            child = pexpect.spawn(install_script,env=os.environ)
            fout_file="installer_fout.log"
            fout = open(fout_file, "ab")
            child.logfile = fout
            i=0
            for a in answers:
                self.logger.info("awaiting question[%d]:%s expect=%s answer=%s timeout=%d" % (i,a["description"],a["expect"],a["answer"],a.get("timeout",-1)))
                child.expect (a["expect"],a.get("timeout",-1))
                child.sendline (a["answer"])
                i+=1
            child.expect(pexpect.EOF)
            fout.close()
            self.logger.info(open(fout_file).read())
            self.logger.info("install finished output below")

    def start(self):
        subprocess.run(["/opt/jedox/ps/jedox-suite.sh","start"], shell=False, check=True)
        #Starting httpd: [  OK  ]

    def stop(self):
        subprocess.run(["/opt/jedox/ps/jedox-suite.sh","stop"], shell=False, check=True)
        #Unmounting /opt/jedox/ps/sys...done.

    def sign_eula(self):
        eula_file=os.path.join(self.installer_directory,self.args["eula"])
        if not os.path.isfile(eula_file):
            with open(eula_file, 'a'):
                os.utime(eula_file, None)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a jedox image for docker')
    parser.add_argument('--installer-download', help='download the installer rather than using a local one',default=False)
    parser.add_argument('--installer-directory',type=str, help='where the install files are or will be uncompressed',default="/opt/jedox_installation")
    parser.add_argument('--jedox-version', help='Jedox version to be installed ex: 6.0_SR1',default="6.0_SR2")
    args = vars(parser.parse_args())

    installer=jedox_installer(args)