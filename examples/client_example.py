
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
# needed for importing from parent directory




from server_client import Client
client = Client(autostart=False, input_type="keyboard", add_switch_hotkey=True, logging=True)
client.start()


