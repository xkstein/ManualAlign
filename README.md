---

# Controls

| Input | Command |
| ----- | ------- | 
| `DOUBLE CLICK` | Select point |
| `#1-5`         | Select marker index[^1] |
| `h`            | "Home" the selected image |

**NOTE**: This list isn't comprehensive, there are other actions and keybinds which can be found in the file and edit menu items

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

---

## To Do:
- Change from qt imsave backend (to suppress FutureWarning) <= the other options where very slow on my machine so this will take some investigating
- Just better cropping code (in ImagePlot, already TODOed)

