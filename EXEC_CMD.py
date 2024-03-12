import csv
import paramiko
import logging
from getpass import getpass
import time
from io import TextIOWrapper

def setup_ssh_connection(host, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=username, password=password)
        return client
    except paramiko.AuthenticationException:
        error_msg = f"Authentication failed for {host}. Please check your credentials."
        logging.error(error_msg)
        print(error_msg)
    except Exception as e:
        error_msg = f"Error connecting to {host}: {e}"
        logging.error(error_msg)
        print(error_msg)
    return None

def execute_ssh_commands(client, command_file, output_file):
    try:
        transport = client.get_transport()
        channel = transport.open_session()

        if isinstance(output_file, TextIOWrapper):
            output_file = output_file.name

        # Start an interactive shell
        channel.get_pty()
        channel.invoke_shell()

        # Read commands from the specified file
        with open(command_file, 'r') as file:
            commands = file.readlines()

            # Execute each command
            for command in commands:
                command = command.strip()

                # Send command to the shell
                channel.send(command + '\n')

                # Wait for the command to finish
                time.sleep(0.2)  # Adjust the sleep duration as needed

                # Read the output
                output = channel.recv(4096).decode('utf-8')

                # Print the output to the console
                print(f"Output for command '{command}':\n{output}")

                # Write the command and output to the output file
                with open(output_file, 'a') as out_file:
                    out_file.write(f"Host: {client.get_transport().getpeername()[0]} | Command: {command}\nOutput:\n{output}\n{'='*50}\n")

    except Exception as e:
        logging.error(f"Error executing commands: {e}")

def main():
    logging.basicConfig(filename='ssh_script.log', level=logging.INFO)

    csv_file_path = input("Enter the path to the CSV file containing host information: ")
    output_file_path = input("Enter the path to the output file: ")
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            username = input("Enter your SSH username: ")
            password = getpass("Enter your SSH password: ")

            # Open the output file outside the loop to share it among all hosts
            with open(output_file_path, 'w') as shared_output_file:
                for row in reader:
                    host = row['host']
                    command_file = row['command_file']

                    try:
                        ssh_client = setup_ssh_connection(host, username, password)
                        execute_ssh_commands(ssh_client, command_file, shared_output_file)
                    finally:
                        ssh_client.close()

    except FileNotFoundError:
        logging.error(f"Error: File '{csv_file_path}' not found.")
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()
