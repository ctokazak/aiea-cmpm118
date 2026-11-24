#!/usr/bin/env bash
# Task 2 on Nautilus, step by step. Run from this folder after you've been added
# to the aiea-auditors namespace. Each step pauses so you can watch what happens.
set -euo pipefail
NS=aiea-auditors
cd "$(dirname "$0")"
pause() { read -r -p "--- $1  [enter to continue] "; }

kubectl auth can-i create jobs -n "$NS" | grep -q yes || { echo "No access to $NS yet."; exit 1; }

pause "1. Create the 5Gi PVC (ctokazak-task2)"
kubectl apply -f pvc.yaml
kubectl get pvc ctokazak-task2 -n "$NS"

pause "2. Create the deployment and wait for its pod"
kubectl apply -f deployment.yaml
kubectl rollout status deployment/ctokazak-task2-deploy -n "$NS" --timeout=15m
POD=$(kubectl get pod -n "$NS" -l app=ctokazak-task2 -o jsonpath='{.items[0].metadata.name}')
echo "pod: $POD"

pause "3. Copy cifar10train.py into the PVC and train on the deployment"
kubectl cp cifar10train.py "$NS/$POD:/data/cifar10train.py"
kubectl exec -n "$NS" "$POD" -- nvidia-smi --query-gpu=name,memory.total --format=csv
kubectl exec -n "$NS" "$POD" -- sh -c 'cd /data && python cifar10train.py' | tee logs/deployment_train.log

pause "4. Delete the deployment (never leave it idle)"
kubectl delete -f deployment.yaml
kubectl wait --for=delete pod -l app=ctokazak-task2 -n "$NS" --timeout=5m || true

pause "5. Run the same training as a Job on the same PVC"
kubectl apply -f job.yaml
kubectl wait --for=condition=complete job/ctokazak-task2-job -n "$NS" --timeout=60m
kubectl logs job/ctokazak-task2-job -n "$NS" | tee logs/job_train.log

pause "6. Delete the Job"
kubectl delete -f job.yaml
echo "Done. Screenshot logs/job_train.log (look for 'Device: cuda:0') for the deliverable."
echo "The PVC is kept; delete it with: kubectl delete -f pvc.yaml"
