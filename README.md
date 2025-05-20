# CI/CD Workflow with Tekton Cluster

<h2 align="center"> Overview </h2>

This workflow demonstrates how to use a **Tekton Cluster** (running on a spare machine) to automate CI/CD tasks triggered from a main desktop. The pipeline pulls, processes it, and pushes the results to GitHub.

_We will try to push the python files (one with correct syntax and one with incorrect) to check if tekton halts the commit or not._

---

<h2 align="center"> Workflow Diagram </h2>

```plaintext
[Main Desktop]
     |
     | 1. Push code / trigger pipeline (e.g., via SSH, webhook, etc.)
     ↓
[Spare Machine (Tekton Cluster)]
     |
     | 2. Pull code from main desktop / repo
     | 3. Run pipeline steps (build, test, dvc push, etc.)
     | 4. Push final code/results to GitHub or remote storage
     ↓
[GitHub / DVC Remote]
```
---

<h2 align="center"> 🧩 Components Needed </h2>
1. Kubernetes on spare machine (e.g., Minikube, kind, or k3s)
2. Tekton Pipelines installed in Kubernetes
3. Git installed and authorized to push to GitHub

---

<h2 align="center">Setup</h2>

### Setting up Tekton

1. Install Docker and enable Kubernetes in the Spare Machine.
2. Install Tekton Pipelines :</br>
   ``kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml``
3. Verify using ``kubectl get pods --namespace tekton-pipelines``.
   You should see pods with names like tekton-pipelines-controller and tekton-pipelines-webhook in the Running state.
4. Download tekton (https://github.com/tektoncd/cli/releases) and add into PATH under environment variables.
5. Verify in cmd using ``tkn version``
6. Use the command below to enable dashboard: </br>
   ``kubectl apply --filename https://storage.googleapis.com/tekton-releases/dashboard/latest/release.yaml``
7. Enable dashboard using ``kubectl proxy``
8. Browse using ``http://localhost:8001/api/v1/namespaces/tekton-pipelines/services/tekton-dashboard:http/proxy/``

---

![image](https://github.com/user-attachments/assets/5378faa5-458d-4ffd-9fa0-8e07b62acb0f)

---

### Setting up Pipelines, Tasks, EventListeners in Tekton

1. Create the pipelines/tasks using ``kubectl apply -f <yaml_file_name> -n <namespace_name>``.
2. Create a role binding service account _(needed for the event-listener)_.
3. Bind the service account using the command ``kubectl apply -f <role_binding_yaml_file>``
4. Forward the github-eventlistener port to 8080 using ``kubectl port-forward svc/el-github-listener -n tekton-pipelines 8080:8080``
5. Install NGROK, and make the port visible. ``ngrok http 8080``
6. Create a webhook(application/json) using the ngrok link. _(json passed will be used to pull the "refs" and the "clone_url" defined in the trigger-bind.yaml file)_

To do: fix the event-listener pod. _(event-listener service is running, but pod is throwing crashloopbackoff error)_

