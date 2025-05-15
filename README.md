# QGIS Window Layout Persistence
Disclaimer: This is not a well maintained repo. 
I will make it work for my own very specific context in nixos.
I am happy to entertain PRs, but will likely ignore issues without PRs, as my motivation is shamelessly selfish.

## Why?
I want QGIS to span across two screens vertically and to remember the tab and map layout.
This doesn't work (as of May 2025) natively, so together with AI llm assistents I coded up this hacky solution.

## Notes
* hardcoded titlebar height
* hardoded 0,0 position (as thats how i want it)
* only one layout #TODO consider UI for multiple layouts
* layout file is saved in ~ #TODO consider somewhere more qgis specific
* splitter size does not persist

## How to use it?

1. Install and activate
2. Set up the qgis window how you want it, and hit save layout
3. Hit Load Layout to restore the situation

# Credits 
this plugin was created using the template from:   
https://github.com/wonder-sk/qgis-minimal-plugin  🙏
