# Component 6: Ansible Configuration

## Executive Summary

Ansible automates the provisioning and configuration of Jenkins CI/CD infrastructure on GCP VMs. The playbooks handle VM creation, Docker installation, Jenkins deployment with SonarQube, and initial configuration. This enables reproducible, idempotent infrastructure setup for the CI/CD pipeline.

---

## 1. Concept & Theory

### What is Ansible?

Ansible is an **agentless configuration management** tool:
- **Agentless**: Uses SSH, no agents needed on target hosts
- **Declarative**: Describe desired state, not steps
- **Idempotent**: Run multiple times, same result
- **YAML-based**: Human-readable playbooks

### Why Ansible for CI/CD Infrastructure?

| Challenge | Ansible Solution |
|-----------|------------------|
| Manual VM setup | Automated provisioning |
| Configuration drift | Idempotent playbooks |
| Inconsistent environments | Same playbook = same setup |
| Documentation | Playbooks ARE documentation |

### Ansible Concepts

| Concept | Description |
|---------|-------------|
| **Inventory** | List of target hosts |
| **Playbook** | YAML file with tasks |
| **Role** | Reusable collection of tasks |
| **Task** | Single action (install, copy, etc.) |
| **Handler** | Task triggered by notification |
| **Variable** | Configuration parameters |

### Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCP Compute Engine VM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Docker Compose                         │   │
│  │  ┌─────────────────┐    ┌─────────────────┐             │   │
│  │  │    Jenkins      │    │   SonarQube     │             │   │
│  │  │  (Port 8080)    │    │   (Port 9000)   │             │   │
│  │  │                 │    │                 │             │   │
│  │  │  ┌───────────┐  │    │                 │             │   │
│  │  │  │  Docker   │  │    │                 │             │   │
│  │  │  │   CLI     │  │    │                 │             │   │
│  │  │  └───────────┘  │    │                 │             │   │
│  │  └─────────────────┘    └─────────────────┘             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Volumes:                                                        │
│  - /var/jenkins_home                                            │
│  - /var/run/docker.sock (for DinD)                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture & Design Decisions

### Directory Structure

```
ansible/
├── ansible.cfg              # Ansible configuration
├── deploy_jenkins.sh        # Quick deployment script
├── deploy_jenkins.yml       # Main playbook entry point
├── requirements.txt         # Python dependencies
├── inventory/
│   └── hosts.ini            # Target hosts
├── group_vars/
│   └── all.yml              # Global variables
└── playbooks/
    ├── 01_create_jenkins_vm.yml    # Provision GCP VM
    ├── 02_install_docker.yml       # Install Docker
    ├── 03_deploy_jenkins.yml       # Deploy Jenkins + SonarQube
    └── 04_configure_jenkins.yml    # Configure Jenkins
```

### Key Design Decisions

#### 1. Modular Playbooks
```yaml
# deploy_jenkins.yml - Orchestrates all playbooks
- import_playbook: playbooks/01_create_jenkins_vm.yml
- import_playbook: playbooks/02_install_docker.yml
- import_playbook: playbooks/03_deploy_jenkins.yml
- import_playbook: playbooks/04_configure_jenkins.yml
```

**Benefit**: Run individual playbooks or full stack.

#### 2. Docker Compose for Jenkins
```yaml
# Instead of bare Docker, use Compose for multi-container
services:
  jenkins:
    image: jenkins/jenkins:lts-jdk17
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # DinD
  sonarqube:
    image: sonarqube:9-community
```

**Rationale**: Easier management of Jenkins + SonarQube together.

#### 3. Idempotent Handlers
```yaml
- name: Restart Jenkins
  listen: "restart jenkins"
  community.docker.docker_compose:
    project_src: /opt/jenkins
    state: present
    restarted: yes
```

---

## 3. Implementation Guide

### Step 1: Ansible Configuration

```ini
# ansible/ansible.cfg
[defaults]
inventory = inventory/hosts.ini
remote_user = your_username
private_key_file = ~/.ssh/gcp_key
host_key_checking = False
retry_files_enabled = False

[privilege_escalation]
become = True
become_method = sudo
become_user = root
```

### Step 2: Inventory

```ini
# ansible/inventory/hosts.ini
[jenkins]
jenkins-vm ansible_host=34.123.45.67 ansible_user=your_username

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```

### Step 3: Group Variables

```yaml
# ansible/group_vars/all.yml
---
# Jenkins Configuration
jenkins_home: /var/jenkins_home
jenkins_port: 8080
jenkins_admin_user: admin
jenkins_admin_password: "{{ lookup('env', 'JENKINS_ADMIN_PASSWORD') | default('changeme') }}"

# SonarQube Configuration
sonarqube_port: 9000

# GCP Configuration
gcp_project: your-project-id
gcp_zone: us-east1-b
gcp_machine_type: e2-standard-2

# Docker Configuration
docker_compose_version: "2.21.0"
```

### Step 4: Create GCP VM Playbook

```yaml
# ansible/playbooks/01_create_jenkins_vm.yml
---
- name: Create Jenkins VM on GCP
  hosts: localhost
  connection: local
  gather_facts: no
  vars_files:
    - ../group_vars/all.yml

  tasks:
    - name: Create Jenkins VM
      google.cloud.gcp_compute_instance:
        name: jenkins-vm
        machine_type: "{{ gcp_machine_type }}"
        zone: "{{ gcp_zone }}"
        project: "{{ gcp_project }}"
        auth_kind: serviceaccount
        service_account_file: "{{ lookup('env', 'GOOGLE_APPLICATION_CREDENTIALS') }}"
        disks:
          - auto_delete: true
            boot: true
            initialize_params:
              source_image: projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts
              disk_size_gb: 50
        network_interfaces:
          - access_configs:
              - name: External NAT
                type: ONE_TO_ONE_NAT
        tags:
          items:
            - jenkins
            - http-server
        state: present
      register: vm_result

    - name: Wait for SSH
      wait_for:
        host: "{{ vm_result.networkInterfaces[0].accessConfigs[0].natIP }}"
        port: 22
        delay: 30
        timeout: 300

    - name: Add host to inventory
      add_host:
        name: jenkins-vm
        ansible_host: "{{ vm_result.networkInterfaces[0].accessConfigs[0].natIP }}"
        groups: jenkins
```

### Step 5: Install Docker Playbook

```yaml
# ansible/playbooks/02_install_docker.yml
---
- name: Install Docker on Jenkins VM
  hosts: jenkins
  become: yes
  vars_files:
    - ../group_vars/all.yml

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install prerequisites
      apt:
        name:
          - apt-transport-https
          - ca-certificates
          - curl
          - gnupg
          - lsb-release
        state: present

    - name: Add Docker GPG key
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present

    - name: Add Docker repository
      apt_repository:
        repo: "deb [arch=amd64] https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable"
        state: present

    - name: Install Docker
      apt:
        name:
          - docker-ce
          - docker-ce-cli
          - containerd.io
          - docker-compose-plugin
        state: present

    - name: Start Docker service
      systemd:
        name: docker
        state: started
        enabled: yes

    - name: Add user to docker group
      user:
        name: "{{ ansible_user }}"
        groups: docker
        append: yes
```

### Step 6: Deploy Jenkins Playbook

```yaml
# ansible/playbooks/03_deploy_jenkins.yml
---
- name: Deploy Jenkins with Docker
  hosts: jenkins
  become: yes
  vars_files:
    - ../group_vars/all.yml

  tasks:
    - name: Create Jenkins directories
      file:
        path: "{{ item }}"
        state: directory
        owner: 1000
        group: 1000
        mode: '0755'
      loop:
        - "{{ jenkins_home }}"
        - /var/jenkins_backup
        - /opt/jenkins

    - name: Create Docker Compose file
      copy:
        dest: /opt/jenkins/docker-compose.yml
        content: |
          version: '3.8'

          services:
            jenkins:
              image: jenkins/jenkins:lts-jdk17
              container_name: jenkins
              restart: unless-stopped
              privileged: true
              user: root
              ports:
                - "{{ jenkins_port }}:8080"
                - "50000:50000"
              volumes:
                - {{ jenkins_home }}:/var/jenkins_home
                - /var/run/docker.sock:/var/run/docker.sock
                - /usr/local/bin/docker:/usr/local/bin/docker
              environment:
                - JENKINS_OPTS=--prefix=/
                - JAVA_OPTS=-Duser.timezone=UTC
              networks:
                - jenkins-net

            sonarqube:
              image: sonarqube:9-community
              container_name: sonarqube
              restart: unless-stopped
              ports:
                - "{{ sonarqube_port }}:9000"
              environment:
                - SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true
              volumes:
                - sonarqube_data:/opt/sonarqube/data
                - sonarqube_extensions:/opt/sonarqube/extensions
                - sonarqube_logs:/opt/sonarqube/logs
              networks:
                - jenkins-net

          networks:
            jenkins-net:
              driver: bridge

          volumes:
            sonarqube_data:
            sonarqube_extensions:
            sonarqube_logs:
        mode: '0644'

    - name: Start Jenkins and SonarQube
      shell: |
        cd /opt/jenkins
        docker compose down || true
        docker compose up -d
      register: compose_result

    - name: Wait for Jenkins to start
      wait_for:
        port: "{{ jenkins_port }}"
        host: 0.0.0.0
        delay: 30
        timeout: 300

    - name: Wait for SonarQube to start
      wait_for:
        port: "{{ sonarqube_port }}"
        host: 0.0.0.0
        delay: 30
        timeout: 300

    - name: Install Docker CLI inside Jenkins
      shell: |
        docker exec jenkins bash -c "apt-get update && apt-get install -y docker.io"
      ignore_errors: yes

    - name: Get Jenkins initial admin password
      shell: |
        timeout 60 sh -c 'until [ -f {{ jenkins_home }}/secrets/initialAdminPassword ]; do sleep 2; done'
        cat {{ jenkins_home }}/secrets/initialAdminPassword
      register: admin_password
      when: not jenkins_configured.stat.exists

    - name: Display access information
      debug:
        msg:
          - "Jenkins URL: http://{{ ansible_host }}:{{ jenkins_port }}"
          - "SonarQube URL: http://{{ ansible_host }}:{{ sonarqube_port }}"
          - "Initial Admin Password: {{ admin_password.stdout | default('Already configured') }}"
```

### Step 7: Configure Jenkins Playbook

```yaml
# ansible/playbooks/04_configure_jenkins.yml
---
- name: Configure Jenkins
  hosts: jenkins
  become: yes
  vars_files:
    - ../group_vars/all.yml

  tasks:
    - name: Wait for Jenkins to be ready
      uri:
        url: "http://localhost:{{ jenkins_port }}/login"
        status_code: 200
      register: result
      until: result.status == 200
      retries: 30
      delay: 10

    - name: Install Jenkins plugins
      community.general.jenkins_plugin:
        name: "{{ item }}"
        url: "http://localhost:{{ jenkins_port }}"
        url_username: "{{ jenkins_admin_user }}"
        url_password: "{{ jenkins_admin_password }}"
        state: present
      loop:
        - git
        - github
        - pipeline
        - docker-workflow
        - kubernetes-cli
        - sonar
        - credentials-binding
      ignore_errors: yes

    - name: Create Jenkins job for Card Approval
      jenkins_job:
        name: card-approval-pipeline
        url: "http://localhost:{{ jenkins_port }}"
        user: "{{ jenkins_admin_user }}"
        password: "{{ jenkins_admin_password }}"
        config: "{{ lookup('template', 'job-config.xml.j2') }}"
      ignore_errors: yes
```

### Deployment Script

```bash
#!/bin/bash
# ansible/deploy_jenkins.sh

set -e

# Check prerequisites
command -v ansible >/dev/null 2>&1 || { echo "Ansible required"; exit 1; }

# Install Ansible collections
ansible-galaxy collection install google.cloud community.docker community.general

# Run playbooks
echo "Starting Jenkins deployment..."
ansible-playbook deploy_jenkins.yml -v

echo "Deployment complete!"
```

---

## 4. Key Concerns & Pitfalls

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Hardcoding passwords | Use `lookup('env', 'VAR')` or Vault |
| Not waiting for services | Use `wait_for` module |
| Running as wrong user | Check `become` and `remote_user` |
| Missing SSH keys | Ensure key is in `~/.ssh/` |

### Security Considerations

```yaml
# Use Ansible Vault for secrets
ansible-vault create secrets.yml

# Reference vault variables
jenkins_admin_password: "{{ vault_jenkins_password }}"

# Run with vault
ansible-playbook deploy_jenkins.yml --ask-vault-pass
```

### Debugging

```bash
# Verbose output
ansible-playbook deploy_jenkins.yml -vvv

# Check connectivity
ansible jenkins -m ping

# Dry run
ansible-playbook deploy_jenkins.yml --check

# Limit to specific host
ansible-playbook deploy_jenkins.yml --limit jenkins-vm
```

---

## 5. Testing & Validation

### Validation Checklist

```bash
# After deployment:

# 1. Check VM is running
gcloud compute instances list

# 2. Check Docker containers
ssh jenkins-vm 'docker ps'

# 3. Test Jenkins access
curl -I http://<JENKINS_IP>:8080

# 4. Test SonarQube access
curl -I http://<JENKINS_IP>:9000

# 5. Check Jenkins plugins
curl -u admin:password http://<JENKINS_IP>:8080/pluginManager/api/json
```

### Idempotency Test

```bash
# Run twice - should have no changes on second run
ansible-playbook deploy_jenkins.yml
ansible-playbook deploy_jenkins.yml  # Should show "changed=0"
```

---

## 6. Further Reading

- [Ansible Documentation](https://docs.ansible.com/)
- [Ansible GCP Collection](https://docs.ansible.com/ansible/latest/collections/google/cloud/)
- [Jenkins Docker Image](https://hub.docker.com/r/jenkins/jenkins)
- [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [Jenkins Configuration as Code](https://www.jenkins.io/projects/jcasc/)
