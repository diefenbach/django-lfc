===================
Cut, Copy and Paste
===================

LFC provides Cut/Copy and Paste of objects. Here is a short description on how
to use it.

Cut and Paste
=============

To Cut'n Paste an object just browse to it and select "Cut" from the "Actions" 
menu. The object is now put to the clipboard and ready to paste.

Now browse to the new location to which you want to paste the object and
select "Paste" from the "Actions" menu

The object is now added to the new and remove from the old location. Moreover 
it is removed from the clipboad so that you cannot move it to another location 
accidently.

Copy and Paste
==============
To Copy'n Paste an object just browse to it and select "Copy" from the "Actions" 
menu. The object is now put to the clipboard and ready to paste.

Now browse to the new location to which you want to paste the object and 
select "Paste" from the "Actions" menu.

The object is now added to the new location. Please note that it is not removed
from the old location (as you expected). It is also not removed from the 
clipboad so that you can repeately paste the object to the same or different
locations. 

If you copy an object following related objects are also copied:

* Children
* Images
* Files
* Translations
* Portlets

Miscellaneous
=============

* Objects can only pasted to parent objects within the object is an allowed 
  sub type. You will get a proper error message if you try it.
* Objects cannot pasted to it's own descendants. You will get a proper 
  error message if you try it.
* Objects will automatically get a unique slug within the parent object.