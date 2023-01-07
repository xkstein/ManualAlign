# Manual Align

This is a tool for manually aligning two images from 2-5 selected points

---

# Installation

Start by cloning this repo, either by just downloading it here or by running (in your shell):

```bash
git clone https://github.com/xkstein/ManualAlign/
```

I recommend installing the required python packages in a python virtual environment (learn more about them [here](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)), to set this up go into the downloaded folder and run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This makes a virtual environment in this folder (under `venv/`), sources it (meaning that you're now using the virtual environment), and installs the required python packages to that virtual environment.

Now just run

```
python align.py
```

to open the application!

---

# Usage

This program aligns an input image to a reference image. To do this,
1. Load both an image and a reference image (commands can be found under `File` in the toolbar)
2. Select 2-5 mutual points between them
3. Align them by selecting the `Align` option under `Edit` in the toolbar. 

The resulting image can either be cropped and exported (using the red square) or exported in full by selecting `Save Cropped Aligned Image` or `Save Aligned Image`.[^2]

## Controls
| Input | Command |
| ----- | ------- | 
| `DOUBLE CLICK` | Select point |
| `#1-5`         | Select marker index |
| `h`            | "Home" the selected image |
| `Backspace`    | Deletes current selected point |

**NOTE**: This list isn't comprehensive, there are other actions and keybinds which can be found in the file and edit menu items

## Functions

Found under `Edit` in the toolbar:
- `Autosave Points` (Toggle) - If set, csv points are automatically saved when an image is saved.
- `Lock ROI` (Toggle) - Immobilizes the ROI (the red square which is used for cropping)

---

# Configuration
> You can set all of the image path things through the gui's toolbar now, which is kinda nice, or you can do it through the code if that's your thing

`TRACE_PATH` - Path to the traced image

`TRACE_PATH_SAVE` - Path to the location where you wanna save the aligned traced image

`RAW_PATH` - Path to the location of the raw image (that you're aligning to the tracing)

`RAW_PATH_SAVE` - Where you want to save the aligned raw image[^1]

`PTS_CSV_READ` - Where to read the alignment points from

`PTS_CSV_SAVE` - Where to save alignment points[^1]


[^1]: **NOTE**: if you change the raw image, you also will need to set where to save points and where to save the aligned image

---

## To Do:
- Change from qt imsave backend (to suppress FutureWarning) <= the other options where very slow on my machine so this will take some investigating
- Just better cropping code (in ImagePlot, already TODOed)
---

**Credit** to [this](https://stackoverflow.com/a/69878947/17338565) stack overflow post for helping in a major way.

[^2]: **NOTE**: your cropping is relative to the reference image, and it is saved and loaded with the csv points.
