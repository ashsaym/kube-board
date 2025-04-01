# Kubernetes Dashboard

A comprehensive web-based UI for managing and monitoring Kubernetes clusters.

## Features

- **Cluster Overview**: Get a quick overview of your cluster's health and resources
- **Resource Management**: View and manage various Kubernetes resources:
  - Pods
  - Deployments
  - ConfigMaps
  - Secrets
  - Ingresses
  - Events
  - And more...
- **Multiple Cluster Support**: Switch between different Kubernetes clusters using kubeconfig files
- **Command Generation**: Automatically generate kubectl commands for common operations
- **Resource Details**: Detailed views of all Kubernetes resources with relevant information
- **Logs Streaming**: Stream logs from pods in real-time
- **User-Friendly Interface**: Clean, light-themed UI designed for both beginners and experienced users

## Quick Start

### Prerequisites

- Python 3.8+
- Django 5.1+
- Kubernetes Python Client 32.0+
- A Kubernetes cluster with a valid kubeconfig file

### Run with Docker

```bash
# Build and run with a single command
docker run -p 8000:8000 \
  -v ~/.kube/config:/app/kubeConfigs/config \
  ghcr.io/ashsaym/kube-board:latest

# Or build locally
docker build -t kube-board .
docker run -p 8000:8000 -v ~/.kube/config:/app/kubeConfigs/config kube-board
```

Access at http://localhost:8000

### Run Locally

```bash
# Clone and install
git clone https://github.com/ashsaym/kube-board.git
cd kube-board
pip install -r requirements.txt

# Setup kubeconfig
mkdir -p kubeConfigs
cp ~/.kube/config kubeConfigs/

# Run
python manage.py runserver 0.0.0.0:8000
```

## Configuration

### Environment Variables

- `KUBECONFIG_DIR`: Directory containing kubeconfig files (default: `./kubeConfigs`)
- `DJANGO_DEBUG`: Set to "True" for development mode (default: "False")
- `DJANGO_SECRET_KEY`: Django secret key (default: auto-generated)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts (default: "*")

### Development Mode

```bash
export DJANGO_DEBUG=True
export KUBECONFIG_DIR=/path/to/kubeconfigs
python manage.py runserver 0.0.0.0:8000 --reload
```

## Project Structure

```
kube-board/
├── appConfig/                 # Main application configuration
│   ├── settings.py           # Django settings
│   ├── urls.py               # Main URL routing
│   └── wsgi.py              # WSGI configuration
├── kubeBoard/                # Dashboard core functionality
├── kubePods/                 # Pod management
├── kubeDeployments/         # Deployment management
├── kubeConfigMaps/          # ConfigMap management
├── kubeSecrets/             # Secret management
├── kubeEvents/              # Event monitoring
├── kubeIngress/             # Ingress management
├── kubeLogs/                # Log streaming
├── static/                  # Static files
├── templates/               # HTML templates
└── manage.py               # Django management script
```

## Contributing

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
5. Make changes and test:
   ```bash
   python manage.py test
   ```
6. Submit a pull request

## Troubleshooting

### Common Issues

1. **No kubeconfig files found**
   ```bash
   ls -l kubeConfigs/
   chmod 600 kubeConfigs/*
   ```

2. **Connection refused**
   ```bash
   # Verify kubeconfig
   KUBECONFIG=kubeConfigs/your-config kubectl get nodes
   ```

3. **Port in use**
   ```bash
   # Check port usage
   lsof -i :8000
   # Use different port
   python manage.py runserver 0.0.0.0:8001
   ```

### Security Best Practices

1. **Kubeconfig Security**
   - Use 600 permissions on kubeconfig files
   - Prefer service account tokens
   - Rotate credentials regularly

2. **Production Deployment**
   - Enable HTTPS
   - Set secure `DJANGO_SECRET_KEY`
   - Configure `ALLOWED_HOSTS`
   - Use reverse proxy
   - Implement authentication

## License

MIT License - see the LICENSE file for details.

## Acknowledgements

- [Kubernetes](https://kubernetes.io/)
- [Django](https://www.djangoproject.com/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Bootstrap](https://getbootstrap.com/)
- [Tabulator](http://tabulator.info/)