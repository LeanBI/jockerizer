from jedox_auto_installer import *
import subprocess
from docker import Client
import json
import os
from time import sleep
from string import Template

class dockerizer(default_logger):
    def __init__(self,args):
        default_logger.__init__(self,"dockerizer")
        self.args=args
        self.config=self.get_config()
        self.args["eula"]=self.config["installer"]["eula"]
        self.directory=(os.path.dirname(os.path.realpath(__file__)))

        self.base_image_name=args["base_image"]
        self.docker=Client(base_url='unix://var/run/docker.sock')


        self.installer=jedox_installer(args)
        self.installer.start()
        sleep(15)
        self.installer.stop()
        sleep(15)

        self.patch()
        self.add()
        self.build_base_image(self.base_image_name)
        self.base_container=self.docker.create_container(self.base_image_name)
        self.docker.start(self.base_container)
        self.docker_exec(self.base_container,self.config["docker"]["exec"])
        self.commit(self.args["docker_repository"],self.args["docker_tag"])
        #remove intermediate container
        self.logger.info("removing base container")
        self.docker.remove_container(container=self.base_container,force=True)

    def get_config(self):
        try :
            config_file=self.args["config"]
            version=self.args["jedox_version"]

            j=json.load(open(config_file))
            return j[version]

        except KeyError as e:
            self.logger.exception(e)
            self.logger.error("Could not find the right config for version=%s in file=%s \n Aborting..." % (version,config_file))
            sys.exit(1)

    def patch(self):
        self.logger.info("patching files from installer")
        self.change_working_directory("patch")

        for p in self.config["patch"]:
            target=os.path.join(self.args["jedox_home"],p["target"])
            description=p.get("description",p["target"])

            self.logger.info("patching : %s" % description)
            subprocess.run("patch %s < %s" % (target,p["source"]),shell=True)

    def add(self):
        self.logger.info("adding additional content to installation")
        self.change_working_directory("add")

        for a in self.config["add"]:
            target=os.path.join(self.args["jedox_home"],a["target"])
            self.logger.info("copy %s to %s" % (a["source"],target))
            shutil.copy(a["source"],target)

    def change_working_directory(self,area):
        working_directory=os.path.join(self.directory,area,self.args["jedox_version"])
        self.logger.info("working dir is now %s" % working_directory)
        os.chdir(working_directory)

    def build_base_image(self,image_name="jedox/base"):
        os.chdir(self.args["jedox_home"])
        self.logger.info("Import Jedox Suite into intermediate docker image '%s'" % image_name)
        subprocess.call("""tar --to-stdout --numeric-owner --exclude=/proc --exclude=/sys --exclude='*.tar.gz' --exclude='*.log' -c ./ | docker import --change "CMD while true; do ping 8.8.8.8; done" --change "ENV TERM=xterm" - %s""" % image_name, shell=True)
        self.logger.info("successfully create basecontainer %s" % image_name)


    def docker_exec(self,myContainer,exec_list):

        self.docker.timeout=300
        for e in exec_list:
            if "description" in e : #print description in logs if available
                self.logger.info(e["description"])
            exec_c=self.docker.exec_create(myContainer,e["cmd"],stdout=True,stderr=True)
            output=self.docker.exec_start(exec_c)
            self.logger.debug(self.docker.exec_inspect(exec_c))
            self.logger.info(output)

        self.logger.debug("all exec done")

    def commit(self,repository,tag):
        tag=Template(self.args["docker_tag"]).safe_substitute(jedox_version=self.args["jedox_version"])
        self.logger.info("commiting finale image %s to %s : %s" % (self.base_container,repository,tag))

        config={"CMD":"/entrypoint",
                "EXPOSE": "[80,7777]",
                }
        self.docker.commit(self.base_container,repository,tag,conf=config)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Build a jedox image for docker')
    parser.add_argument('--installer-download', help='download the installer rather than using a local one',default=False)
    parser.add_argument('--installer-directory',type=str, help='where the install files are or will be uncompressed',default="/opt/jedox_installation")
    parser.add_argument('--installer-file',type=str, help='where the installer tar file is stored',default=False)
    parser.add_argument('--jedox-home',type=str, help='directory where jedox is installed default=/opt/jedox/ps',default="/opt/jedox/ps")
    parser.add_argument('--jedox-version', help='Jedox version to be installed ex: 6.0_SR1',default="6.0_SR2")
    parser.add_argument('--base-image', help='name of the docker base image to be created default=jedox/base',default="jedox/base")
    parser.add_argument('--config', help='json config file',default="./config.json")
    parser.add_argument('--docker-repository', help='docker repository where the image will be stored',default="jedox/base")
    parser.add_argument('--docker-tag', help='tag used for storing final docker image',default="$jedox_version")
    args = vars(parser.parse_args())

    installer=dockerizer(args)