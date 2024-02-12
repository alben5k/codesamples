This folder contains various scripts and tools that I've written to show examples of me using
math functions in python. 

`3d_Math_weightingByMeshVolume.py` uses the volume of a mesh to weight the vertices of another mesh. I wrote my own math functions for most operations for the purposes of the example. The theory behind its opporation is that it casts a ray from all vertices and if the ray passes through an odd number of faces that make up the volume, the vertex is inside the volume. This can sometimes break if the borders of the volume have extreme angles or the ray that is cast is parallel with a face but these are extreme outliers.

`depthmaps` is a folder containing a script to convert an image into a depth map and an obj file. It uses the transformers library and there are some functions in there to let you change the depth model.
