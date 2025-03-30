# Kubernetes Dashboard

A comprehensive web-based UI for managing and monitoring Kubernetes clusters with Material Design and real-time updates.

## Features

- **Modern Material Design UI**: Clean, intuitive interface with dark mode by default and light mode toggle
- **Cluster Overview**: Get a quick overview of your cluster's health and resources
- **Resource Management**: View and manage various Kubernetes resources:
  - Pods
  - Deployments
  - StatefulSets
  - DaemonSets
  - Jobs
  - CronJobs
  - ConfigMaps
  - Secrets
  - Ingresses
  - Network Policies
  - Storage Classes
  - And more...
- **Multiple Cluster Support**: Dynamically switch between different Kubernetes clusters using kubeconfig files
- **Command Generation**: Automatically generate kubectl commands for common operations with copy-to-clipboard functionality
- **Resource Details**: Detailed views of all Kubernetes resources with relevant information
- **Logs Streaming**: Stream logs from pods in real-time
- **Real-time Updates**: WebSocket support for live resource monitoring
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Hover Command Tips**: View kubectl commands by hovering over resource names

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

4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

5. Run the development server:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

6. Access the dashboard at http://localhost:8000

## Usage

1. Select a kubeconfig file from the dropdown in the top navigation bar
2. Navigate through the different resource types using the navigation menu
3. Click on individual resources to view detailed information
4. Use the generated kubectl commands for common operations (hover over resources to see commands)
5. Stream logs from pods directly in the browser
6. Toggle between dark and light themes using the theme button in the navigation bar

## Development

### Project Structure

- `appConfig/`: Main application configuration and settings
- `kubeBoard/`: Dashboard core functionality and WebSocket consumers
- `kubePods/`: Pod management and log streaming
- `kubeDeployments/`: Deployment management
- `kubeStatefulSets/`: StatefulSet management
- `kubeDaemonSets/`: DaemonSet management
- `kubeJobs/`: Job management
- `kubeCronJobs/`: CronJob management
- `kubeConfigMaps/`: ConfigMap management
- `kubeSecrets/`: Secret management
- `kubeEvents/`: Event monitoring
- `kubeIngress/`: Ingress management
- `kubeNetworkPolicies/`: Network Policy management
- `kubeStorageClasses/`: Storage Class management
- `static/`: Static files (CSS, JS)
- `templates/`: HTML templates
- `kubeConfigs/`: Directory for kubeconfig files

### Adding New Features

1. Create a new Django app for the resource type:
   ```bash
   python manage.py startapp kubeNewResource
   ```

2. Add the app to `INSTALLED_APPS` in `appConfig/settings.py`

3. Create views, templates, and URL patterns for the new resource

4. Add navigation links in the base template

### WebSocket Support

The application uses Django Channels for WebSocket support, enabling real-time updates for resources. To implement real-time updates for a new resource type:

1. Add the resource type to the WebSocket consumer in `kubeBoard/consumers.py`
2. Add the data-realtime attribute to the resource container in the template
3. Implement the updateResourceDisplay function in the JavaScript

## Features Added in This Version

- Material Design UI with dark theme by default
- Theme toggle between dark and light modes
- Improved navigation with dropdown menus for resource categories
- WebSocket support for real-time updates
- Storage Classes management module
- Kubectl command hover tooltips
- Responsive design improvements
- Consistent styling across all pages
- Enhanced error handling and user feedback

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Kubernetes](https://kubernetes.io/)
- [Django](https://www.djangoproject.com/)
- [Django Channels](https://channels.readthedocs.io/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Bootstrap](https://getbootstrap.com/)
- [Tabulator](http://tabulator.info/)
- [Material Design](https://material.io/design)