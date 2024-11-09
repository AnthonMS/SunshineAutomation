### Create Windows Task that Enables Virtual Display Adapter, updates Sunshine config and starts Sunshine.

1. Create powershell script `StartSunshine.ps1` with content: (**Change directories to match your setup if needed**)
    ```powershell
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
    ```
2. Press Win+R and open Task Scheduler `taskschd.msc`
3. Create a New Task
	- In the Task Scheduler window, on the right side, click Create Task (**not "Create Basic Task"**).
	- **Name**: "Sunshine Start"
	- **Description**: 
    ```
    Enables Idd Virtual Display Adapter.
    Updates Sunshine Configuration
    Starts Sunshine using the Sunshine Service
	```
	- **Enable**: Run with highest privileges
	- **Configure for**: Windows 10
4. Add a new action.
    - **Action**: Choose Start a program.
    - **Program/script**: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
    - **Add arguments**: -ExecutionPolicy Bypass -File "C:\Users\Anthon\Scripts\powershell\StartSunshine.ps1"
5. Set Settings:
	- **Stop the task if it runs longer than**: 1 minute
	- **If the running task does not end when requested, force it to stop**: Enabled
	- **Bottom Dropdown**: Stop the existing instance
		

### Create Windows Task that Disables Virtual Display Adapter and stops Sunshine.

1. Create powershell script `StopSunshine.ps1` with content: 
    ```powershell
    # Disable Virtual Display Adapter
    $device = Get-PnpDevice | Where-Object { $_.HardwareID -eq 'root\iddsampledriver' }
    Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false

    # Stop Sunshine Service
    Stop-Service -Name 'Sunshine Service'
    ```
2. Press Win+R and open Task Scheduler `taskschd.msc`
3. Create a New Task
	- In the Task Scheduler window, on the right side, click Create Task (**not "Create Basic Task"**).
	- **Name**: "Sunshine Stop"
	- **Description**: 
        ```
        Disables Idd Virtual Display Adapter.
        Stops Sunshine using the Sunshine Service
        ```
	- **Enable**: Run with highest privileges
	- **Configure for**: Windows 10
4. Add a new action.
    - **Action**: Choose Start a program.
    - **Program/script**: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
    - **Add arguments**: -ExecutionPolicy Bypass -File "C:\Users\Anthon\Scripts\powershell\StopSunshine.ps1"
5. Set Settings:
	- **Stop the task if it runs longer than**: 1 minute
	- **If the running task does not end when requested, force it to stop**: Enabled
	- **Bottom Dropdown**: Stop the existing instance

Notes:  
There are 2 tasks "StartSunshine.xml" and "StopSunshine.xml". These files can be modified directly and imported into Task Scheduler. You can change the arguments and other settings directly in here before importing.  
But if tasks are created directly in Task Scheduler, you can change the "Stop the task if it runs longer than" to "1 minute" manually. This way it doesn't run longer than 1 minute, before stopped.


### Create commands in Hass.Agent:
Right Click Hass.Agent icon in taskbar and click Manage Commands.
1. Add New Command:
    - **Selected Type**: CustomCommand  
    - **Entity Type**: Button  
    - **Name**: StartSunshine  
    - **Command**: schtasks /run /tn "Start Sunshine"

2. Add New Command:  
    - **Selected Type**: CustomCommand
    - **Entity Type**: Button
    - **Name**: StopSunshine
    - **Command**: schtasks /run /tn "Stop Sunshine"

### Create Sunshine sensor in Hass.Agent:
Right Click Hass.Agent icon in taskbar and click Manage Sensor.
1. Add New Sensor:
	- **Type**: ProcessActive
	- **Name**: SunshineActive
	- **Update** every: 10 seconds
	- **Process**: sunshine.exe



### Home Assistant UI Example
In Home Assistant UI I am using the my-cards bundle, and I have created a button like this in my Computer Popup UI.
```yaml
- type: custom:my-button
  label: 
      text: Sunshine
  icon: mdi:cog
  styles:
      card:
      - height: auto
      - cursor: 'default'
      button:
      - 'aspect-ratio': 'initial'
      - 'margin-top': '2px'
      - 'margin-left': '2px'
      - 'margin-bottom': '2px'
      - 'border-radius': '5px'
      - 'box-shadow': '0px 4px 8px rgba(0, 0, 0, 0.2)'
      - background: 'rgba(32,33,36, .25)'
      - padding: '1px 5px'
      - cursor: 'pointer'
  stats:
      show: true
      text: >
      [[[
          if (states["sensor.mycomputer_sunshineactive"].state > 0) return "Active";
          else return "Inactive";
      ]]]
  buttons:
      show: true
      vertical: false
      button0:
      show: true
      text: >
          [[[
          if (states["sensor.mycomputer_sunshineactive"].state > 0) return "Stop Sunshine";
          else return "Start Sunshine";
          ]]]
      tap_action:
          action: call-service
          service: >
              [[[
              if (states["sensor.mycomputer_sunshineactive"].state > 0) return "script.stop_sunshine";
              else return "script.start_sunshine";
              ]]]
```

And the scripts looks like this:
I turn on and off my monitor with a smart switch so the monitor isn't causing any trouble with programs being opened on wrong monitor when remoted in using Moonlight. The monitor is always on otherwise since the sleep mode on it use the same amount of power as if it was off anyway.
```yaml
start_sunshine:
  sequence:
    - service: switch.turn_off
      entity_id: switch.computer_monitor
    - service: button.press
      entity_id: button.anthons_beast_startsunshine

stop_sunshine:
  sequence:
    - service: switch.turn_on
      entity_id: switch.computer_monitor
    - service: button.press
      entity_id: button.anthons_beast_stopsunshine
```