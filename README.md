<div style="margin: 0; padding: 0; text-align: center; border: none;">
<a href="https://quantlet.com" target="_blank" style="text-decoration: none; border: none;">
<img src="https://github.com/StefanGam/test-repo/blob/main/quantlet_design.png?raw=true" alt="Header Image" width="100%" style="margin: 0; padding: 0; display: block; border: none;" />
</a>
</div>

```
Name of QuantLet: IDA Team

Published in: Institute for Digital Assets (IDA)

Description: Generates an animated transparent GIF in which the flags of 16 countries (Germany, Romania, Taiwan, Russia, United Kingdom, Poland, Switzerland, China, Tunisia, Macau, Hong Kong, Croatia, Portugal, Czech Republic, France, India) rotate on a flat circular orbit around the Bucharest University of Economic Studies (ASE) logo. Each flag is placed in a uniform bounding box with its native aspect ratio preserved (no stretching). Flag extraction from a single composite grid PNG uses column- and row-gap detection plus a smart-crop step that preserves dark stripes such as the black band of the German flag, while a logo-flattening step ensures crisp rendering inside the GIF palette. All visual parameters (canvas size, logo size, flag bounding box, orbit radius, frame count, frame duration, rotation direction) are exposed as knobs at the top of the script.

Keywords: animated GIF, transparent background, flags, rotation, orbit, ASE Bucharest, IDA, Pillow, image processing, palette quantization, smart crop

Author: Daniel Traian Pele

Submitted: Sunday, 17 May 2026

Input: flags_grid.png, ase_logo.png

Output: ase_flags_rotation_slow.gif

```
<div align="center">
<img src="https://raw.githubusercontent.com/QuantLet/IDA_Team/main/ase_flags_rotation.gif" alt="Image" />
</div>

<div align="center">
<img src="https://raw.githubusercontent.com/QuantLet/IDA_Team/main/ase_logo.png" alt="Image" />
</div>

<div align="center">
<img src="https://raw.githubusercontent.com/QuantLet/IDA_Team/main/flags_grid.png" alt="Image" />
</div>

