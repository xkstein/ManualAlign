## To Do:
- Change from qt imsave backend, for some reason it's very slow
- Add support for removing anchors
- Move locking ROI to toolbar
- Move aligning to toolbar
- Universal pointer selection (like I can press 2 anywhere in the application and it changes the selector to 2)
- Just better cropping code (in ImagePlot, already TODOed)

### Maybe Do:
- Add a separate window for managing all of the filenames

---
# Controls
| Input | Command |
| ----- | ------- | 
| `DOUBLE CLICK` | Select point |
| `#1-5`         | Select marker index[^1] |
| `CMD-l`        | Load points (reads from `PTS_CSV_READ`) |
| `CMD-p`        | Save current point (saved to `PTS_CSV_SAVE`) |
| `a`            | Compile and align images with selected points |
| `CMD-o`        | Open a new raw image to edit[^2] |
| `CMD-s`        | Save roi of aligned images |
| `m`            | Toggles movablility of roi (the little red square that shows up in the third window) |

[^1]: **NOTE**: you have to left-click on the plot that you want to make this change in each time, its sort of an unfortunate thing, deciding on how to fix it
[^2]: **NOTE**: if you change the raw image, you also will need to set where to save points and where to save the aligned image

---

# Configuration
> You can set all of the image path things through the gui's toolbar now, which is kinda nice, or you can do it through the code if that's your thing

`TRACE_PATH` - Path to the traced image

`TRACE_PATH_SAVE` - Path to the location where you wanna save the aligned traced image

`RAW_PATH` - Path to the location of the raw image (that you're aligning to the tracing)

`RAW_PATH_SAVE` - Where you want to save the aligned raw image

`PTS_CSV_READ` - Where to read the alignment points from

`PTS_CSV_SAVE` - Where to save alignment points

---

# Workflow
There are basically two modes to this application (if you're aliging a set of images to one tracing that you want to all line up): 
1. Aligning an image AND its tracing
2. Aligning an image TO its tracing. 

In 1 you need to change/set the region of the crop, but in mode 2 you don't want to touch the crop (so your images align)[^3]. If you're aligning a set of images to one tracing and you want them all to line up (like if you're doing some n-channel image process), you should only select the points on the tracing once. So after you align the first image, you should save those points and then load those when you align the next image (if you press `o`, you can open the next image)

---

**Credit** to [this](https://stackoverflow.com/a/69878947/17338565) stack overflow post for helping in a major way.

[^3]: Side note, your cropping is based off the hand tracing, and it is saved and loaded with the csv points.

