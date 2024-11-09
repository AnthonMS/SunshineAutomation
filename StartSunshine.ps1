# Enable the Virtual Display Driver
$device = Get-PnpDevice | Where-Object { $_.HardwareID -eq 'root\iddsampledriver' }
Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false

# Capture output in array of strings
$output = & "C:\Program Files\Sunshine\tools\dxgi-info.exe"

# Search for 'Output Name' and capture matched lines
$matches = $output | Select-String -Pattern '^\s*Output Name\s*:\s*\\\\.\\DISPLAY\d*'

# Select the last match (if any) and extract the value from captured group
$lastOutputName = ($matches[-1].Line -replace '^\s*Output Name\s*:\s*', '').Trim()

# Define the config file path
$configFilePath = "C:\Program Files\Sunshine\config\sunshine.conf"

# Read the content of the file and remove empty lines
$fileContent = Get-Content -Path $configFilePath | Where-Object { $_.Trim() -ne '' }

# Check if output_name exists in the file, add it if it doesn't or change it if it does
if ($fileContent -match '^output_name\s*=\s*') {
    # Replace the existing output_name value with the new value
    $fileContent = $fileContent -replace '^output_name\s*=\s*.*$', "output_name = $lastOutputName"
} else {
    # Append the new output_name at the end of the file
    $fileContent += "output_name = $lastOutputName"
}

# Write the updated content back to the file
$fileContent | Out-File -FilePath $configFilePath -Force -Encoding UTF8

# Start the Sunshine Service
Start-Service -Name 'Sunshine Service'


# Ensure the script exits
exit