"""This profile sets up an n-node cluster of machine along with a NFS server. The NFS server uses a long term dataset that is persistent across experiments and is mounted at `/nfs_data` on all nodes.

Instructions:
Click on any node in the topology and choose the `shell` menu item. Your shared NFS directory is mounted at `/nfs_data` on all nodes."""

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
pc.defineParameter("num_nodes", "Number of nodes", portal.ParameterType.INTEGER, 4)
pc.defineParameter("os_image", "Select OS image", portal.ParameterType.IMAGE, imageList[2], imageList)
pc.defineParameter("node_type", "Hardware type of all nodes", portal.ParameterType.NODETYPE, "", longDescription="A specific hardware type to use for each node.")
pc.defineParameter("storage_size", "Storage Size (GB)", portal.ParameterType.INTEGER, 250)
pc.defineParameter("ext_uri", "External Dataset URI", portal.ParameterType.STRING, "")
params = pc.bindParameters()

# Setting the required NFS network options.
nfsLan = request.LAN("nfs_lan")
nfsLan.best_effort = True
nfsLan.vlan_tagging = True
nfsLan.link_multiplexing = True

# Defining the NFS server.
nfsServer = request.RawPC("nfs_server")
nfsServer.disk_image = params.os_image

# Attaching the NFS server to LAN.
nfsLan.addInterface(nfsServer.addInterface())

# Defining the initialization script for the server
nfsServer.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-server.sh"))

# Defining the node that represents the ISCSI device where the dataset resides
dsnode = request.RemoteBlockstore("dsnode", "/nfs_data")
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

    # Adding the NFS LAN interface
    nfsLan.addInterface(node.addInterface())

    # Defining the initialization script for the clients
    node.addService(pg.Execute(shell="sh", command="sudo /bin/bash /local/repository/nfs-client.sh"))

# Printing RSpec to the enclosing page.
pc.printRequestRSpec(request)