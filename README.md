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
2. Install Tekton CRDs :</br>
   ``kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml``
3. Install Tekton Interceptors using ``kubectl apply --filename https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml``
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
7. Generate the PAT github token, then apply the secrets and add it in triggertemplate using this command: ``kubectl create secret generic github-secret `
  --from-literal=username="<git username>" `
  --from-literal=password="github_pat_..." `
  -n tekton-pipelines``

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

#### Error 4: Workspace/Volume Issue

Error: ``message: '"step-push" exited with code 128'`` </br>
Run this to get more details on error: ``kubectl logs <pod_name> -c step-push -n tekton-pipelines``</br>

1. NonRootUser cannot cd to /workspace/output.
2. Create a workspace _(Workspaces allow Tasks to declare parts of the filesystem that need to be provided at runtime by TaskRuns. A Taskrun can use existing volumes or create a new one and discard after run.)_ [Refer](https://tekton.dev/docs/pipelines/workspaces/)

---

<h2 align="center">GitHub branch protection rules Setup</h2>
Referred -> [Configuring_github](https://medium.com/@ambeshgaunker123/automating-ci-cd-with-tekton-setting-up-github-webhooks-for-pr-pipelines-291308f03c59)

1) Added params and its values in all files in webhooks folder and in pipeline.yaml under pipelines folder.
2) Applied github-set-status.yaml using kubectl command which is why it's causing PodSecurity error.
   Solution -> Create a custom set-status task with required security contexts.
3) To Resolve :
```
May 29, 1:46:48 AMTraceback (most recent call last):
May 29, 1:46:48 AM  File "/tekton/scripts/script-0-82tvj", line 8, in <module>
May 29, 1:46:48 AM    with open(token_path, "r") as f:
May 29, 1:46:48 AM         ^^^^^^^^^^^^^^^^^^^^^
May 29, 1:46:48 AMFileNotFoundError: [Errno 2] No such file or directory: '/etc/github-set-status/token'

```

   ---

<h2 align="center"> Final Output: </h2>

1) git-status.yaml gets the realtime status from tekton via the webhook.
   ![image](https://github.com/user-attachments/assets/6979adc7-0ed4-4455-a760-1d18db43d836)
2) Set-status task sends the status and the finally block sends the final success/failure status.
   ![image](https://github.com/user-attachments/assets/ebfdd3f5-ce66-47a4-a181-b619878da5ef)

---

<h2 align="center">To Do </h2>

1. setup .gitignore to avoid github secret token passing into repo along with other unwanted files/ change the HOME dir to avoid loading libraries, gitcredentials, etc.
2. [Almost done]To ensure that all changes go through Tekton before merging to main, 
setup GitHub branch protection rules and a Tekton-based CI workflow that reports status checks to GitHub. [To_Read1](https://www.reddit.com/r/devops/comments/14qfuck/should_i_trigger_cicd_pipeline_on_merge_to_master/?force_seo=1)
3. Avoid resetting of airflow pushes (for a particular user in feature branch) when other user pushes their code into their feature/main branch.
4. Document properly :/

---

<h2 align="center"> Continuous Delivery (CD) Enhancements (To-Do) </h2>

The following steps can be added to complete the **CD** pipeline and make it production-grade:

1. **Artifact Delivery**
   - Push validated code or datasets to:
     - GitHub (different branch or release)
     - Google Cloud Storage (GCS)
     - DVC remote
     - Artifact Registry

2. **Automated Deployment**
   - Add deployment tasks such as:
     - `kubectl apply` for updated Kubernetes manifests
     - Uploading Airflow DAGs to Composer
     - Deploying Cloud Functions or Cloud Run services via `gcloud deploy`

3. **Versioning & Release Management**
   - Tag commits on success (`git tag`)
   - Create GitHub Releases programmatically

4. **Notifications & Logging**
   - Send Slack/email/webhook alerts on pipeline success/failure
   - Log pipeline run summaries to:
     - Stackdriver / Cloud Logging
     - BigQuery or log monitoring systems

5. **Post-Deployment Testing**
   - Add smoke tests or health checks for deployed services
   - Use `curl`, `pytest`, or `postman` tasks

🛠️ These enhancements ensure full automation from code validation to delivery, aligning with enterprise-grade CI/CD practices.

---

<h2 align="center"> 🛠️ To-Do: Tekton Push to `main` on Successful Tests </h2>

### 🧪 Goal:
Automate promotion of tested code to the `main` branch, **only if CI tasks succeed**, while handling open Pull Requests appropriately.

### ✅ Steps:
1. Add a `finally` block or gated step in your Tekton pipeline:
   - If tests pass, run a `git push` to `main` using a bot or service account.
   - Else, skip this step.

2. Modify the pipeline to:
   - Checkout the current feature branch
   - Rebase or cherry-pick tested commits onto `main`
   - Push `main` via Tekton’s Git step

3. Handle open PRs:
   - Option 1: **Auto-close the PR** using GitHub API (via Tekton Task)
   - Option 2: **Label PR as Merged via CI**, leave for manual cleanup
   - Option 3: Create protected PRs from `tekton-ci/*` branches and merge only if Tekton CI passes

4. Add PR cleanup automation:
   - Use GitHub Actions or Tekton to:
     - Comment on the PR
     - Add a label like `auto-merged-by-Tekton`
     - Close the PR if `main` already includes the changes

### 🔒 Notes:
- Protect the `main` branch to allow **only CI-based commits**
- Ensure GitHub token used has `repo` and `pull_request` scopes
- Avoid push loops by using a dedicated bot branch or CI-only tag

---

Note: Need a cleanup yaml file to cleaup kubernetes pod runs (eg: new pod gets created for every pipelinerun) every 1 hour to avoid errors like Pod Timeouts, etc.
