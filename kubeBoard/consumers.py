import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from appConfig.utils import get_cluster_client
from appConfig.settings import logger
from kubernetes.client.exceptions import ApiException


class KubernetesResourceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time Kubernetes resource updates.
    """
    
    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        """
        # Extract resource type from the URL path
        self.resource_type = self.scope['url_route']['kwargs'].get('resource_type')
        
        if not self.resource_type:
            await self.close(code=4000)
            return
        
        # Create a unique group name for this resource type
        self.group_name = f"k8s_{self.resource_type}"
        
        # Join the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        logger.info(f"WebSocket connection established for {self.resource_type}")
    
    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket connection closed for {self.resource_type} with code {close_code}")
    
    async def receive(self, text_data):
        """
        Called when we receive a text frame from the client.
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'subscribe':
                # Handle subscription to a specific namespace
                namespace = data.get('namespace')
                
                # Store namespace in the consumer instance for later use
                self.namespace = namespace
                
                # Start the background task to fetch resource updates
                asyncio.create_task(self.fetch_resource_updates())
                
                await self.send(text_data=json.dumps({
                    'type': 'subscription_success',
                    'resourceType': self.resource_type,
                    'namespace': namespace
                }))
            
            elif action == 'unsubscribe':
                # Handle unsubscription
                await self.send(text_data=json.dumps({
                    'type': 'unsubscription_success',
                    'resourceType': self.resource_type
                }))
            
            else:
                # Handle unknown action
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f"Unknown action: {action}"
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': "Invalid JSON format"
            }))
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def resource_update(self, event):
        """
        Called when a message is received from the group.
        """
        # Forward the update to the WebSocket
        await self.send(text_data=json.dumps(event))
    
    async def fetch_resource_updates(self):
        """
        Background task to periodically fetch resource updates.
        """
        try:
            # Continue fetching updates until the connection is closed
            while True:
                # Wait for a specified interval (e.g., 5 seconds)
                await asyncio.sleep(5)
                
                # Fetch the resources
                resources = await self.get_resources()
                
                # Send the update to the group
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'resource_update',
                        'resourceType': self.resource_type,
                        'resources': resources
                    }
                )
        
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            logger.info(f"Resource update task cancelled for {self.resource_type}")
        except Exception as e:
            logger.error(f"Error in fetch_resource_updates: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f"Error fetching resource updates: {str(e)}"
            }))
    
    async def get_resources(self):
        """
        Fetch resources from the Kubernetes API.
        This is a placeholder that should be implemented in the actual application.
        """
        # This would be implemented to use the Django views or direct API calls
        # to fetch the resources based on the resource_type and namespace
        
        # For now, return an empty list as a placeholder
        return []