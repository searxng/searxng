.. _installation macos telugu:

=========================
macOS లో సేర్చ్‌ఎన్‌జి ఇన్‌స్టాలేషన్
=========================

macOS సిస్టమ్స్ కోసం SearXNG ఇన్‌స్టాలేషన్ గైడ్ (Apple Silicon M1/M2/M3 మరియు Intel Mac లు)

.. contents::
   :depth: 2
   :local:
   :backlinks: entry

ముందు అవసరమైనవి
=================

సిస్టమ్ అవసరాలు
-----------------

* macOS 11 (Big Sur) లేదా తరువాతి వెర్షన్
* macOS 15.7.1 (Sequoia) పరీక్షించబడింది మరియు పనిచేస్తుంది
* కనీసం 4GB RAM
* 2GB ఖాళీ డిస్క్ స్థలం

అవసరమైన సాఫ్ట్‌వేర్
--------------------

Homebrew Package Manager
~~~~~~~~~~~~~~~~~~~~~~~~

మీకు Homebrew ఇన్‌స్టాల్ చేయబడలేదంటే::

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

ఇన్‌స్టాలేషన్ తర్వాత, మీ PATH కు Homebrew జోడించడానికి సూచనలను అనుసరించండి.

Mac కోసం Docker Desktop
~~~~~~~~~~~~~~~~~~~~~~~~~

Docker Desktop ఇన్‌స్టాల్ చేయండి::

    brew install --cask docker

లేదా నేరుగా డౌన్‌లోడ్ చేయండి: https://www.docker.com/products/docker-desktop

**Apple Silicon వాడుకరులకు ముఖ్యం**: మీరు Docker Desktop యొక్క Apple Silicon వెర్షన్‌ను డౌన్‌లోడ్ చేసుకోవాలి.

ఇన్‌స్టాలేషన్ తర్వాత:

1. Applications నుండి Docker Desktop ప్రారంభించండి
2. Docker ప్రారంభం కావడం వరకు వేచి ఉండండి
3. Docker రన్నింగ్ అవుతుందో తనిఖీ చేయండి::

    docker --version
    docker compose version

ఇన్‌స్టాలేషన్ పద్ధతులు
=======================

పద్ధతి 1: Docker ఇన్‌స్టాలేషన్ (సిఫార్సు చేయబడింది)
--------------------------------------------------

ఇది macOS వాడుకరులకు సులభమైన పద్ధతి.

దశ 1: Docker Repository క్లోన్ చేయండి
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    cd ~/Documents
    git clone https://github.com/searxng/searxng-docker.git
    cd searxng-docker

దశ 2: మీ Instance ను కాన్ఫిగర్ చేయండి
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``.env`` ఫైల్‌ను సవరించండి::

    nano .env

మీ instance పేరు మరియు ఇతర ప్రాధాన్యతలను సెట్ చేయండి.

దశ 3: SearXNG ప్రారంభించండి
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    docker compose up -d

దశ 4: మీ Instance యాక్సెస్ చేయండి
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

మీ బ్రౌజర్ తెరిచి వెళ్ళండి: http://localhost:8080

macOS-నిర్దిష్ట పరిగణనలు
===========================

Apple Silicon (M1/M2/M3) గమనికలు
---------------------------------

Mac కోసం Docker Desktop ఆర్కిటెక్చర్ తేడాలను స్వయంచాలకంగా నిర్వహిస్తుంది. ARM64 ఆర్కిటెక్చర్ కోసం ప్రత్యేక కాన్ఫిగరేషన్ అవసరం లేదు.

ఫైల్ అనుమతులు
---------------

మీకు అనుమతి లోపాలు ఎదురైతే::

    sudo chown -R $(whoami) ~/Documents/searxng-docker/

Port సంఘర్షణలు
---------------

సాధారణ macOS సేవలు డిఫాల్ట్ ports తో సంఘర్షించవచ్చు:

Port 8080 సంఘర్షణ తనిఖీ::

    lsof -i :8080

Port ఉపయోగంలో ఉంటే, ఒకటి:

1. సంఘర్షించే ప్రక్రియను ముగించండి::

    kill -9 <PID>

2. లేదా ``docker-compose.yml`` లో port మార్చండి

సమస్య పరిష్కారం
==================

Docker ప్రారంభం కావడం లేదు
---------------------------

Docker ప్రారంభం కాకపోతే:

1. Docker Desktop పూర్తిగా నిష్క్రమించండి
2. మళ్లీ Docker Desktop ప్రారంభించండి

SearXNG యాక్సెస్ చేయలేకపోవడం
----------------------------

మీరు localhost:8080 వద్ద SearXNG యాక్సెస్ చేయలేకపోతే:

1. Docker containers రన్నింగ్ అవుతున్నాయో తనిఖీ చేయండి::

    docker ps

2. లాగ్‌లను తనిఖీ చేయండి::

    docker compose logs searxng

తదుపరి దశలు
=============

* :ref:`searxng settings`
* :ref:`buildhosts`
* engines కాన్ఫిగర్ చేయండి
* nginx లేదా Apache తో HTTPS సెటప్ చేయండి

అదనపు వనరులు
===============

* అధికారిక డాక్యుమెంటేషన్: https://docs.searxng.org
* GitHub Issues: https://github.com/searxng/searxng/issues
* కమ్యూనిటీ చాట్: Matrix లో #searxng

సహకారం
========

ఈ macOS సూచనలతో సమస్య కనుగొన్నారా? దయచేసి GitHub లో నివేదించండి లేదా pull request సమర్పించండి!

----

**పరీక్షించబడింది**: macOS Sequoia 15.7.1 (Build 24G231) Apple Silicon తో
