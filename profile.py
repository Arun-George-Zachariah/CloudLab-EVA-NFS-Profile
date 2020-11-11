"""This profile sets up an n-node cluster of machines along with an NFS server. The NFS server uses a long term dataset that is persistent across experiments that is mounted at `/nfs` on all nodes along with a temporary block storage mounted at `/mydata` across all nodes.

Instructions:
Click on any node in the topology and choose the `shell` menu item. Your shared NFS directory is mounted at `/nfs` on all nodes."""

# Geni imports
import geni.portal as portal
import geni.rspec.pg as pg

# Creating the portal context.
pc = portal.Context()

# Creating a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# List of Images
imageList = [
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD', 'UBUNTU 20.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD', 'UBUNTU 18.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU16-64-STD', 'UBUNTU 16.04'),
]

# Defining the input parameters.
pc.defineParameter("userName", "User name",portal.ParameterType.STRING, "", longDescription="Your CloudLab user name.")
pc.defineParameter("num_nodes", "Number of nodes", portal.ParameterType.INTEGER, 4)
pc.defineParameter("os_image", "Select OS image", portal.ParameterType.IMAGE, imageList[2], imageList)
pc.defineParameter("node_type", "Hardware type of all nodes", portal.ParameterType.NODETYPE, "", longDescription="A specific hardware type to use for each node.")
pc.defineParameter("ext_uri", "External Dataset URI", portal.ParameterType.STRING, "")
pc.defineParameter("agree", "I agree to use only deidentified data", portal.ParameterType.BOOLEAN, True, longDescription="By checking the box, I agree to store and process only deidentified data on this node.")
params = pc.bindParameters()

# Performing the validations.
if not params.agree or params.num_nodes < 2:
    pc.reportError(portal.ParameterError("Cannot proceed with the experiment.", [params.agree, params.num_nodes]), True)

# Setting the required NFS network options.
nfsLan = request.LAN("nfsLan")
nfsLan.best_effort = True
nfsLan.vlan_tagging = True
nfsLan.link_multiplexing = True

# Defining the NFS server.
nfsServer = request.RawPC("nfs")
nfsServer.disk_image = params.os_image

# Attaching the NFS server to LAN.
nfsLan.addInterface(nfsServer.addInterface())

# Defining the initialization script for the server
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-server.sh"))

# Defining the node that represents the ISCSI device where the dataset resides
dsnode = request.RemoteBlockstore("dsnode", "/nfs")
dsnode.dataset = params.ext_uri

# Defining the link between the NFS server and the ISCSI device that holds the dataset
dslink = request.Link("dslink")
dslink.addInterface(dsnode.interface)
dslink.addInterface(nfsServer.addInterface())

# Setting the required attributes for this link.
dslink.best_effort = True
dslink.vlan_tagging = True
dslink.link_multiplexing = True

# Dynamically creating the nodes.
for i in xrange(params.num_nodes):
    # Adding a raw PC to the request
    node = request.RawPC("vm%d" % i)

    # Specifying the disk image.
    node.disk_image = params.os_image

    # Specifying the hardware type
    if params.node_type:
        node.hardware_type = params.node_type

    # Adding the NFS LAN interface
    nfsLan.addInterface(node.addInterface())

    # Defining the initialization script for the clients
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))

    # Mounting a temporary block storage.
    bsname = "bs%d" % i
    bs = node.Blockstore(bsname, "/mydata")
    bs.size = "0GB"
        
    # Changing permissions of the block storage.
    bs_perm_cmd = "sudo chown " + params.userName + " /mydata"
    node.addService(pg.Execute(shell="bash", command=bs_perm_cmd))

# Printing RSpec to the enclosing page.
pc.printRequestRSpec(request)
