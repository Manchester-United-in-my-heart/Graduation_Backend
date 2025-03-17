import subprocess

# Path to your JavaScript file
js_file_path = 'test.mjs'

# Command to run the JavaScript file using Node.js
command = f'node {js_file_path}'

# Execute the command and wait for it to complete
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Get the output and error (if any)
stdout, stderr = process.communicate()

# Decode the output and error from bytes to string
stdout = stdout.decode('utf-8')
stderr = stderr.decode('utf-8')

# Print the output and error
print("Output:\n", stdout)
print("Error:\n", stderr)
