
import paramiko

def start_server():
    # Raspberry Pi SSH credentials
    hostname = "raspberrypi.local"  # Replace with your Raspberry Pi's IP address
    username = "cheth"             # Replace with your Raspberry Pi's username
    password = "root"      # Replace with your Raspberry Pi's password

    # Path to the Python script on the Raspberry Pi
    remote_script_path = "/home/cheth/camera_server.py"

    # Command to execute the Python script on the Raspberry Pi
    command = f"python {remote_script_path}"

    # Create an SSH client
    ssh = paramiko.SSHClient()

    # Automatically add the Raspberry Pi's host key (for first-time connections)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the Raspberry Pi
        print(f"Connecting to {hostname}...")
        ssh.connect(hostname, username=username, password=password)
        print("Connected successfully!")

        # Execute the command to run the Python script
        print(f"Running script: {remote_script_path}")
        stdin, stdout, stderr = ssh.exec_command(command)

        # # Print the output of the script
        # print("Script output:")
        # for line in stdout:
        #     print(line.strip())

        # # Print any errors
        # print("Script errors:")
        # for line in stderr:
        #     print(line.strip())

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the SSH connection
        ssh.close()
        print("SSH connection closed.") 
