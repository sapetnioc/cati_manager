CATI Portal
============

Getting Started
---------------

- Install dependencies

    sudo apt install git python3 python3-click singularity-container

- Create a new directory for hosting an instance of the portal (everything 
  the instance will create goes into that directory)

    mkdir cati_portal

- Download source code

    git clone https://github.com/sapetnioc/cati_portal.git cati_portal/git

- During the transition from Pyramid to Flask, it is necessary to use the "flask" branch:

    cd cati_portal/git
    git checkout flask
    cd ../..

- Install a new portal

    cati_portal/git/cati_portal_ctl new

- Start the portal

    cati_portal/git/cati_portal_ctl start

- Visit http://localhost:8080
