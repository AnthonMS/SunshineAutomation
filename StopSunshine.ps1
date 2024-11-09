# Disable Virtual Display Adapter
$device = Get-PnpDevice | Where-Object { $_.HardwareID -eq 'root\iddsampledriver' }
Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false

# Stop Sunshine Service
Stop-Service -Name 'Sunshine Service'


# Ensure the script exits
exit