Sunshine automation script that I use from Home Assistant to start/stop sunshine and enable/disable the virtual display driver and update sunshine settings to reflect the newly enabled virtual display driver.


Sunshine automation setup.

You should create a sunshine.env file located in the same directory as sunshine.py
This config file should have these keys:

```
DEVCON_PATH=C:\Program Files (x86)\Windows Kits\10\Tools\10.0.22621.0\x86
SUNSHINE_PATH=C:\Program Files\Sunshine\
SUNSHINE_SHORTCUT=C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Sunshine\Sunshine.lnk
SUNSHINE_WEB=https://localhost:47990
SUNSHINE_AUTH=

# Not needed, but will be used if present
ENCODER=nvenc
NVENC_PRESET=1
```

You should obviously change the variables that are custom for each user. But this is mostly just the SUNSHINE_AUTH key. That is found by navigating to the sunshine webui after launching it. Open Developer tools with F12 and go to network tab. Clear the history to get a better overview of the new requests. Go to configratuion->general and change the Log Level temporarily to whatever and click save.
You should now see a new network request in the list, you should be able to find the auth token by marking it in the list and checking the headers of that request. There is a key 'Authorization: Basic LKJlskdf0s89jlksfhgLJKH90lnnl='
The SUNSHINE_AUTH should bet set to this 'SUNSHINE_AUTH=LKJlskdf0s89jlksfhgLJKH90lnnl='

Here you can see the different configuration fields name for the API if you want to set the encoder to something other than nvenc. If you want to add other fields to the auto configuration, it can be done in the update_sunshine_config function with a code snippet looking like this:
```
if os.getenv("NVENC_PRESET"):
	data_dict["nvenc_preset"] = os.getenv("NVENC_PRESET")
```

Just make sure to add the config keys before this line `data = json.dumps(data_dict)`



When first running the sunshine.py script, run the command 'python3 sunshine.py test'. This will simply install the missing dependencies. The only dependency you need to install manually, if you don't have it already, is dotenv. That is done with the command `pip install python-dotenv`.




But when everything is done, you can now run the command `python3 sunshine.py start` and this will: 
	Close all apps added to the close_apps function. For now only discord. This is to get rid of discord overlay not going away when streaming.
	Start Sunshine if it isn't running already
	Enable Virtual Display Driver 'root\iddsampledriver' if it isn't already
	Update Sunshine config to stream the last display found, which in my case is always the Virtual Display. Let me know if that isn't the case for everyone. And set encoder and nvenc preset if present in env file.
	Then it will restart sunshine to make the new config take effect.
	Then it will run the keyboard shortcut Win+M to minimize all windows so screen is ready to show games!
	
The command `python3 sunshine.py stop` will simply:
	Quit Sunshine completely
	Disable Virtual Display Driver so there isn't an annoying virtual display when actually using PC



To run these commands from Home Assistant I am using Hass.Agent. This is very simple to set up. First open Task Scheduler and create a couple new tasks. These should not be triggered by anything other than manually.
Name the first "Start Sunshine", Enable "Run with highest privliges", create a new action:
	Action: Start a program
	Program/script: C:\Windows\System32\cmd.exe
	Add Arguments (optional): /c python3 C:\Users\Antho\Scripts\python\sunshine_automation\sunshine.py start

Name the second task "Stop Sunshine", Enable "Run with highest privliges", create a new action:
	Action: Start a program
	Program/script: C:\Windows\System32\cmd.exe
	Add Arguments (optional): /c python3 C:\Users\Antho\Scripts\python\sunshine_automation\sunshine.py stop

You obviously need to change the path to the script to wherever you have placed it. I recomment placing it in a location without any spaces in the names.
You can now run these tasks either through ssh if that is what you want, but you can also create Hass.Agent buttons and expose them to HA that way.

Open Hass.Agent and edit Commands, Add a new Command:
	Selected Type: CustomCommand
	Entity Type: Button
	Name: StartSunshine
	Command: schtasks /run /tn "Start Sunshine"
	
Add another Command:
	Selected Type: CustomCommand
	Entity Type: Button
	Name: StopSunshine
	Command: schtasks /run /tn "Stop Sunshine"


You can now store and activate the commands in Home Assistant.


With this setup, I can from anywhere, Turn on my PC, wait for that, Run this StartSunshine command to start sunshine, enable virtual device, automatically set the virtual device in sunshine config and be ready to stream my games without being near the computer.
This could obviously be done by just doing all these things on startup and always having the virtual display enabled so I dont have to change the config every time. But I sincerely hate that the mouse disappears onto another screen that doesn't exist when I'm actually using the PC. And who wants to slow down their startup time because of something you immediately quit when using the PC normally?

To combat the fact that it might still open windows/games on the Main monitor if you leave that on always, is to just use a smart plug for that and "physically" turn it off. Could not find an easy way to change main display by command on windows. Because why would I ever do that Windows? *Sigh*


I have then created a ProcessActive sensor in Hass.Agent 'SunshineActive'. The state will be the number of sunshine processes running on the host.


You can now start the game streaming service through HA.

I would like to add some functionality to Hass.Agent so there is a sensor displaying if the Virtual Display is active, but haven't gotten around to that part yet. I'm busy playing games wherever I want.


This script is nothing fancy, I threw it together very quickly and spend 30 minutes after cleaning the code a bit, adding logging and .env variables. I probably spend the same amount of time writing this as I did on the code. Please let me know if this is something you would like seen better integrated into HA.






In Home Assistant UI I am using the my-cards bundle, I wonder why, and I have created a button like this in my Computer Popup UI.


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


The scripts they are calling are just turning off/on my monitor with a smart plug and pressing the sunshine buttons exposed through Hass.Agent. This way I can start/stop and check the status of sunshine through a single UI Card. My monitor uses next to no power when sleeping, which is why I am controlling it with a smart plug. I have not been able to find a way to switch primary display through scripting or anything. I know it must be possible, maybe through Registtry Keys manually? That seems dangerous.