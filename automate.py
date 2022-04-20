from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import git
import hmac
import time
import subprocess


# take environment variables from .env
load_dotenv()
RUN_CMD = os.getenv('RUN_CMD')
LOCAL_GIT_FOLDER_PATH = os.getenv('LOCAL_GIT_FOLDER_PATH')
GIT_REPO_SSH = os.getenv('GIT_REPO_SSH')

app = Flask(__name__)

@app.route('/update_server', methods=['POST'])
def webhook():
	try:
		# get the Github signature from the request header
		header_signature = request.headers.get('X-Hub-Signature')

		# pass request data and signature to verify function
		if verify_signature(request.get_data(), header_signature):
			# Check if the repo exist, otherwise clone it
			if not os.path.exists(LOCAL_GIT_FOLDER_PATH) or not os.path.exists(LOCAL_GIT_FOLDER_PATH + '.git'):
				print("Path does not exist, cloning repo")
				os.system('cd '+LOCAL_GIT_FOLDER_PATH)
				git.Git().clone(GIT_REPO_SSH)
			else:
				print("Path exists, pulling repo")
				os.system('cd '+LOCAL_GIT_FOLDER_PATH)
				git.Git(GIT_REPO_SSH).pull()
			time.sleep(2)
			print("Running command: " + RUN_CMD)
			# go to the LOCAL_GIT_FOLDER_PATH and run the command
			output = subprocess.check_output("cd "+LOCAL_GIT_FOLDER_PATH+" && "+RUN_CMD, shell=True)
			print("Commands executed")
			print(output)
			return jsonify({'message': 'success'}), 200
		else:
			print("Signature does not match")
			return jsonify({'message': 'failure', 'description': 'Signature does not match'}), 404
	except Exception as e:
		print(e)
		return jsonify({'message': 'failure', 'description':str(e)}), 404

def verify_signature(request_data, header_signature):
	secret_key = os.environ.get('GITHUB_WEBHOOK_SECRET')

	if not header_signature:
		return False

	# separate the signature from the sha1 indication
	sha_name, signature = header_signature.split('=')
	if sha_name != 'sha1':
		return False

	# create a new hmac with the secret key and the request data
	mac = hmac.new(secret_key.encode(), msg=request_data, digestmod='sha1')
	# verify the digest matches the signature
	if hmac.compare_digest(mac.hexdigest(), signature):
		return True

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0")
