===================
Cut, Copy and Paste
===================

LFC provides a cut/copy and paste of objects. Here is a short description what 
happens if you use it.

Cut'n Paste
===========

To cut'n paste an object just browse to it and select "Cut" from the "Actions" 
menu. You will get a message that the object is now put to the clipboard.

Now browse to the new location to which you want to paste the object and
select "Paste" from the "Actions" menu.

The object is now added to the new location and remove from the old location.
Moreover it is removed from the clipboad so that you can't move to another 
location accidently. 

Copy'n Paste
============
To copy'n paste an object just browse to it and select "Copy" from the "Actions" 
menu. You will get a message that the object is now put to the clipboard.

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

Generally
=========

* Objects can only pasted to parent objects within the object is an allowed 
  sub type. You will get a proper error message if you try it.
* Objects cannot pasted to it's own descendants. You will get a proper 
  error message if you try it.
* Objects will automatically get a unique slug within the parent object.