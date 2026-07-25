A simple application to display a selection of avatars in rotation.

On first use, the selection process is invoked. UP/DOWN ("A","D") cycle through 
available avatars; CONFIRM ("C") enables/disables the currently shown avatar 
(enablement being clearly indicated by a tick icon); BACK ("E") enters display 
mode. In subsequent invocations, the display cycle starts immediately. To 
re-enter selection mode use CONFIRM ("C") again.  To exit, from display mode use 
EXIT ("E"), then CONFIRM ("C").

At the moment, avatar images need to be uploaded using the mpremote tool, although 
a starter selection are provided.  Images should be 240x240 pixels, and placed in 
:apps/camopants_tildagon_display_avatar/assets/avatars/

    mpremote cp <file> :apps/camopants_tildagon_display_avatar/assets/avatars/

To delete an unwanted avatar:

    mpremote fs ls :apps/camopants_tildagon_display_avatar/assets/avatars/
    mpremote fs rm :apps/camopants_tildagon_display_avatar/assets/avatars/<file>

TODO:
Differentiate between selection and display states.
