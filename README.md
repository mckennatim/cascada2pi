#cascada

An Internet of Things (IOT) project using relays and electronics controlled by a raspberry Pi. Project is used for outdoor water control. It turns on and off and sets timers for outdoor watering and controls a two ponds and the waterfall between them injecting new water as needed.

Project uses `python` running forever through `supervisrctl`. `gevent` and `flask` provide the web framework for a `Restful API` that uses `ServerSentEvents(SSE)` to notify internet connected devices as to the state of the system. Each garden device is controlled on its own `thread`