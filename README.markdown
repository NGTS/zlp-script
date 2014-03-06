NGTS Zero Level Pipeline Input Catalogue Generator
==================================================

`ngts_catalogue`

The Zero Level Pipeline Input Catalogue Generator (ZLPICG) for the NGTS project

*NGTS-ZLPICG* - catchy eh?

Development
-----------

To help develop this code, preferably inside a virtualenv: run

``` python
python setup.py develop
```

This will effectively create symlinks to the package contents to allow development without installing properly after each change.

To uninstall, run

``` python
python setup.py develop --uninstall
```

The python scripts to run the code will be updated during development.

Installation
------------

To install, run `python setup.py install` or to install directly from git:

```
python setup.py install git+https://github.com/NGTS/zlp-input-catalogue.git
```
