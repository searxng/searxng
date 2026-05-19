Android / Termux Installation
=============================

It is possible to run SearXNG on Android devices using the Termux app, turning your mobile phone into a private self-hosted search engine. This platform is ideal for:

- Privacy enthusiasts
- Self-hosters
- Developers and cybersecurity learners
- Repurposing old Android phones

.. note::
   This setup is somewhat advanced and not all search engines will work on Android. Community support is limited.

Prerequisites
-------------

- Android device with Termux installed (`F-Droid recommended <https://f-droid.org/en/packages/com.termux/>`_)
- Sufficient storage and stable internet connection
- Basic familiarity with Python and Linux commands

Installation Steps
------------------

1. Open **Termux** on your Android device.
2. Update packages::

     pkg update && pkg upgrade

3. Install required dependencies::

     pkg install clang python git make libxml2 libxslt

4. Upgrade pip and setup tools::

     pip install --upgrade pip setuptools wheel

5. Clone the SearXNG project and enter directory::

     git clone https://github.com/searxng/searxng.git
     cd searxng

6. Install Python requirements (lxml may take longer to build)::

     pip install -r requirements.txt

7. **Change the secret key** (before first run):
   
   Open ``searx/settings.yml`` in nano or your editor::

     nano searx/settings.yml

   Find the line::

     secret_key: "ultrasecretkey"

   And set it to a long, random value.

8. Start SearXNG::

     python3 -m searx.webapp

Accessing SearXNG
-----------------

- By default, browse to: ``http://localhost:8888`` on your Android device.
- If you cannot connect, set ``bind_address: "0.0.0.0"`` in ``searx/settings.yml``, restart SearXNG, and try accessing from another device on the LAN.
- For browser issues, try **Firefox for Android** or Termux's web CLI tools.

Extra Tips
----------

- To disable problematic engines, edit ``searx/settings.yml`` and comment out or remove entries.
- To access SearXNG from other devices on your network:
  
  - Find your phone's IP in Termux with::

        ip addr

  - Then browse to ``http://<ip>:8888`` from your other device.


----

*Guide contributed by Z-Hussein.
