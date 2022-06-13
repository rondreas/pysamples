# View 3D Overlay

This Python Package defines a helper class for getting and storing information from a camera item `camera_info.py`, and a Modo Package we can attach to cameras in Modo which will draw extra information to screen when looking through the camera we've added the Modo Package to.

To test this, create a camera item and with it selected. Run the command 
``` 
item.addPackage py.safeAreaOverlay
```

## Instance

## Package

## Channel UI

In our Package class we also implement the `lxifc.ChannelUI` interface which we can use to enable or disable channels. This will allow us to hide channels from forms.

## Config

TODO: document config file filterPreset, how we can use ShowWhenDisable