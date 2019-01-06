# PanicPanda - A 3D rendering demo powered by Python and Vulkan

![A helmet renderer by panic panda](/demo.png "Image")  

## About

Codename "PanicPanda" is a 3D rendering tech demo that use Vulkan as its rendering API and python as its programming language.

The main purpose of this project was to create an environment that is both simple to reason with and lightning fast to debug in order to quickly prototype a wide variety of 3D applications. Speed and effiency was never a goal for this project, and while PanicPanda doesn't do anything particularly wrong, it doesn't do anything particularly right either.

In its current state, PanicPanda could be considered an framework embryo. You are free to take inspiration from it, but building another project around it would be foolish.

See the "Documentation" section for a more detailed information on how everything works together.

## Dependencies

* Python >= 3.6
* The project compiled assets TODO LINK
* [Optional] PyQt5 https://pypi.org/project/PyQt5/
* [Optional] The LunargG Vulkan SDK https://www.lunarg.com/vulkan-sdk/
* [Optional] Compressonator https://github.com/GPUOpen-Tools/Compressonator
* [Optional] envtools https://github.com/cedricpinson/envtools

If PyQt5 is installed, there will be a debugging UI available to edit the project values at runtime.

The LunarG SDK is a must for debugging Vulkan applications. It also includes tools to compile the shaders yourself.

Compressonator is used to compress the textures.

envtools is required to compile the environment maps.

## Starting the application

On Windows

TODO: include binary link

On Linux

```sh
git clone git@github.com:gabdube/panic-panda
cd panic-panda

# TODO download compiled assets link

# Running without '-O' enable the debbuging utilities
# and use lower quality assets for quicker load times
python -O src  
```

## Commands & Controls

The demo includes demo 3 scenes, accessible by pressing the key `2`, `3` and `4` (not the ones on the notepad)

* Scene `4` (the default), is a PBR demo. Use the mouse to move the model around and the `UP` and `DOWN` arrow keys to check out the different stages.

* Scene `3` was used to debug a normals problem. It's kind of nice to look at so I left it here

* Scene `2` is used for texture debugging. It includes normal textures, raw textures, array textures and mipmapped cubemaps. You can iterator over them with the array keys.

* Scene `1`. Is an empty scene.

## Documentation

TODO

## Attributions

* Approching storm HDRI by Greg Zaal, published under CC0
  * https://hdrihaven.com/hdri/?h=approaching_storm
  * https://hdrihaven.com/

* Battle Damaged Sci-fi Helmet - PBR by theblueturtle_, published under a Creative Commons Attribution-NonCommercial license
  * https://sketchfab.com/models/b81008d513954189a063ff901f7abfe4
  * https://sketchfab.com/theblueturtle_
