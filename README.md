# Generic-Static-vCenter-VM-Shell-2G

The __Generic Static vCenter VM Shell 2G__ shell allows you to load an existing VM from your vCenter server into CloudShell. The VM is loaded as an inventory resource and provides the sandbox end-user with the automation capabilities of the vCenter cloud provider resource it is based on.

# Prerequisites
* vCenter cloud provider resource
* CloudShell 2021.2 and above

# High-level configuration flow
1. CloudShell admin imports the __Generic Static vCenter VM Shell 2G__ shell into CloudShell. For details, see CloudShell Help's [Importing Shells](https://help.quali.com/Online%20Help/0.0/Portal/Content/CSP/MNG/Mng-Shells.htm?Highlight=managing%20shells#Adding).
2. The CloudShell admin or domain admin creates an inventory resource from the shell.
3. The blueprint designer adds the static VM inventory resource to a sandbox.

# Importing the __Generic Static vCenter VM Shell 2G__ shell into CloudShell
* For details, see CloudShell Help's [Importing Shells](https://help.quali.com/Online%20Help/0.0/Portal/Content/CSP/MNG/Mng-Shells.htm?Highlight=managing%20shells#Adding).

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
