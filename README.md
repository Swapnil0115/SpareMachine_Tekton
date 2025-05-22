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
2. Install Tekton Interceptors using ``kubectl apply --filename https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml``
3. Install Tekton CRDs :</br>
   ``kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml``
4. Verify using -> ``kubectl get pods --namespace tekton-pipelines``.
   You should see pods with names like tekton-pipelines-controller and tekton-pipelines-webhook in the Running state.
5. Download tekton (https://github.com/tektoncd/cli/releases) and add into PATH under environment variables.
6. Verify in cmd using ``tkn version``
7. Use the command below to enable dashboard: </br>
   ``kubectl apply --filename https://storage.googleapis.com/tekton-releases/dashboard/latest/release.yaml``
8. Forward the dashboard service to any port to access from localhost using this command -> ``kubectl port-forward svc/tekton-dashboard -n tekton-pipelines 9097:9097``

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

#### Error 1: Interceptors 
Fix for the event-listener:
It was due to the error: "error":"Timed out waiting on CaBundle to available for clusterInterceptor: Timed out waiting on CaBundle to available for Interceptor: empty caBundle in clusterInterceptor spec".

To fix this:
1. Ensure the Tekton Triggers Custom Resource Definitions (CRDs) and controller are installed properly by running ``kubectl apply -f https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml``
2. Ensure Tekton Interceptors are installed (We missed this in setup on the first setup).
``kubectl apply --filename https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml``
4. This resolves the clusterInterceptor error. (As the name suggest, interceptors were missing).
5. Forward the port for event-listener and setup webhooks again using ngrok.
6. Commit and push

#### Error 2: SecurityContext
1. Run ``kubectl edit configmap feature-flags -n tekton-pipelines``
2. If ``set-security-context: "false"``, change it to ``set-security-context: "true"``. ([Reference](https://tekton.dev/docs/pipelines/additional-configs/#running-taskruns-and-pipelineruns-with-restricted-pod-security-standards))
3. Commit and Push again.

#### Error 3: Failed to create pod due to config error
More details: container has runAsNonRoot and image will run as root
</br>
Fix: 
1. Add this under securityContext in all tasks ->
```yaml
runAsNonRoot: true
runAsUser: 1000
```
3. Push again.

Output:
![image](https://github.com/user-attachments/assets/07ab3cde-7f23-4961-8f93-2568b9942251)

to do:
fix workspaces and environments for the nonrootuser.

NonRootUser canno't cd to /workspace/output.
</br>
Create a workspace _(Workspaces allow Tasks to declare parts of the filesystem that need to be provided at runtime by TaskRuns. A Taskrun can use existing volumes or create a new one and discard after run.)_
Error: ``message: '"step-push" exited with code 128'``
Run this to get more details on error: ``kubectl logs <pod_name> -c step-push -n tekton-pipelines``
</br>
Use Workspaces to fix this error
---

<h2 align="center">GitHub branch protection rules Setup</h2>

To Do:
To ensure that all changes go through Tekton before merging to main, 
setup GitHub branch protection rules and a Tekton-based CI workflow that reports status checks to GitHub.
