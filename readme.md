#Create automatically docker images for jedox

Aim ist being able to create automatically jedox images. You can specify the download url from jedox,
or provide the directory where the install tar has been extracted. The program then automatically install jedox, 
and create the corresponding docker image.

All was done based on the (https://github.com/zkhadikov/dockerize_jedox/ "work from Zurab Khadikov")


##Usage


--installer-download', help='download the installer rather than using a local one',default=False)
--installer-directory',type=str, help='where the install files are or will be uncompressed',default="/opt/jedox_installation")
--jedox-home',type=str, help='directory where jedox is installed default=/opt/jedox/ps',default="/opt/jedox/ps")
--jedox-version', help='Jedox version to be installed ex: 6.0_SR1',default="6.0_SR1")
--base-image', help='name of the docker base image to be created default=jedox/base',default="jedox/base")
--config', help='json config file',default="./config.json")
--docker-repository', help='docker repository where the image will be stored',default="leanbi/jedox6")
--docker-tag', help='tag used for storing final docker image',default="$jedox_version")