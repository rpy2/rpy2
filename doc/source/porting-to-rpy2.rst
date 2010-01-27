Porting code to rpy2
====================


From R
------

From rpy
--------

From rpy2-2.0.x
---------------

The camelCase naming disappeared from variables and methods, as it seemed
to be mostly absent from such obejcts in the standard library
(although nothing specific appears about that in :pep:`8`).

Practically, this means that `globalEnv` became `globalenv`, `baseEnv` became `baseenv`, etc...

