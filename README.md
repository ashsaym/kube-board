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
- **User-Friendly Interface**: Intuitive UI designed for both beginners and experienced users

## Installation

### Prerequisites

- Python 3.8+
- Django 5.1+
- Kubernetes Python Client 32.0+
- A Kubernetes cluster with a valid kubeconfig file

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ashsaym/kube-board.git
   cd kube-board
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a kubeConfigs directory and add your kubeconfig files:
   ```bash
   mkdir -p kubeConfigs
   cp /path/to/your/kubeconfig.yaml kubeConfigs/
   ```

4. Run the development server:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

5. Access the dashboard at http://localhost:8000

## Usage

1. Select a kubeconfig file from the dropdown in the top navigation bar
2. Navigate through the different resource types using the navigation menu
3. Click on individual resources to view detailed information
4. Use the generated kubectl commands for common operations
5. Stream logs from pods directly in the browser

## Development

### Project Structure

- `appConfig/`: Main application configuration
- `kubeBoard/`: Dashboard core functionality
- `kubePods/`: Pod management
- `kubeDeployments/`: Deployment management
- `kubeConfigMaps/`: ConfigMap management
- `kubeSecrets/`: Secret management
- `kubeEvents/`: Event monitoring
- `kubeIngress/`: Ingress management
- `kubeLogs/`: Log streaming
- `static/`: Static files (CSS, JS)
- `templates/`: HTML templates

### Adding New Features

1. Create a new Django app for the resource type:
   ```bash
   python manage.py startapp kubeNewResource
   ```

2. Add the app to `INSTALLED_APPS` in `appConfig/settings.py`

3. Create views, templates, and URL patterns for the new resource

4. Add navigation links in the base template

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Kubernetes](https://kubernetes.io/)
- [Django](https://www.djangoproject.com/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Bootstrap](https://getbootstrap.com/)
- [Tabulator](http://tabulator.info/)