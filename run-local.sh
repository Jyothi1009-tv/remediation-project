#!/bin/bash

set -e

echo "Agent 1: OWASP"

mkdir -p reports
export NVD_API_KEY=D231509C-B765-F111-836C-0EBF96DE670D

mvn 