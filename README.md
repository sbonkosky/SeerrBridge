# 🌉 SeerrBridge - Automate Your Media Fetching with DMM 🎬

![seerrbridge-cover](https://github.com/user-attachments/assets/653eae72-538a-4648-b132-04faae3fb82e)

![GitHub last commit](https://img.shields.io/github/last-commit/Woahai321/SeerrBridge?style=for-the-badge&logo=github)
![GitHub issues](https://img.shields.io/github/issues/Woahai321/SeerrBridge?style=for-the-badge&logo=github)
![GitHub stars](https://img.shields.io/github/stars/Woahai321/SeerrBridge?style=for-the-badge&logo=github)
![GitHub release](https://img.shields.io/github/v/release/Woahai321/SeerrBridge?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.10.11+-blue?style=for-the-badge&logo=python)
[![Website](https://img.shields.io/badge/Website-soluify.com-blue?style=for-the-badge&logo=web)](https://soluify.com/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-connect-blue?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/company/soluify/)
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-4-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

---

## 🚀 What is SeerrBridge?

🌉 **SeerrBridge** is a browser automation tool that integrates [Jellyseer](https://github.com/Fallenbagel/jellyseerr)/[Overseerr](https://overseerr.dev/) with [Debrid Media Manager](https://github.com/debridmediamanager/debrid-media-manager). It listens to movie requests via Overseerr webhook. It automates the torrent search and download process using Debrid Media Manager via browser automation, which in turn, gets sent to Real-Debrid. This streamlines your media management, making it fast and efficient.

_Heads up: the BridgeBoard dashboard/UI has been removed—the FastAPI service remains fully functional and exposes the same automation features via API and logs._

<details>
<summary>🛠️ Why SeerrBridge?</summary>

**SeerrBridge** eliminates the need to set up multiple applications like [Radarr](https://radarr.video/), [Sonarr](https://sonarr.tv/), [Jackett](https://github.com/Jackett/Jackett), [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr), and other download clients. With SeerrBridge, you streamline your media management into one simple, automated process. No more juggling multiple tools—just request and download!

Simply put, I was too lazy to set up all of these other applications (arrs) and thought.... I want this instead.

Example:

![sb](https://github.com/user-attachments/assets/f4a9f1c9-5fa9-4fa5-b1e8-3ddc6a156a91)
</details>

---

<details>
<summary>📊 Flowchart (Rectangle of Life)</summary>

![image](https://github.com/user-attachments/assets/e6b1a4f2-8c69-40f9-92a8-e6e76e8e34e7)
</details>


<details>
<summary>🔑 Key Features</summary>

- **Automated Movie Requests**: Automatically processes movie requests from Overseerr and fetches torrents from Debrid Media Manager.
- **Automated Job Runner**: A lightweight worker runs every few minutes (and on webhook) to inspect Overseerr/Jellyseerr and fire Selenium searches.
- **TV & Movie Coverage**: Applies prioritized regex searches, Instant RD buttons, and `RD (100%)` checks to both movies and individual seasons.

- **Debrid Media Manager Integration**: Uses DMM to automate (via browser) torrent search & downloads.
  
- **Persistent Browser Session**: Keeps a browser session alive using Selenium, ensuring faster and more seamless automation.

- **Error Handling & Logging**: Provides comprehensive logging and error handling to ensure smooth operation.
</details>

<details>
<summary>📊 Compatibility</summary>

| Service        | Status | Notes                                |
|----------------|--------|--------------------------------------|
| **[List Sync](https://github.com/Woahai321/list-sync)**| ✅      | Our other Seerr app for importing lists   |
| **Jellyseerr**  | ✅      | Main integration. Supports movie requests via webhook  |
| **Overseerr**   | ✅      | Base application Jellyseerr is based on  |
| **Debrid Media Manager**| ✅      | Torrent fetching automation          |
| **Real-Debrid**| ✅      | Unrestricted (torrent) downloader       |
| **AllDebrid**| ❌      | Not Supported      |
| **TorBox**| ❌      | Not Supported     |
| **SuggestArr**| ✅      | Automatically grab related content and send to Jellyseerr/Overseerr      |
| **Windows & Linux x86-64**| ✅      | Tested and working in both Windows & Linux environments      |
</details>

<details>
### (THIS SCRIPT IS STILL IN BETA)
<summary>⚙ Requirements</summary>

Before you can run this script, ensure that you have the following prerequisites:

### 1. **Jellyseerr / Overseerr API & Notifications**
  - SeerrBridge should be running on the same machine that Jellyseerr / Overseerr is running on.
  - You will need the API key for your .env file.
  - For notifications, navigate to Settings > Notifications > Webhook > Turn it on, and configure as shown below

     ```bash
     http://localhost:8777/jellyseer-webhook/
     ```

![image](https://github.com/user-attachments/assets/170a2eb2-274a-4fc1-b288-5ada91a9fc47)

Ensure your JSON payload is the following 

```
{
    "notification_type": "{{notification_type}}",
    "event": "{{event}}",
    "subject": "{{subject}}",
    "message": "{{message}}",
    "image": "{{image}}",
    "{{media}}": {
        "media_type": "{{media_type}}",
        "tmdbId": "{{media_tmdbid}}",
        "tvdbId": "{{media_tvdbid}}",
        "status": "{{media_status}}",
        "status4k": "{{media_status4k}}"
    },
    "{{request}}": {
        "request_id": "{{request_id}}",
        "requestedBy_email": "{{requestedBy_email}}",
        "requestedBy_username": "{{requestedBy_username}}",
        "requestedBy_avatar": "{{requestedBy_avatar}}",
        "requestedBy_settings_discordId": "{{requestedBy_settings_discordId}}",
        "requestedBy_settings_telegramChatId": "{{requestedBy_settings_telegramChatId}}"
    },
    "{{issue}}": {
        "issue_id": "{{issue_id}}",
        "issue_type": "{{issue_type}}",
        "issue_status": "{{issue_status}}",
        "reportedBy_email": "{{reportedBy_email}}",
        "reportedBy_username": "{{reportedBy_username}}",
        "reportedBy_avatar": "{{reportedBy_avatar}}",
        "reportedBy_settings_discordId": "{{reportedBy_settings_discordId}}",
        "reportedBy_settings_telegramChatId": "{{reportedBy_settings_telegramChatId}}"
    },
    "{{comment}}": {
        "comment_message": "{{comment_message}}",
        "commentedBy_email": "{{commentedBy_email}}",
        "commentedBy_username": "{{commentedBy_username}}",
        "commentedBy_avatar": "{{commentedBy_avatar}}",
        "commentedBy_settings_discordId": "{{commentedBy_settings_discordId}}",
        "commentedBy_settings_telegramChatId": "{{commentedBy_settings_telegramChatId}}"
    },
    "{{extra}}": []
}
```

Notification Types should also be set to "Request Automatically Approved", and your user should be set to automatic approvals.

![image](https://github.com/user-attachments/assets/46df5e43-b9c3-48c9-aa22-223c6720ca15)

![image](https://github.com/user-attachments/assets/ae25b2f2-ac80-4c96-89f2-c47fc936debe)


### 2. **Real-Debrid Account**
   - You will need a valid [Real-Debrid](https://real-debrid.com/) account to authenticate and interact with the Debrid Media Manager.
     - The Debrid Media Manager Access token, Client ID, Client Secret, & Refresh Tokens are used and should be set within your .env file. Grab this from your browser via Inspect > 

![image](https://github.com/user-attachments/assets/c718851c-60d4-4750-b020-a3edb990b53b)

This is what you want to copy from your local storage and set in your .env:

    RD_ACCESS_TOKEN={"value":"your_token","expiry":123}
    RD_CLIENT_ID=YOUR_CLIENT_ID
    RD_CLIENT_SECRET=YOUR_CLIENT_SECRET
    RD_REFRESH_TOKEN=YOUR_REFRESH_TOKEN

### 3. **Trakt API / Client ID**
   - Create a [Trakt.tv](https://Trakt.tv) account. Navigate to Settings > Your API Apps > New Application
     - You can use https://google.com as the redirect URI
     - Save the Client ID for your .env file.
    
![image](https://github.com/user-attachments/assets/c5eb7dbf-7785-45ca-99fa-7e6341744c9d)
![image](https://github.com/user-attachments/assets/3bb77fd5-2c8f-4675-a1da-59f0cb9cb178)


### 4. **Python 3.10.11+**
   - The bot requires **Python 3.10.11** or higher. You can download Python from [here](https://www.python.org/downloads/).

### 5. **Required Python Libraries**
   - You can install the required libraries by running:
     ```bash
     pip install -r requirements.txt
     ```

---

### Example `.env` File

Create a `.env` (or rename the example .env) file in the root directory of the project and add the following environment variables:

```bash
RD_ACCESS_TOKEN={"value":"YOUR_TOKEN","expiry":123456789}
RD_REFRESH_TOKEN=YOUR_REFRESH_TOKEN
RD_CLIENT_ID=YOUR_CLIENT_ID
RD_CLIENT_SECRET=YOUR_CLIENT_SECRET
TRAKT_API_KEY=YOUR_TRAKT_TOKEN
OVERSEERR_API_KEY=YOUR_OVERSEERR_TOKEN
OVERSEERR_BASE=https://YOUR_OVERSEERR_URL.COM
HEADLESS_MODE=true
MAX_MOVIE_SIZE=0
MAX_EPISODE_SIZE=0
JOB_INTERVAL_SECONDS=180
```
</details>

<details>
<summary>🛠️ Getting Started</summary>

### Sending Notifications to SeerrBridge from Jellyseerr / Overseerr

Configure your webhook as mentioned above so SeerrBridge can ingest and process approval requests.


### Python Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Woahai321/SeerrBridge.git
   cd SeerrBridge
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

### 🐳 Docker Support

SeerrBridge now ships only as the FastAPI automation service. You can run it on its own by using the provided Docker image or composing it yourself.

## Prerequisites
- Docker and Docker Compose installed on your system
- A `.env` file with your configuration

### Quick Start with Docker Compose

1. **Use the provided docker-compose.yml** (identical to the file in this repo):

```yaml
services:
  seerrbridge:
    image: ghcr.io/woahai321/seerrbridge:latest
    container_name: seerrbridge
    ports:
      - "8777:8777"
    env_file:
      - ./.env
    volumes:
      - shared_logs:/app/logs
      - ./.env:/app/.env
    restart: unless-stopped
    command: >
      sh -c "
        cat /app/.env > /dev/null && 
        echo 'Starting SeerrBridge with refreshed env' &&
        uvicorn main:app --host 0.0.0.0 --port 8777
      "
    networks:
      - seerrbridge_network

volumes:
  shared_logs:

networks:
  seerrbridge_network:
    driver: bridge
```

2. **Create or edit your `.env` file**:

```bash
RD_ACCESS_TOKEN={"value":"YOUR_TOKEN","expiry":123456789}
RD_REFRESH_TOKEN=YOUR_REFRESH_TOKEN
RD_CLIENT_ID=YOUR_CLIENT_ID
RD_CLIENT_SECRET=YOUR_CLIENT_SECRET
TRAKT_API_KEY=YOUR_TRAKT_TOKEN
OVERSEERR_API_KEY=YOUR_OVERSEERR_TOKEN
OVERSEERR_BASE=https://YOUR_OVERSEERR_URL.COM
HEADLESS_MODE=true
MAX_MOVIE_SIZE=0
MAX_EPISODE_SIZE=0
JOB_INTERVAL_SECONDS=180
```

3. **Ensure you get the latest image**:

```bash
docker compose pull
```

4. **Start the container**:

```bash
docker compose up -d
```

5. **Access the API**:
   - SeerrBridge API: [http://localhost:8777](http://localhost:8777)

### Configuration Notes

- **Volumes**: `/app/logs` is persisted so historical logs remain available across restarts.
- **Networks**: The default bridge network allows Overseerr/Jellyseerr containers to reach SeerrBridge.
- **Environment Variables**: Bind-mounting `.env` allows container restarts to pick up changes automatically.
- **Restart Policy**: The container will restart automatically unless manually stopped.
---

***IF YOU ARE USING OVERSEERR IN DOCKER AND SEERRBRIDGE IN DOCKER, YOUR WEBHOOK IN OVERSEERR NEEDS TO BE THE DOCKER CONTAINER IP***

To find the IP of the SeerrBridge Docker container do the following:

```bash
docker ps
```

You will see the container and ID

![image](https://github.com/user-attachments/assets/dac5fb21-89a7-42ff-8e73-911a6b8ee149)

Grab the ID and do

```bash
docker inspect YOUR-ID
```

You will see the ID in the response:

![image](https://github.com/user-attachments/assets/b9a67170-748b-4c44-b37c-86a820e8d09a)

This will determine your Overseerr Webhook URL i.e. HTTP://DOCKER-CONTAINER-IP:8077/jellyseer-webhook/

---



## Docker Network Configuration

### Steps to Align Containers on the Same Network

1. **Check Container Networks:**
   Run the following command to list the containers and their associated networks:
   ```bash
   docker ps --format '{{ .ID }} {{ .Names }} {{ json .Networks }}'
   ```
   This will display the container IDs, names, and the networks they are connected to.

2. **Disconnect the Container from Its Current Network:**
   Use the following command to disconnect a container from its current network:
   ```bash
   docker network disconnect NETWORK_NAME CONTAINER_ID
   ```
   Replace `NETWORK_NAME` with the name of the network the container is currently on, and `CONTAINER_ID` with the ID of the container.

3. **Connect the Container to the Desired Network:**
   Use the following command to connect the container to the target network:
   ```bash
   docker network connect TARGET_NETWORK_NAME CONTAINER_ID
   ```
   Replace `TARGET_NETWORK_NAME` with the name of the network you want the container to join (e.g., `overseerr`), and `CONTAINER_ID` with the ID of the container.

4. **Verify the Changes:**
   Run the `docker ps --format '{{ .ID }} {{ .Names }} {{ json .Networks }}'` command again to confirm that both containers are now on the same network.

### Example
To move a container with ID `abc123` from its current network to the `overseerr` network:
```bash
docker network disconnect current_network abc123
docker network connect overseerr abc123
```

### Notes
- Ensure both containers are connected to the same network after completing the steps.
- If the containers are still not communicating, double-check the network configuration and ensure no firewall rules are blocking the connection.

---

That's it! Your **SeerrBridge** container should now be up and running. 🚀
</details>

<details>
<summary>🛤️ Roadmap</summary>

- [ ] **Faster Processing**: Implement concurrency to handle multiple requests simultaneously.
- [x] **TV Show Support**: Extend functionality to handle TV series and episodes.
- [x] **DMM Token**: Ensure access token permanence/refresh
- [x] **Jellyseer/Overseer API Integration**: Direct integration with Jellyseer/Overseer API for smoother automation and control.
- [x] **Title Parsing**: Ensure torrent titles/names are properly matched and handle different languages.
- [x] **Docker Support**: Allow for Docker / Compose container.
</details>

<details>
<summary>🔍 How It Works</summary>

1. **Seerr Webhook**: SeerrBridge listens for movie requests via the configured webhook.
2. **Automated Search**: It uses Selenium to automate the search for movies on Debrid Media Manager site.
3. **Torrent Fetching**: Once a matching torrent is found, SeerrBridge automates the Real-Debrid download process.
4. **Background Job**: Requests are handled by a single background runner that periodically re-checks Overseerr.

If you want to see the automation working in real-time, you can edit the .env and set it to false

![image](https://github.com/user-attachments/assets/dc1e9cdb-ff59-41fa-8a71-ccbff0f3c210)

This will launch a visible Chrome browser. Be sure not to mess with it while it's operating or else you will break the current action/script and need a re-run.

Example:

![sb](https://github.com/user-attachments/assets/c6a0ee1e-db07-430c-93cd-f282c8f0888f)
</details>

<details>
<summary>📁 Movie and Show File Sizes</summary>

For movies, possible values are: 
| Value | Description |
| :-----------: | :-----------: |
| 0| Biggest Size Possible |
|1|1 GB|
|3|3 GB|
|5|5 GB **(Default)**|
|15|15 GB|
|30|30 GB|
|60|60 GB|

For episodes, possible values are: 
| Value | Description |
| :-----------: | :-----------: |
| 0| Biggest Size Possible |
|0.1|100 MB|
|0.3|300 MB|
|0.5|500 MB|
|1|1 GB **(Default)**|
|3|3 GB|
|5|5 GB|
</details>


## 📞 Contact

Have any questions or need help? Feel free to [open an issue](https://github.com/Woahai321/SeerrBridge/issues) or connect with us on [LinkedIn](https://www.linkedin.com/company/soluify/).

---

## 🤝 Contributing

We welcome contributions! Here’s how you can help:

1. **Fork the repository** on GitHub.
2. **Create a new branch** for your feature or bug fix.
3. **Commit your changes**.
4. **Submit a pull request** for review.

---

## 💰 Support SeerrBridge's Development

If you find SeerrBridge useful and would like to support its development, consider becoming a sponsor:

➡️ [Sponsor us on GitHub](https://github.com/sponsors/Woahai321)

Thank you for your support!

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Woahai321/SeerrBridge&type=Date)](https://star-history.com/#Woahai321/SeerrBridge&Date)

---

## Contributors 🌟

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/KRadd1221"><img src="https://avatars.githubusercontent.com/u/5341534?v=4?s=100" width="100px;" alt="Kevin"/><br /><sub><b>Kevin</b></sub></a><br /><a href="https://github.com/Woahai321/SeerrBridge/commits?author=KRadd1221" title="Code">💻</a> <a href="https://github.com/Woahai321/SeerrBridge/issues?q=author%3AKRadd1221" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/shivamsnaik"><img src="https://avatars.githubusercontent.com/u/16705944?v=4?s=100" width="100px;" alt="Shivam Naik"/><br /><sub><b>Shivam Naik</b></sub></a><br /><a href="https://github.com/Woahai321/SeerrBridge/commits?author=shivamsnaik" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jacobmejilla"><img src="https://avatars.githubusercontent.com/u/112974356?v=4?s=100" width="100px;" alt="jacobmejilla"/><br /><sub><b>jacobmejilla</b></sub></a><br /><a href="https://github.com/Woahai321/SeerrBridge/commits?author=jacobmejilla" title="Code">💻</a> <a href="#ideas-jacobmejilla" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://www.funkypenguin.co.nz"><img src="https://avatars.githubusercontent.com/u/1524686?v=4?s=100" width="100px;" alt="David Young"/><br /><sub><b>David Young</b></sub></a><br /><a href="https://github.com/Woahai321/SeerrBridge/commits?author=funkypenguin" title="Documentation">📖</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

---

<details>
<summary>📜 Legal Disclaimer</summary>

This repository and the accompanying software are intended **for educational purposes only**. The creators and contributors of this project do not condone or encourage the use of this tool for any illegal activities, including but not limited to copyright infringement, illegal downloading, or torrenting copyrighted content without proper authorization.

### Usage of the Software:
- **SeerrBridge** is designed to demonstrate and automate media management workflows. It is the user's responsibility to ensure that their usage of the software complies with all applicable laws and regulations in their country.
- The tool integrates with third-party services which may have their own terms of service. Users must adhere to the terms of service of any external platforms or services they interact with.

### No Liability:
- The authors and contributors of this project are not liable for any misuse or claims that arise from the improper use of this software. **You are solely responsible** for ensuring that your use of this software complies with applicable copyright laws and other legal restrictions.
- **We do not provide support or assistance for any illegal activities** or for bypassing any security measures or protections.

### Educational Purpose:
This tool is provided as-is, for **educational purposes**, and to help users automate the management of their own legally obtained media. It is **not intended** to be used for pirating or distributing copyrighted material without permission.

If you are unsure about the legality of your actions, you should consult with a legal professional before using this software.
</details>
