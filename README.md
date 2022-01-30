# Generic-Static-vCenter-VM-Shell-2G

Release date: December 2021

Shell version: 1.1.0

Document version: 2.0

# In This Guide

* [Overview](#overview)
* [Prerequisites](#prerequisites)
* [High-level configuration flow](#high-level-configuration-flow)
* [Downloading the shell](#downloading-the-shell)
* [Importing the shell into CloudShell](#importing-the-shell-into-cloudshell)
* [Offline installation](#offline-installation)
* [Creating the static VM resource](#creating-the-static-vm-resource)
* [Updating online Python dependencies](#updating-online-python-dependencies)

# Overview

The __Generic Static vCenter VM Shell 2G__ shell allows you to load an existing VM from your vCenter server into CloudShell. The VM is loaded as an inventory resource and provides the sandbox end-user with the automation capabilities of the vCenter cloud provider resource it is based on.

# Prerequisites

* vCenter cloud provider resource
* CloudShell 2021.2 and above

# High-level configuration flow

1. Download the __Generic Static vCenter VM Shell 2G__ shell locally.
2. CloudShell admin imports the __Generic Static vCenter VM Shell 2G__ shell to your computer.
3. The CloudShell admin or domain admin creates an inventory resource from the shell.
4. The blueprint designer adds the static VM inventory resource to a sandbox.

# Downloading the shell

The __Generic Static vCenter VM Shell 2G__ shell is available from the [Quali Community Integrations](https://community.quali.com/integrations) page. 

Download the files into a temporary location on your local machine. 

The shell comprises:

|File name|Description|
|:---|:---|
|Generic.Static.vCenter.VM.Shell.2G.zip|Device shell package|
|cloudshell-Generic-Static-vCenter-VM-Shell-2G-dependencies-win-package-1.0.0.zip, cloudshell-Generic-Static-vCenter-VM-Shell-2G-dependencies-linux-package-1.0.0.zip|Shell Python dependencies (for offline deployments only)|

# Importing the shell into CloudShell

* For details, see CloudShell Help's [Importing Shells](https://help.quali.com/Online%20Help/0.0/Portal/Content/CSP/MNG/Mng-Shells.htm?Highlight=managing%20shells#Adding).

# Offline installation

Offline installation instructions are relevant only if CloudShell Execution Server has no access to PyPi. You can skip this section if your execution server has access to PyPi. For additional information, see the online help topic on offline dependencies.

## Offline installation of a shell

In offline mode, import the shell into CloudShell and place any dependencies in the appropriate dependencies folder. The dependencies folder may differ, depending on the CloudShell version you are using:

See [Adding Shell and script packages to the local PyPi Server repository](#adding-shell-and-script-packages-to-the-local-pypi-server-repository).

## Adding shell and script packages to the local PyPi Server repository
If your Quali Server and/or execution servers work offline, you will need to copy all required Python packages, including the out-of-the-box ones, to the PyPi Server's repository on the Quali Server computer (by default *C:\Program Files (x86)\QualiSystems\CloudShell\Server\Config\Pypi Server Repository*).

For more information, see [Configuring CloudShell to Execute Python Commands in Offline Mode](http://help.quali.com/Online%20Help/9.0/Portal/Content/Admn/Cnfgr-Pyth-Env-Wrk-Offln.htm?Highlight=Configuring%20CloudShell%20to%20Execute%20Python%20Commands%20in%20Offline%20Mode).

**To add Python packages to the local PyPi Server repository:**
  1. If you haven't created and configured the local PyPi Server repository to work with the execution server, perform the steps in [Add Python packages to the local PyPi Server repository (offline mode)](http://help.quali.com/Online%20Help/9.0/Portal/Content/Admn/Cnfgr-Pyth-Env-Wrk-Offln.htm?Highlight=offline%20dependencies#Add). 
  
  2. For each shell or script you add into CloudShell, do one of the following (from an online computer):
      * Connect to the Internet and download each dependency specified in the *requirements.txt* file with the following command: 
`pip download -r requirements.txt`. 
     The shell or script's requirements are downloaded as zip files.

      * In the [Quali Community's Integrations](https://community.quali.com/integrations) page, locate the shell and click the shell's **Download** link. In the page that is displayed, from the Downloads area, extract the dependencies package zip file.

3. Place these zip files in the local PyPi Server repository.

# Creating the static VM resource
1. As CloudShell admin or domain admin, log into CloudShell Portal.
2. Switch to the suitable domain and open the __Inventory__ dashboard.
3. Click __+ Add New__.
4. Select __Generic Static vCenter VM 2G__.
5. Enter a __Name__ for the resource and click __Create__.
6. Fill in the details, as appropriate:

|Attribute|Description|
|:---|:---|
|VM NAME|Full path to the VM. For example: "VMs/Linux/my Linux VM"|
|VCENTER RESOURCE NAME|Name of the vCenter cloud provider resource|
|USER|VM user with administrator permission. Specify the user if you plan on allowing the sandbox end-user to establish in-browser connections to the VM's OS using QualiX.|
|PASSWORD|VM user's password|
7. Click __Continue__.
<br>CloudShell is discovering the resource. This may take a few minutes.

# Updating online Python dependencies
In online mode, the execution server automatically downloads and extracts the appropriate dependencies file to the online Python dependencies repository every time a new instance of the driver or script is created.

**To update online Python dependencies:**
* If there is a live instance of the shell's driver or script, terminate the shell’s instance, as explained [here](http://help.quali.com/Online%20Help/9.0/Portal/Content/CSP/MNG/Mng-Exctn-Srv-Exct.htm#Terminat). If an instance does not exist, the execution server will download the Python dependencies the next time a command of the driver or script runs.
