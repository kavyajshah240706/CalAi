import requests

# Path to your test image
image_path = r'C:\Users\Kavya Shah\Downloads\food_volume_estimation\Screenshot 2025-10-03 002613.png'

# Send request
with open(image_path, 'rb') as f:
    response = requests.post(
        'http://localhost:5000/estimate-volume',
        files={'image': f}
    )

# Print results
print(response.json())