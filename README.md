JupyterHub on Kubernetes for Data 8
=======

[![Build Status](https://travis-ci.org/data-8/jupyterhub-k8s.svg?branch=master)](https://travis-ci.org/data-8/jupyterhub-k8s)

This repo contains the Kubernetes config, container images, and docs for Data
8's deployment of JupyterHub on Kubernetes. This is a major work in progress
and is not ready for the real world yet.

Why was this deployment created?
-------
##### The Problem:
Berkeley's Data-8 class was using a jupyterhub deployment using ansible. However, this deployment was difficult to deploy, prone to errors, and time consuming. This made the deployment unapproachable for non technical instructors to setup.

##### The Solution:
With this kubernetes deployment, any instructors, regardless of technical ability, will be able to easily spin up their own cluster with **two** commands. 

Who is this for?
-------
The deployment is designed for any instructor wanting to run a no-hassel jupyterhub deployment.

Getting Started
-------

### Google Cloud

Clone this repo:

    git clone https://github.com/data-8/jupyterhub-k8s

Set up a Kubernetes cluster using Google Container Engine. Other cloud
providers are not currently supported but will be before release.

Configure [`kubectl`][kubectl] to point to your cluster. This is automatically
done when using `minikube` or the `gcloud` CLI. Verify that

    kubectl cluster-info

Returns output that looks like:

    Kubernetes master is running at https://146.148.80.79

Then, from the project root, run

    kubectl apply -f manifest.yaml

That deploys JupyterHub!

### Azure Deployment

An easy way to deploy k8s on azure is through [`kubernetes-anywhere`][k8sanywhere]. Make sure to run all of the following on an Ubuntu vm on Azure.

First, install [`docker`][docker]

Clone the repo and start a docker container

    git clone https://github.com/kubernetes/kubernetes-anywhere && cd kubernetes-anywhere && make docker-dev

After the container starts, run:

    make deploy

Enter the following configurations:
**Phase 1**

```python
phase1.num_nodes: ''
phase1.cluster_name: '<name of cluster>'
phase1.cloud_provider: 'azure'
phase1.azure.subscription_id: '<azure subscription id>'
phase1.azure.client_id: ''
phase1.azure.client_secret: ''
phase1.azure.image_publisher: ''
phase1.azure.image_offe: ''
phase1.azure.image_sku: ''
phase1.azure.image_version: ''
phase1.azure.storage_account_name: ''
phase1.azure.master_vm_size: ''
phase1.azure.node_vm_size: ''
phase1.azure.master_private_ip: ''
phase1.azure.location: '<location of resource group>' # ex. 'westus'
phase1.azure.admin_username: '<username>'
phase1.azure.admin_password: '<password>' # must be 6-24 chars and at least one lower case, one uppercase char and one non-letter char
```

**Phase 2**

```python
phase2.installer_container: ''
phase2.docker_registry: ''
phase2.kubernetes_version: 'v1.5.0' # or the latest version of k8s
phase2.provider: ''
```

**Phase 3**: Deploying Addons

```python
phase3.run_addons: 'y'
phase3.kube_proxy: 'y'
phase3.dashboard: 'y'
phase3.heapster: 'y'
phase3.kube_dns: 'y'
```

If you get an error or mess up somewhere on the `make deploy`, do the following and start again from `git clone`:

```
docker images
docker rmi <image id of kubernetes-anywhere> && docker rmi <image id of mhart/alpine-node>
cd .. && sudo rm -Rf kubernetes-anywhere
```

Open the link it gives you and enter the code it gives you

Ctrl+D or run `exit`

Setup kube config

```
mkdir -p ~/.kube && cp ./phase1/azure/.tmp/kubeconfig.json ~/.kube/config
```

Verify that everything is working

```
kubectl get nodes
```

To run the data8 deployment:
```
cd ~ && git clone https://github.com/data-8/jupyterhub-k8s.git && cd jupyterhub-k8s && kubectl apply -f manifest.yaml
```
**Note:**
    You must change the storage class spec in the `manifest.yaml` to:

```
parameters:
  storageAccount: '<storage account>'
```

And:

```
provisioner: kubernetes.io/azure-disk
```

(Where **<storage account>** is your storage account in the resource group)


[kubectl]: http://kubernetes.io/docs/user-guide/prereqs/
[k8sanywhere]: https://github.com/kubernetes/kubernetes-anywhere/blob/master/phase1/azure/README.md
[docker]: https://docs.docker.com/engine/installation/linux/ubuntulinux/

File / Folder structure
-------

The `manifest.yaml` file in the project root directory contains the entirety of
the Kubenetes configuration for this deployment.

The subdirectories contain the Dockerfiles and scripts for the images used for
this deployment.

All the images for this deployment are pushed to the [data8 Docker Hub][]
organization and are named `data8/jupyterhub-k8s-<name>` where `<name>` is the
name of the containing folder for that image.

[data8 Docker Hub]: http://hub.docker.com/r/data8/

Development
-------

Current work on this project lives in a [ZenHub][] board for this repo. You
must install the browser extension to see the board.

After installing the extension, navigate to [the issue board](#boards) or press
`b`. You'll see a screen that looks something like this:

![screenshot 2016-11-04 13 24 21](https://cloud.githubusercontent.com/assets/2468904/20021193/084bb660-a292-11e6-9720-10746f475746.png)

- **Icebox** contains future tasks that haven't been prioritized.
- **This week** contains tasks that we plan to finish this week.
- **In Progress** contains tasks that someone is currently working on. All of
  these tasks have at least one person assigned to them.
- When the task is complete, we close the related issue.

**Epics** are groups of tasks that correspond to a complete feature. To see
only issues that belong to a specific Epic, you can click / unclick the
"Filter by this epic" button on the Epic.

[ZenHub]: https://www.zenhub.com/

### Workflow

1. As tasks / issues first get created, they land in the **Icebox** pipeline
   and are categorized into an **Epic** if needed.
2. During our weekly planning meetings we'll move tasks from **Icebox** to
   **This Week**.
3. When team members start actively working on a task, they'll assign
   themselves to the task and move it into the **In Progress** pipeline.
4. When team members finish a task, they'll make a Pull Request for the task.
   When the PR gets merged, they'll close the task to take it off the board.
