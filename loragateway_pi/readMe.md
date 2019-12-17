In order to connect to the gateway, you have 2 options:
- Ethernet @ address 192.168.10.10
	- Make sure your computers port is configured to 192.168.10.x

- Local wireless network

To view the Loraserver that is running, just go to: address:8080/ in your browser.
	- Username: admin
	- Password: admin

LoraServer notes:
  * To change the address for what the Loraserver is forwarding to, go to "App/Integrations" and click on "HTTP", you can change the server there.
  * To change the payload that is being decoded, go to "App/Application Configuration" and change the custom JavaScript codec function.
  * To view device data, click on the device name and go to "Device Data" tab on the top.

  * When adding a NEW Lora node:
    - Use "DeviceProfile\_ABP"
    - Have the LoraServer make a Device EUI, you will define that through code.

Other useful notes:
  * To change various settings about the LoraServer (region, etc), use "sudo gateway-config"
  * Here is [the link](https://www.adafruit.com/product/4327) to the product, with product guides in the description.
