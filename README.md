I2C OLED Controller for Raspberry Pi
====================================

Python library to enable 128x32 pixel OLED for Raspberry Pi (both 32 and 64-bit). This works as a standalone service and can run on a standard Raspberry Pi running Raspian.

<a href="https://www.buymeacoffee.com/jedimeat" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/white_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>

[![license-badge]][license-url]
[![release][release-badge]][release-url]
<br>
<br>

## Some Teaser Screenshots

| Welcome | HA Splash | CPU | Memory | Storage | Network | Exit Screen |
|-----------|-----------|-----------|-----------|---------------|---------------|---------------|
| ![Welcome][welcome-url] | ![Splash][splash-url] | ![CPU Stats][cpu-stats-url] | ![RAM Stats][ram-stats-url] | ![Storage Stats][storage-stats-url] | ![Network Stats][network-stats-url] | ![Exit][exit-url] |
|  | | ![CPU Stats][cpu-stats-url-icon] | ![RAM Stats][ram-stats-url-icon] | ![Storage Stats][storage-stats-url-icon] | ![Network Stats][network-stats-url-icon] | |
|  | | ![CPU Stats][cpu-stats-url-compact] | ![RAM Stats][ram-stats-url-compact] | ![Storage Stats][storage-stats-url-compact] | ![Network Stats][network-stats-url-compact] | |

## Custom Screen & Static Text Variables

As well as the above screens, you can configure a static custom screen which can be fixed or animated.

If the configured text is greater than the screen size, it will scroll across the screen unless you configure it to display as lines.

Scrolling animations also supports configurable apmlitude enabling the text to wave up and down as it scrolls.

![Exit][exit-url]
![Welcome][welcome-url]

This screen can take variables to help personalise your view:
```
"Static_Screen_Text": "Today is {datetime}, running hassio verion {hassio.os.version} on {hostname} with IP {ip}"
```
The following variables are supported
| Variable               | Description |
|------------------------|-------------|
| {datetime}             | Displays the current datetime based on the defined format specified in the ```DateTime_Format``` config option. |
| {hostname}             | Displays the current hostname of the host device |
| {ip}                   | Displays the host device IP |
| {hassio.info.property} | Fetches a specified property from Home Assistants supervisor API (e.g. http://supervisor/os/info). You can state the namespace and property which will populate with the responding value. This must be fixed with hassio first, followed by the namespace (e.g. os, network etc), then the property e.g. hassio.os.latest_version will call http://supervisor/os/info and display the ```latest_version``` value. |

<br>
<br>

Adafruit Python SSD1306
=======================
**This addon leverages the original [Adafruit Python SSD1306](https://github.com/adafruit/Adafruit_Python_SSD1306) and [GPIO](https://github.com/adafruit/Adafruit_Python_GPIO) libraries, which have been deprecated. However, I have taken the nessassary parts out of this and bundled them into this I2C module avoiding the need for GPIO and relying on the Raspberry Pi's I2C setup.**

Original Repo: https://github.com/adafruit/Adafruit_Python_SSD1306

Originally designed specifically to work with the Adafruit SSD1306-based OLED displays ----> https://www.adafruit.com/categories/98

Adafruit invests time and resources providing this open source code, please support Adafruit and open-source hardware by purchasing products from Adafruit!
<br>
<br>

Home Assistant Support
======================
This repository has been broken out to work as a standalone service and will work on a standard Raspberry Pi running Raspian.

Any screens which are dependent on Home Assistant (e.g. ```Splash```) will be automatically disabled

Home Assistant variant of this build can be accessed from [HomeAssistant_Addons](https://github.com/crismc/homeassistant_addons)
<br>
<br>

Hardware Setup
===============
You can use 0.91 Inch 128X32 I2C module, as long as it is registered on /dev/i2c-1 which is the Rasperry Pi default.

I purchased this [MakerHawk I2C OLED Display Module I2C Screen Module 0.91" 128X32 I2C](https://www.amazon.co.uk/gp/product/B07BDFXFRK/ref=ppx_yo_dt_b_asin_title_o07_s00?ie=UTF8&psc=1)

Pin setup:
--------------
```
- PIN1 : Power (3.3V / VCC)
- PIN3: SDA (I2C Data)
- PIN5: SCL (I2C Clock)
- PIN14: Ground (0V)
```

Enable I2C on the Raspberry Pi
```
sudo raspi-config
# Interface Options > I2C
```

One-Step Automated Install
----------------
Those who want to get started quickly and conveniently may install the RPI_I2C_OLED using the following command:
```
curl -sSL https://raw.githubusercontent.com/crismc/rpi_i2c_oled/v1.0.4/basic-install.sh | sudo bash
```

This will download the latest release, and install it as a service. Once run, you can control the ```oled``` service by the following:
```
sudo service oled start
sudo service oled stop
sudo service oled restart
```

Installing From Source
------------------------
Initial apt-get installs:
```
sudo apt-get install i2c-tools git vim
```

Test I2C device is working:
```
$ i2cdetect -y 1
```

Install Python3 dependencies
```
sudo apt-get install python3-dev python3-smbus python3-pil
```

Checkout this code
```
git clone git@github.com:crismc/rpi_i2c_oled.git
cd rpi_i2c_oled
```

Test OLED
```
cd rpi_i2c_oled
python3 display.py
```

Create a service
-----------------

Copy the repo file to /etc:
```
sudo cp -ri ../rpi_i2c_oled /etc
```

Create a sym link of the service file in /etc/systemd/system, and reload it
```
sudo ln -s /etc/rpi_i2c_oled/oled.service /etc/systemd/system/oled.service
sudo systemctl daemon-reload
```

Test it out
```
sudo service oled start
sudo service oled stop
sudo service oled restart
```

Start on boot
```
sudo systemctl enable oled.service
```

## Configuration Options

You can modify the display of the content by editing the ```options.json``` file.

By default the ```options.json``` is loaded from the same directory as the ```display.py```.

Note: The keys are case **in**sensitive

If you want to change this location, simply pass in the path to the desired config using the flags -c or --config:

```
python3 display.py -c /path/to/options.json
```
or
```
python3 display.py --config /path/to/options.json
```

| Name                 | Type    | Requirement  | Description                                            | Default             |
| ---------------------| ------- | ------------ | -------------------------------------------------------| ------------------- |
| i2c_bus     | int  | **Required** | I2C bus number. /dev/i2c-[bus number]                  | `1`                 |
| Temperature_Unit     | string  | **Required** | Display the CPU temperature in C or F                  | `C`                 |
| Rotate     | int  | **Optional** | Rotates the screen by the number of degrees provided counter clockwise around its centre (e.g. 180 displays the screen upside down).     | 0                 |
| Show_Icons | boolean | **Optional** | Show icons for each screen | `true` |
| Show_Hint | boolean | **Optional** | Show hint for each screen (instead of icon) | `false` |
| Compact   | boolean | **Optional** | Show data in a more compact form | `false` |
| Default_Duration     | int     | **Required** | How long in seconds to display each screen by default. Ignored if specified on specific screen  | `10`                |
| DateTime_Format      | string  | **Optional** | Format of the ```{datetime}``` static text variable  | `%d/%m/%Y %H:%M:%S` |
| Graceful_Exit_Text   | string  | **Optional** | Text to display when the service is exited. Accepts same variables as the custom screen.  | `Exited at {datetime}` |
| Static_Screen_Text   | string  | **Optional** | Text to display when the ```Show_Static_Screen``` is enabled. Accepts all static text variables.  | `Hassio verion {hassio.os.version} on {hostname} with IP {ip}` |
| Static_Screen_Text_NoScroll  | boolean | **Optional** | Disable the scrolling animation if the static text its too large to fit. If set to true, make a best effort to stack the text as centered lines        | `false`              |
| Scroll_Amplitude  | int | **Optional** | Amount of wave action the scrolling animation text has. The bigger the number, the bigger the wave. | `6`              |
| Show_Static_Screen  | boolean | **Required** | Show the static screen with the specified custom text         | `false`              |
| Show_Welcome_Screen  | boolean | **Required** | Show the animated Welcome to `hostname` screen         | `true`              |
| Welcome_Screen_Text  | string | **Optional** | Text to display when the ```Show_Welcome_Screen``` is enabled. Accepts all static text variables.         | `Welcome to {hostname}`              |
| Show_Splash_Screen  | boolean | **Required** | Show the Home Assistant core and version screen. I you're not using Home Assistant, leave this false         | `false`              |
| Show_Network_Screen  | boolean | **Required** | Show the Network Information screen         | `true`              |
| Show_CPU_Screen  | boolean | **Required** | Show the CPU Information screen         | `true`              |
| Show_Memory_Screen  | boolean | **Required** | Show the Memory Information screen         | `true`              |
| Show_Storage_Screen  | boolean | **Required** | Show the Storage Information screen         | `true`              |
| Screenshot  | boolean or string | **Optional** | Saves a screenshot of the screen to the specified path, or to './img/examples/' if set to True         | `false`              |
| *_Screen_Limit    | int | **Optional** | Number of times to show the screen in the cycle. Once limit is reached, display will no longer appear                            | null              |
| *_Screen_Duration | int | **Optional** | How long in seconds to display the screen              | `10`              |

<br>
<br>

## Logs & Debugging
As logging is initiated before the party begins, log levels are defined outside of the ```options.json```.

Therefore, to enable debugging, when running ```display.py``` add ```-d``` or ```--debug``` to the command.

e.g.:

```
$ python3 display.py -d
INFO:Config:Loading config: /etc/rpi_i2c_oled/options.json
INFO:Config:Home Assistant is not supported on this instance
INFO:Config:'welcome' limited to 5 iterations
INFO:__main__:'welcome' is being processed
INFO:Screen:'WelcomeScreen' created
INFO:Screen:'WelcomeScreen' rendering
```

<br>
<br>
<br>

## Compatible Hardware (SSD1306 Chips)

Several examples of SSD1306 driven I2C OLED hardware that should work. This was originally designed specifically to work with the Adafruit SSD1306-based OLED displays: https://www.adafruit.com/categories/98

* [Adafruit 128x32 I2C OLED](https://www.adafruit.com/product/931)
* [Adafruit 0.91" 128x32 I2C OLED - STEMMA QT / Qwiic](https://www.adafruit.com/product/4440)
* [Adafruit PiOLED 128x32 OLED Add-on for Raspberry Pi](https://www.adafruit.com/product/3527)

## Credits

* Special thanks to [Gareth Cheyne](https://github.com/garethcheyne/HomeAssistant) for his initial version of this project. After the removal of GPIO support from Home Assistant, the referenced addon no longer worked for me, so I took the initial project apart, and smashed it together with the Adafruit I2C libraries removing the GPIO requirements. Additionally, the original build didn't work on 64-bit versions of the Raspberry Pi, nor would it work as a stand alone service.

* [Tony DiCola](https://github.com/tdicola) ([RIP](https://cascadememorial.com/obituary/659469/Anthony-Charles-Dicola/)) and [Adafruit Industries](https://github.com/adafruit) for initial implementation details.
* [crismc](https://github.com/crismc/)
* Ultronics

## See Also

* [IC2 OLED Home Assistant Add-On](https://github.com/akonkol/homeassistant_addons)
* [Adafruit Python SSD1306 notice to comply with distribution requirement](Adafruit_Notice.md)


<!-- References -->
[release-badge]: https://img.shields.io/github/v/release/crismc/rpi_i2c_oled?style=flat-square
[downloads-badge]: https://img.shields.io/github/downloads/crismc/rpi_i2c_oled/total?style=flat-square
[release-url]: https://github.com/crismc/rpi_i2c_oled/releases
[license-badge]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: https://opensource.org/licenses/MIT

[welcome-url]: /img/examples/welcome.png?raw=true
[cpu-stats-url]: /img/examples/cpu.png?raw=true
[ram-stats-url]: /img/examples/memory.png?raw=true
[storage-stats-url]: /img/examples/storage.png?raw=true
[network-stats-url]: /img/examples/network.png?raw=true
[splash-url]: /img/examples/splash.png?raw=true
[exit-url]: /img/examples/static_goodbye.png?raw=true

[cpu-stats-url-compact]: /img/examples/compact/cpu.png?raw=true
[ram-stats-url-compact]: /img/examples/compact/memory.png?raw=true
[storage-stats-url-compact]: /img/examples/compact/storage.png?raw=true
[network-stats-url-compact]: /img/examples/compact/network.png?raw=true

[cpu-stats-url-icon]: /img/examples/icon/cpu.png?raw=true
[ram-stats-url-icon]: /img/examples/icon/memory.png?raw=true
[storage-stats-url-icon]: /img/examples/icon/storage.png?raw=true
[network-stats-url-icon]: /img/examples/icon/network.png?raw=true
