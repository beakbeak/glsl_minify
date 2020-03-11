# glsl_minify

glsl_minify reduces the size of GLSL code by collapsing or eliminating
whitespace and replacing identifiers starting with a prefix (`'_'` by default)
with generated names.

It can be used from the command line or imported as a Python module.

## Command line help

    $ python glsl_minify.py -h

    usage: glsl_minify.py [-h] [--copy] [-q] [-i INDIR] -o OUTDIR
                          [filename [filename ...]]

    positional arguments:
      filename              file path relative to INDIR. If unspecified, all .glsl
                            files reachable from INDIR will be processed

    optional arguments:
      -h, --help            show this help message and exit
      --copy                copy files without minifying
      -q, --quiet           disable status messages
      -i INDIR, --indir INDIR
                            path containing source glsl files (default: .)
      -o OUTDIR, --outdir OUTDIR
                            where to store output files
