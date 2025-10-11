"""
CalTopo Team API client for map listing and selection.
"""

import logging
from typing import Dict, List, Optional, Any
import requests
import base64

logger = logging.getLogger(__name__)


class CalTopoTeamAPI:
    """CalTopo Team API client."""

    def __init__(self, credential_id: str, secret_key: str):
        """
        Initialize CalTopo Team API client.

        Args:
            credential_id: CalTopo service account credential ID
            secret_key: CalTopo service account secret key
        """
        self.credential_id = credential_id
        self.secret_key = secret_key
        self.base_url = "https://caltopo.com/api/v1"
        self.team_api_url = f"{self.base_url}/team"

        # Set up authentication
        self.auth_header = None
        if credential_id and secret_key:
            self._setup_authentication()

    def _setup_authentication(self):
        """Set up authentication headers for Team API."""
        try:
            # Create basic auth header
            credentials = f"{self.credential_id}:{self.secret_key}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.auth_header = f"Basic {encoded_credentials}"

            logger.info("CalTopo Team API authentication configured")

        except Exception as e:
            logger.error(f"Failed to setup CalTopo Team API authentication: {e}")

    def list_maps(self) -> List[Dict[str, Any]]:
        """
        Retrieve all available CalTopo maps.

        Returns:
            list: List of map information dictionaries
        """
        try:
            if not self.auth_header:
                logger.error("CalTopo Team API not authenticated")
                return []

            headers = {"Authorization": self.auth_header}
            response = requests.get(f"{self.team_api_url}/maps", headers=headers)

            if response.status_code == 200:
                maps_data = response.json()
                logger.info(f"Retrieved {len(maps_data)} maps from CalTopo")
                return maps_data
            else:
                logger.error(f"Failed to list maps: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error listing CalTopo maps: {e}")
            return []

    def get_map_details(self, map_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific map.

        Args:
            map_id: CalTopo map identifier

        Returns:
            dict: Map details or None if not found
        """
        try:
            if not self.auth_header:
                logger.error("CalTopo Team API not authenticated")
                return None

            headers = {"Authorization": self.auth_header}
            response = requests.get(f"{self.team_api_url}/maps/{map_id}", headers=headers)

            if response.status_code == 200:
                map_details = response.json()
                logger.info(f"Retrieved details for map {map_id}")
                return map_details
            elif response.status_code == 404:
                logger.warning(f"Map {map_id} not found")
                return None
            else:
                logger.error(f"Failed to get map details: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting map details for {map_id}: {e}")
            return None

    def test_map_connection(self, map_id: str) -> bool:
        """
        Test connection to a specific map.

        Args:
            map_id: CalTopo map identifier

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if not self.auth_header:
                logger.error("CalTopo Team API not authenticated")
                return False

            headers = {"Authorization": self.auth_header}
            response = requests.get(f"{self.team_api_url}/maps/{map_id}/test", headers=headers)

            if response.status_code == 200:
                logger.info(f"Map {map_id} connection test passed")
                return True
            else:
                logger.error(f"Map {map_id} connection test failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error testing map connection for {map_id}: {e}")
            return False

    def create_map(self, map_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new CalTopo map.

        Args:
            map_data: Map creation data

        Returns:
            str: Created map ID or None if failed
        """
        try:
            if not self.auth_header:
                logger.error("CalTopo Team API not authenticated")
                return None

            headers = {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.team_api_url}/maps",
                json=map_data,
                headers=headers
            )

            if response.status_code == 201:
                created_map = response.json()
                map_id = created_map.get("id")
                logger.info(f"Created new map: {map_id}")
                return map_id
            else:
                logger.error(f"Failed to create map: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating map: {e}")
            return None

    def update_map(self, map_id: str, map_data: Dict[str, Any]) -> bool:
        """
        Update an existing CalTopo map.

        Args:
            map_id: CalTopo map identifier
            map_data: Map update data

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if not self.auth_header:
                logger.error("CalTopo Team API not authenticated")
                return False

            headers = {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }

            response = requests.put(
                f"{self.team_api_url}/maps/{map_id}",
                json=map_data,
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Updated map {map_id}")
                return True
            else:
                logger.error(f"Failed to update map {map_id}: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error updating map {map_id}: {e}")
            return False

    def delete_map(self, map_id: str) -> bool:
        """
        Delete a CalTopo map.

        Args:
            map_id: CalTopo map identifier

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            if not self.auth_header:
                logger.error("CalTopo Team API not authenticated")
                return False

            headers = {"Authorization": self.auth_header}
            response = requests.delete(f"{self.team_api_url}/maps/{map_id}", headers=headers)

            if response.status_code == 204:
                logger.info(f"Deleted map {map_id}")
                return True
            else:
                logger.error(f"Failed to delete map {map_id}: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error deleting map {map_id}: {e}")
            return False

    def get_team_info(self) -> Optional[Dict[str, Any]]:
        """
        Get team information.

        Returns:
            dict: Team information or None if failed
        """
        try:
            if not self.auth_header:
                logger.error("CalTopo Team API not authenticated")
                return None

            headers = {"Authorization": self.auth_header}
            response = requests.get(f"{self.team_api_url}/info", headers=headers)

            if response.status_code == 200:
                team_info = response.json()
                logger.info("Retrieved team information")
                return team_info
            else:
                logger.error(f"Failed to get team info: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting team info: {e}")
            return None
