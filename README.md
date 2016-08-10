Descartes Holland
descartes.holland@gmail.com


Update Philips Hue or LIFX smart RGB lightbulbs via a Python script, and send the HSB values to a Kafka instance.

Configuration Values:

gui_HUE.py
    HUE_CONNECT    (bool)    - True to connect to the smart lights, false to debug
    KAFKA_CONNECT  (bool)    - True to connect to the configured Kafka instance, false otherwise
    BRIDGE_IP      (string)  - Set to the IP address of the Hue bridge
    KAFKA_IP       (string)  - Set to the hostname and port of the Kafka instance

gui_lifx.py
    * Set the number of bulbs in the line containing lifx = Lifx(num_bulbs = <int here>)
    HUE_CONNECT    (bool)    - True to connect to the smart lights, false to debug
    KAFKA_CONNECT  (bool)    - True to connect to the configured Kafka instance, false otherwise
    KAFKA_IP       (string)  - Set to the hostname and port of the Kafka instance

