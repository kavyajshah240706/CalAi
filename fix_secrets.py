import os
import subprocess

def run_cmd(cmd, input_data):
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    out, err = process.communicate(input=input_data.encode('utf-8'))
    if process.returncode != 0:
        print(f"Error: {err.decode('utf-8')}")
    else:
        print(f"Success: {out.decode('utf-8')}")

def update_secrets():
    gcloud_path = r"C:\Users\Kavya Shah\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    
    with open('f:/CalAi/.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip()
            
            # We only want to update secrets that are used in Cloud Run
            if key in ['DATABASE_URL', 'GOOGLE_API_KEY', 'FIRECRAWL_API_KEY', 'ADMIN_PASSWORD']:
                print(f"Updating secret: {key}")
                cmd = f'"{gcloud_path}" secrets versions add {key} --data-file=-'
                run_cmd(cmd, val)

if __name__ == "__main__":
    update_secrets()
