# InkyDash

A dashboard to display the following in a rotating manner:
* Current COVID-19 hospitalizations and positive tests for a state
* Top 3 Hacker News Stories and their points
* Current Air Quality and weather conditions from a [personal monitor](https://github.com/hubertron/air_quality_monitor)
* Today's weather forecast from NOAA

## Equipment Needed

1. Rasperry Pi - Any newer one will do
2. InkyPhat
3. Internet access

## Installation

1. Clone this repo: `git clone https://github.com/hubertron/inkydash`
2. Install requirements `pip3 install -r requirements.txt`
3. Configure locations in `locations.yaml` 
4. Remove or comment out `currentCondtions` function if you do not have your own personal station running
5. Run with `python3 main.py`
6. Start on boot with systemd service:
```
[Unit]
Description = Display Feeds on eInk
After = network.target

[Service]
User=pi
ExecStart = /usr/bin/python3 /home/pi/inkydash/main.py
Restart=always
RestartSec=10

[Install]
WantedBy = multi-user.target
```
7. Final setup
`sudo systemctl daemon-reload`,
`sudo systemctl enable eink.service`, and
`sudo systemctl start eink.service`


## Wishlist
- [ ] Add uptime monitoring func to tell me if any of my sites are down
- [ ] Add intergration to Outlook to notify me of upcoming meeting
- [ ] Add traffic service to tell me if commute time is longer than expected (if COVID ever ends)
- [ ] Maybe quote of the day or breaking news?
