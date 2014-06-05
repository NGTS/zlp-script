Scripts or files external to the root directory that need moving

* `/home/ag367/progs/pipebias.py`
* `/home/ag367/progs/pipedark.py`
* `/home/ag367/test/shuttermap.fits`
* `/home/ag367/progs/pipeflat.py`
* `/home/ag367/progs/pipered.py`
* `/home/toml/Python/NGTS_workpackage/bin/ZLP_app_photom.py`
* My code


External programs:

* My version of sysrem, or the final implementation from Richard needs to be moved.

Ideas:

* Make the `WORKINGDIR` variable a program argument

All scripts:

```
/usr/local/python/bin/python
/wasp/home/sw/SelectionEffects/bin/Sysrem.srw
/ngts/pipedev/OriginalData/scripts/createlists.py
/home/ag367/progs/pipebias.py
/home/ag367/progs/pipedark.py
/home/ag367/progs/pipeflat.py
/home/ag367/progs/pipered.py
/ngts/pipedev/wait.sh 
/ngts/pipedev/InputCatalogue/run_on_directory.sh
/ngts/pipedev/AperturePhot/run_app_photom.sh
```

Also `casutools` needs to be on the script-runner's path
