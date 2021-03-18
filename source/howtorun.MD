from above the Distrib-ToyChord directory run the following
```
export FLASK_APP=Distrib-ToyChord/source/
export FLASK_ENV=development
export MODE_CONFIG=normal or boot
export SET_PORT=.... (optional, if not used load from appropriate config file (subject to mode_config))
flask run [--host 0.0.0.0 (externally visible) --port whatever (for selecting port)]
```
