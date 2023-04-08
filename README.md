# pfsense-ultimate-config
This project contains the documentation on how to setup your pfSense firewall to route traffic through VPN providers and provide corporate features not found in home networks

## Table of Contents
1. [Features](#features)
2. [Requirements](#requirements)
3. [Before We Start](#before-we-start)
    1. [VPN Provider Information Gathering](#vpn-provider-information-gathering)
4. [Prepare the Virtual Environment](#prepare-the-virtual-environment)
5. [Install Virtual pfSense](#install-virtual-pfsense)
6. [Install Virtual Debian](#install-virtual-debian)
7. [Initial pfSense Setup](#initial-pfsense-setup)
8. [Make Initial pfSense Snapshot](#make-initial-pfsense-snapshot)
9. [Install pfSense 3rd Party Packages](#install-pfsense-3rd-party-packages)
10. [Create CA and Certificates](#create-ca-and-certificates)
11. [OpenVPN Tunnels](#openvpn-tunnels)

## Features
* Secure VPN:
   * VPN aggregation with WAN fail over.
   * OpenVPN with hardware acceleration.
   * Wireguard with hardware acceleration.
   * Details on how to connect to ExpressVPN and NordVPN.
   * Load Balancing.
   * Dedicated connections for media devices to bypass VPN.
   * VPN Passthrough for IKE/IPSEC/OpenVPN.
   * Dial-in VPN Support
   * DNSSEC
* Squid Proxy for site that do no like VPNs:
   * Includes instructions to setup a CA for HTTPS.
   * Includes wpad.dat / wpad.da / proxy.pac configuration via DHCP.
* Custom DHCP options:
   * PXE.
   * Custom NFSroot options for NFSv3/v4.1.
   * Automatic proxy configuration.
* Whitebox instructions for pcengines.ch devices:
   * Firmware Updates.
   * Performance Improvements.
* Containerized PXE boot with netboot.xyz:
   * Includes how to customize windows PE to chainload Win10 and Win11 installs.
   * Includes how to create dynamic NFS root configurations via pfSense that iPXE reads from DHCP information.
   * Includes how to create custom dynamic netboot.xyz menus for iPXE.
* Network Analysis via Traffic Totals.
* TODO:
   * Containerized Network Analysis Reports.
   * Fix proxy configs.
   * Add drivers to WinPE for addition network card support.

## Requirements
* Hardware:
    * whitebox or netgate (not the cheapest!) network appliance
        * I recommend pcengines apu2/3, personally I use an apu2c4 board.
        * If using an old desktop, a second 1gbe nic and labeling the MAC address on the outside so you know which NIC is which later.
* Software:
    * VirtualBox -- https://www.virtualbox.org/wiki/Downloads
    * Docker on a NAS or server, personally I use Synology with DSM 7.1 which already supports Docker as an add-on package.
    * pfSense -- https://www.pfsense.org/download/ -- AMD64 -- ISO
    * A couple LiveCDs -- I use Debian during the setup as WireGuard is _not_ possible to setup in Gentoo quickly.
        * https://www.gentoo.org/downloads/ -- Click on "LiveGUI USB Image"
        * http://debian.osuosl.org/debian-cdimage/11.6.0-live/amd64/iso-hybrid/debian-live-11.6.0-amd64-kde.iso
* Knowledge:
  * A general working understanding of IPV4, protocols and SSL. However, I will do my best to remove the mystery for the otherwise uninitiated.

## Before We Start
The process is to build up a virtual environment using your new configuration we build together so you don't break your internet connection unintentionally. You can use VMware Fusion/Workstation/ESXi or Microsoft HyperV, but I'm going with an open source platform agnostic solution here.<br><br>
I will need you to find a few things before we start.
1. Figure out if your internet provider's WAN configuration, if you don't know it is probably DHCP. Find the WAN MAC Address of your current router and write it down!<br>
![Spoiler alert: If you don't write down current router's MAC address, you are going to have a bad time](images/meme-macaddress.jpeg)
2. Be prepared for configuration corruption and using snapshots of your pfSense install as you tinker with it. Once we create a configuration you are happy with we can export it and apply it to your production environment.
3. Also be prepared that your current VPN provider might suck. You will want to research what VPN providers in your area you want to use, as well as seeing how flexible they are at sending a ton of data through their network.

### VPN Provider Information Gathering
#### ExpressVPN
* Their directions: https://www.expressvpn.com/support/vpn-setup/pfsense-with-expressvpn-openvpn/
    * In my experience, I highly doubt most vpn providers actually try to keep these settings for pfSense updated, familiarize yourself with what they recommend then come back to this page and apply the information they provided with what I know to work.
    * ExpressVPN allows for 2 concurrent connections via OpenVPN (Yes, they say 5 devices, but we're connecting the SAME device twice!), they do not currently allow for WireGuard connections (2023-04-07) as they deem it experimental and not secure yet.
    * You will want the following information from your account page with them:
        * Username / Password
        * TLS OpenVPN Static Key -- in case the one published here is out of date (2023-04-07)
        * Encryption Algorithm -- in case the one published here is out of date (2023-04-07)

#### NordVPN
* NordVPN has directions for both OpenVPN and WireGuard. I will be using WireGuard in this guide for the final product but will provide my last used settings for OpenVPN. If you know how to improve upon them, let me know!
* NordVPN also allows for 2 concurrent connections via OpenVPN, but only just 1 using WireGuard, however the throughput will be a lot higher per connection via WireGuard.
* Setting up WireGuard will require a lot of additional steps to lift the information specific for your connection, we will circle back to this topic after we have Debian running.

## Prepare the Virtual Environment
1. Download your LiveCD and pfSense .iso files.
2. Install VirtualBox.
3. Unpack the pfsense.iso.gz file, I run a mac and the default archiver will not unpack it, use keke or the following command:
    *   ```gzip --decompress pfSense-CE-2.6.0-RELEASE-amd64.iso.gz```
4. Open VirtualBox.
5. Create a new Virtual Machine for pfSense. I emulate the settings of pcengines.ch APU2c4.
![venv-virtualbox-new-pfsense-1.png](images/venv-virtualbox-new-pfsense-1.png)
![venv-virtualbox-new-pfsense-2.png](images/venv-virtualbox-new-pfsense-2.png)
![venv-virtualbox-new-pfsense-3.png](images/venv-virtualbox-new-pfsense-3.png)
    1. Once created, right click on virtual machine and add it to a group so you do not get it confused with your other virtual machines!
    2. Select the virtual machine we just created and click **Settings > Network > Adapter 1**.
    3. Change the attached network to **Bridged Adapter**.
    4. Select the ethernet port that your computer is currently using to connect to your network.
    5. Click **Adapter 2 > Enable Network Adapter**.
    6. Change the attached network to **Internal Network**.
    7. Change the name to **pfSense**.
    8. You should be left with settings like these:
![venv-virtualbox-pfsense-network-1.png](images/venv-virtualbox-pfsense-network-1.png)
![venv-virtualbox-pfsense-network-2.png](images/venv-virtualbox-pfsense-network-2.png)
    9. Make note of the MAC addresses used by virtualbox otherwise you will not know which is which when setting up pfSense.
    10. Once updated, we will create the second virtual machine.
6. Create a new Virtual Machine for gentoo LiveCD, give it enough power that you don't 5 minutes waiting for it to boot, you're not using all those extra cores anyway [=:
![venv-virtualbox-debian-setup-1.png](images/venv-virtualbox-debian-setup-1.png)
![venv-virtualbox-debian-setup-2.png](images/venv-virtualbox-debian-setup-2.png)
![venv-virtualbox-debian-setup-3.png](images/venv-virtualbox-debian-setup-3.png)
    1. Select the virtual machine we just created and click **Settings > Network > Adapter 1**.
    2. Change the attached network to **Internal Network**.
    3. Change the name to **pfSense**.
    4. Save changes.

## Install Virtual pfSense
1. Start the pfsense virtual machine.
    * If you have a Retina display click **View > Virtual Screen 1 > Scale to 200%**.
2. Mash enter through the entire install.
3. Reboot the virtual machine.
    1. It will start the iso again, select from the menu above **Machine > ACPI Shutdown**.
    2. Open settings and navigate **Storage** then the CD icon under Storage Devices, on the right side of the menu click the CD icon again and select **Remove Disk from Virtual Drive**
    3. Restart the virtual machine.
    4. You shouldn't need luck yet to see this screen, if you do, quit now:<br>
![venv-virtualbox-pfsense-firstboot.png](images/venv-virtualbox-pfsense-firstboot.png)
    5. We configured the interfaces in the right order so we do not need to do anything here, however, when you build the actual device, you may have to reassign the interfaces.
    6. You may need to change the LAN network if your **WAN** also lists **192.168.1.x/24** to do that, select option **2** and follow the onscreen directions. Or if you can wait, the general setup wizard below will do it for you.

## Install Virtual Debian
1. We now leave the pfSense virtual machine on at all times and use the Debian LiveCD to edit and test the new configuration!
    * If I do not specify otherwise or if you know better, everything in the following steps is left as **Default**.
2. Start the Debian LiveCD.
    * If you have a Retina display click **View > Virtual Screen 1 > Scale to 200%**.
3. Click on **Install Debian**
4. Follow the instructions on the screen to install, it is mostly a _mash next_ endeavor.
    * <span style="color:red">I suggest setting the correct timezone so you don't get SSL errors later!</span>
    * If your screen locks while it installs, the password is **live**
5. Shut the virtual machine down. VirtualBox will automagically remove the LiveCD for you after installation.
6. Start the Debian virtual machine back up again and login.
7. Open **Konsole** and run the following commands:
    1. ```sudo su```
    2. ```apt-get update && apt-get upgrade```
    3. ```apt-get install dkms linux-headers-$(uname -r) build-essential```
    4. ```exit```
8. On the menu above the virtual machine, click **Devices > Insert Guest Additions CD Image**
9. Open the directory of the mounted cd image
10. Double click on **autorun.sh**
11. Once complete, reboot the Debian virtual machine
12. Click on the menubar for the virtual machine and adjust the scale manually to what is typically comfortable. At this point it will wake up and give you the full resolution.
13. Depending on your VPN providers, installation instructions may vary. Below are the steps outlined to get ExpressVPN and NordVPN settings for pfSense.
    1. Open Firefox.
    2. Navigate to: https://www.expressvpn.com/setup#manual -- You will have to login.
    3. Find some servers near you from the expandable list on the right and download their *.ovpn files.
    4. Now we get NordVPN
    5. Go back to **Konsole** and install it with: ```sh <(curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh)```
    6. ```sudo usermod -aG nordvpn $USER```
    7. ```sudo apt-get install wireguard```
    8. Reboot the Debian virtual machine and open the terminal again.
        * <span style="color:red">Do not skip this step as NordVPN has its own implementation of WireGuard that it will use if it cannot connect the running WireGuard system socket</span>
    9. Navigate to: https://www.nordvpn.com -- You will have to login.
    10. Click **NordVPN** under **Services** on the left navigation bar.
    11. Scroll down until you see **Access token**
    12. Generate a new token for 30 days.
    13. Paste into Konsole as ```nordvpn login --token <copied tokenID without the aligator brackets>```
        * <span style="color:yellow">Watch out for garbage at the beginning and end of the copied string, it doesn't paste cleanly!</span>
    14. ```nordvpn connect```
    15. ```sudo wg show```
    16. ```sudo wg showconf nordlynx```
    17. Save this information somewhere as you will need it later! I saved mine with my favorite text editor which wasn't installed:
        * ```sudo apt-get install vim```

## Initial pfSense Setup
14. Open an installed browser **Firefox/Chromium/Konqueror** and navigate to 192.168.1.1 (unless you had to change it above, however, I will be referring to it as 192.168.1.1 for the rest of this section).
15. Login to pfSense using the default login credentials: **admin / pfsense**
16. Follow the general setup instructions and make changes on steps I highlight below:
    1. **Step 2**: Setup the hostname and search domain of your firewall, for this I use **pfSense** and **virtualhome.local**:<br>
![venv-virtualbox-pfsense-setup-wizard-1.png](images/venv-virtualbox-pfsense-setup-wizard-1.png)
    2. **Step 3**: NTP settings are safe to leave alone unless you have your own:
![venv-virtualbox-pfsense-setup-wizard-2.png](images/venv-virtualbox-pfsense-setup-wizard-2.png)
    3. **Step 4**: This is where you can enter your current router's MAC address, being that it is on the LAN side of the actual broadcast domain, it will not impact your network. But it will save you from chasing your tail later:<br>
![venv-virtualbox-pfsense-setup-wizard-3.png](images/venv-virtualbox-pfsense-setup-wizard-3.png)
    4. **Step 5**: This is where you can change your local network from 192.168.1.1, we will be setting it to 192.168.5.1/24 for this virtual environment:<br>
![venv-virtualbox-pfsense-setup-wizard-4.png](images/venv-virtualbox-pfsense-setup-wizard-4.png)
    5. pfSense will now attempt to reload the page and fail. Disconnect and connect **Wired connection 1** from the task manager in the bottom right. Then navigate to **192.168.5.1**:<br>
![venv-virtualbox-gentoo-reset-network-1.png](images/venv-virtualbox-debian-reset-network-1.png)
    6. At this point, the internet will start working through the Firewall in the Gentoo virtual machine. And it finished the general setup while the network was broken.

## Make Initial pfSense Snapshot
1. You will be making a lot of mistakes, the pfSense configuration can get 'stuck' or messed up from aggressive tinkering as of version 2.4.x. As an extra precaution, I like to create snapshots in stages in order to not have to chase a _Ghost in the Shell_. 
2. We are going to make one change to the config before we make a Snapshot.
3. Click **System > Advanced**. Change the **Protocol** to **HTTP** then click **Save**
    * Why? The wpad.dat / wpad.da / proxy.pac file will be stored on the Firewall and will be called by browsers on your network. If this is a concern, host them elsewhere, you can point to them later via DHCP options. Otherwise, you will need self-signed certs everywhere.
4. pfSense will get angry again, use the pfSense virtual machine terminal to reboot it (Yeah, I don't remember pfSense having these problems either).
5. Try logging into pfSense from your Gentoo virtual machine again. It should be working again. Once confirmed, use the next step to create the snapshot.
6. Open the pfSense virtual machine window. Click **Machine > Take Snapshot**, Label it, **Initial Config**
7. Once created, shut down pfSense and then restore the snapshot top verify it actually works. Snapshots are hidden in the menu just right of the virtual machine name:<br>
![venv-virtualbox-pfsense-initial-snapshot-1.png](images/venv-virtualbox-pfsense-initial-snapshot-1.png)

## Install pfSense 3rd Party Packages
1. Navigate to **System > Package Manger > Available Packages**
2. Install the following packages:
    * Filer
    * nmap
    * pfBlockerNG
    * Service_Watchdog
    * squid
    * Status_Traffic_Totals
    * WireGuard
3. Take another snapshot and label it: **Installed Packages**

## Create CA and Certificates
* <span style="color:red">**From this point forward in the documentation, if I omit details about configuring something, it means I leave it at its default values.**</span>
1. Navigate to **System > Certificate Manager > Add**
2. Enter the following data:
    * **Descriptive name:** Home CA
    * **Method:** Create an internal Certificate Authority
    * **Randomize Serial:** Checked
    * **Common Name:** internal-vpn-ca
    * Fill out the rest of the information as needed
3. Navigate to **System > Certificate Manager > Certificates > Add/Sign**
4. Enter the following data:
    * **Method:** Create an internal Certificate
    * **Descriptive name:** Home CA - VPN
    * **Certificate authority:** Home CA
    * **Common Name:** pfsense.virtualhome.local
    * **Certificate Type:** Server Certificate
    * Fill out the rest of the information as needed
    * Save
5. Create an additional Certificate:
    * **Method:** Create an internal Certificate
    * **Descriptive name:** Home CA - Proxy
    * **Certificate authority:** Home CA
    * **Common Name:** pfsense.virtualhome.local
    * **Certificate Type:** User Certificate
    * Fill out the rest of the information as needed
    * Save


## OpenVPN Tunnels
* This is where you and I might diverge a little. For OpenVPN I use ExpressVPN. NordVPN's support for OpenVPN drops a _lot_ of packets. I will cover setting up WireGuard with NordVPN in the next section.
* In addition I will be pulling details from my production environment so if you see CA/Certs or subnets that conflict with what I previously told you, I will address them under the screenshots in a bullet point.
1. Navigate to **VPN > OpenVPN > Clients > Add**
