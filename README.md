[![Build Status](https://circleci.com/gh/cloudify-examples/cloudify-rolling-upgrade.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/cloudify-examples/cloudify-rolling-upgrade)

# Rolling Upgrade Example Project
___
## Overview/Requirements

This projects demonstrates a rolling upgrade implementation in the form of a Cloudify blueprint. It was developed and tested with Cloudify manager 3.3.1 and Openstack Kilo. It has the following characterstics and limitations:
* It is based on the standard Nodecellar project, but does not include MongoDb.
* It demonstrates upgrading a NodeJS hosted webapp
* Upgrading is implemented in the form of a workflow.  No plugins are used.
* The blueprint includes HAProxy as the load balancer
* The workflow supports upgrading some of all of the instances of the webapp
* The workflow algorithm is:
  * FOR EACH NODEJS INSTANCE 'N'
    * Remove 'N' from the load balancer
    * Upgrade the webapp in the NodeJS instance
    * Add the webapp back into the loadbalancer
* The workflow accepts a 'percentage' parameter (defaults to 100), which causes only a portion of the instances to be upgrade
* The workflow accepts a 'pause' parameter (defaults to 0), which causes the workflow to pause for a specified number of seconds between each upgrade.
* The workflow accepts a 'version' parameter which causes only instances with lesser version to be upgraded.  Version numbers of the form a.b, where and b are positive integer.
* Version precendence is determined by treating the version 'a.b' as a float, and doing a simple arithmetic compare.
* Workflow errors cause rollback
* A file naming convention is used to identify the version of the webapp archive.  The scheme is &lt;name&gt;-&lt;a.b&gt;.tgz, where 'a' is the major version number and 'b' the minor version number.
* For ease of verification test, the webapp only has one output: the current version installed.

---

## Operational Guidelines

The webapp rolling upgrade example consists of a custom workflow, _webapp_upgrade_, and related scripts.  The usage of webapp_upgrade:
* For a rolling upgrade of all instances, run `cfy executions start -w webapp_upgrade -p <parms>`. Parameters:
  * `version`.  The version number of the new webapp.  The version is interpreted as a simple floating point number in this implementation (i.e. 1.2 > 1.1).  Webapps that are not at a lower version will not be upgraded.
  * `url`. The URL of the new webapp.  The webapp must be packaged as compressed gzip file, named with the following pattern: `<name>_<version>.tgz`.  For example: mywebapp_1.1.tgz.  This simple naming convention is mainly used to communicate the version of the webapp during the initial install (which has no "version" parameter).
  * `pause`: The number of seconds to sleep between instance upgrades.
* For a rolling upgrade using an A/B strategy, the `percentage` parameter is used.  It is an integer from 0 to 100 (default is 100), indicating the percentage of webapp instances to be upgraded.

### Running The Example Blueprint
In order to deploy and run the blueprint, the following process should be followed.  This process uses the Cloudify UI.:

#### Prerequisites:
* Access to an Openstack environment with resource creation permissions.
* A boostrapped Cloudify manager (version 3.3.1) in the Openstack environment.

#### Instructions:

1. Clone this repo : `git clone https://github.com/cloudify-examples/cloudify-rolling-upgrade.git`
2. In order to run the blueprint, the test applications must be accessible from a URL accessible from Openstack.  If you don't have a web server, you can easily create a simple one on a host with Python 2.7 installed.  Either use a pre-exiting host, create an instance in Openstack (with a public IP), or ssh to the Cloudify manager.  To serve the apps from the Cloudify server, first transfer the test apps to the server (e.g. `scp  -i ~/.ssh/cloudify-manager-kp.pem upgrade-test-1.0.tgz centos@<manager_ip>:upgrade-test-1.0.tgz`) from the blueprint/resources directory.  Then ssh to the server (`ssh -i ~/.ssh/cloudify-manager-kp.pem centos@<manager_ip>`) and start the server by running the following command: `nohup python -m SimpleHTTPServer <port> >/dev/null 2>&1 &`.  The server will listen on the supplied port.

##### UI Method
3. Navigate a browser to the Cloudify UI (<manager_ip>:80).
4. Edit the `openstack-blueprint.yaml` file, and replace the `application_url` property value for the `nodejs_app` node with the URL and port corresponding to the server started in step 2.
5. From the blueprint directory, package the blueprint for upload to the manager: `tar czf blueprint.tgz *`.
6. From the Cloudify manager UI, upload the blueprint.tgz file using the "Upload Blueprint" button.
7. Select the new blueprint and create a deployment.  Set inputs according to these guidelines:
  * Include a Linux image id from those available in Openstack.  The blueprint was tested against Ubuntu 14.04.
  * Set the flavor ID, to a flavor with at least 2GB of RAM.
  * Set the agent user to the OS user that the image represents (`centos` for Centos, `ubuntu` for Ubuntu).
8. Select the newly created deployment and execute the "install" workflow. 
9. The deployment outputs show the URL of the resulting load balancer.  Visit the URL in a browser.  The output will be "Version=1.0".
10. To upgrade the deployment, execute the `webapp_upgrade` workflow.  Required parameters are "url" and "version".  "url" should point to the URL with new webapp (e.g. http://10.1.0.3/upgrade-test-1.1.tgz), and "version" should be set to "1.1".
12. To test the rollback capability, run the `execute_operation` workflow.  Target an instance (or all of them), and run the `rollback` operation on that instance.  To verify the rollback, you'll need to ssh to the manager (or other server on the deployment network), and run `curl <instance ip>:8080`.  The instance will return 1.0.


##### CLI Method
3. Edit the `openstack-blueprint.yaml` file, and replace the `application_url` property value for the `nodejs_app` node with the URL and port corresponding to the server started in step 2.
4. From the blueprint directory run `cfy blueprints upload -b <name> -p openstack-blueprint.yaml`.
5. Edit the inputs file, and set values according to these guidelines:
  * Include a Linux image id from those available in Openstack.  The blueprint was tested against Ubuntu 14.04.
  * Set the flavor ID, to a flavor with at least 2GB of RAM.
  * Set the agent user to the OS user that the image represents (`centos` for Centos, `ubuntu` for Ubuntu).
6. Create the deployment `cfy deployments create -b <blueprint-id from step 4> -d <deployment-id> -i inputs.yaml`.
7. Run the install workflow: `cfy executions start -w install -d <deployment-id>.
8. The deployment outputs show the URL of the resulting load balancer.  Visit the URL in a browser.  The output will be "Version=1.0".  Get the outputs by running `cfy deployments outputs -d <deployment-id>`.
9. To upgrade the deployment, execute the `webapp_upgrade` workflow.  Required parameters are "url" and "version".  "url" should point to the URL with new webapp (e.g. http://10.1.0.3/upgrade-test-1.1.tgz), and "version" should be set to "1.1". For example `cfy executions start -w webapp_upgrade -d <deployment-id> -p '{"url":"your-url","version":"1.1"}'
10. After the workflow execution, access the load balancer url.  The output is "Version=1.1".
11. To test the rollback capability, run the `execute_operation` workflow.  Target an instance (or all of them), and run the `rollback` operation on that instance.  To verify the rollback, you'll need to ssh to the manager (or other server on the deployment network), and run `curl <instance ip>:8080`.  The instance will return 1.0. For examle: `cfy executions start -w execute_operation -d <deployment-id> -p '{"operation":"webapp_upgrade.rollback","node_ids","nodejs_app"}'.
12. To test the partial upgrade capability, when performing step 9, set the `percentage` property to 50.  Then verify that only one instance was upgraded by accessing the URL on the instances.

## Code Organization and Algorithm
The code and configuration that implements the rolling upgrade algorithm is organized as a blueprint and associated artifacts in subdirectories as so:
* `types/upgrade.yaml` - This file contains the interface definition that identifies a node as an upgradable webapp.
* `scripts/nodejs/upgrade.py` - Implementation of the upgrade algorithm for a particular instance.  Compares new version number to existing, and only upgrades if newer.  Saves current version for possible rollback. 
* `scripts/nodejs/rollback.py` - Implementation of the rollback algorithm for a particular instance.
* `openstack-blueprint.yaml` - Contains the definition of the upgrade workflow, which references the workflow implementation.
* `scripts/upgrade_workflowy.py` - Implementation of the upgrade workflow.  The workflow follows the following sequence:
![Upgrade Sequence](upgrade-uml-seq.png)

## Authoring Guidelines
In order to utilize this example to create a new implementation, there are some parts that must change, and some parts that can stay the same.  No need to change:
* `scripts/upgrade_workflow.py` - The algorithm is written in an implementation independent way.  However, it is tied to the HAProxy relationship `app_connectedto_haproxy` which is defined in the `types\haproxy.yaml` file.  This relationship is used to connect and disconnect the load balancer from individual instances.  If using a different load balancer (and therefore different relationship), this reference will need to be changed.  The assumption is that the `unlink` and `establish` operations remove and add instances to the load balancer configuration.
* `openstack-blueprint.yaml` - The workflow definition in this file can be left the same, and replicated exactly as is to other blueprints, provided the same "scripts" directory structure is maintained.

Files that probably need to be changed (or whose functions need to be replicated):
* `resources/*.tgz` - These are the simple webapps used for the demonstration.  They are constructed for ease of installation in NodeJS.  Other target web servers will have other needs.  Also note that the file names are specifically formatted to communicate the version number to their respective install scripts.  Other version numbering schemes may require other naming formats, or entirely new ways of communicating version info (for example a "version.txt" file in the archive).  This is needed because the default "install" workflow has no way to communicate a version number to underlying scripts as a parameter.
* `scripts/nodesj/{upgrade,rollback}.py` These scripts perform the upgrade and rollback operations on individual nodes.  As such, they are tied to the NodeJS implementation for both installation and restarting of the server.  Other servers will have other needs.  Also note that there is an implicit assumption about the format of version numbers and their comparison.  Other schemes will need other logic.
* `scripts/nodejs/install-nodejs-app.sh` - This script infers the version number of the webapp from the file name.  If another scheme of version numbering is desired, different logic will need to be implemented.
* the remained of the scripts in `scripts/nodejs` - These scripts are all tied to NodeJS and would need to be replaced with other code for another web server (or other application provider).


