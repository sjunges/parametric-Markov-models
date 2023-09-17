Parametric Markov Model Benchmark Suite
=======================================

[![DOI](https://zenodo.org/badge/689586831.svg)](https://zenodo.org/badge/latestdoi/689586831)

This suite contains a set of benchmarks and a simple runner script that can be used to run these benchmarks. 

Benchmarks
-----------
This benchmark set is maintained by Sebastian Junges and hosted at github.com/sjunges/parametric-markov-benchmarks.
To add or update benchmarks, please use the issues/pull-request feature.

### Benchmark files

This benchmark set contains a collection of scalable parametric benchmarks from various sources. The benchmarks are available as PRISM or JANI files. Each benchmark set contains a README with the original sources.

### Other Benchmarks

#### POMDPs
A rich source for additional pMC benchmarks with many parameters is by considering FSCs for POMDPs [1].
Notice that this translation comes with various options and variations that yields significantly different pMCs.

To obtain such pMCs, one may take POMDPs, e.g., those found in https://github.com/moves-rwth/pomdp-collection/ and use Storm to translate them into an (explicitly represented) pMC, which can be exported in (explicit) textual formats.

#### Bayesian Nets
Recent work by Salmani and Katoen applies parameter synthesis on Bayesian networks. Various (incompatible) file formats can be translated to an explicit pMC, see e.g., https://github.com/BaharSlmn/pbn-epsilon-tuning/blob/main/IJCAI2023-Experiments/run-experiments.cpp

### Other collections
- The git by Jip Spel maintains a large set of parametric models: https://github.com/jipspel/benchmarks/
- An original benchmark set is maintained at https://depend.cs.uni-saarland.de/tools/param/casestudies/

Benchmark Runner
-----------------
The benchmark runner has been last tested with Storm as presented here: https://github.com/moves-rwth/storm/pull/360.

To run it,
```
python benchmark-runner.py PATH_TO_STORM_BINARY_DIR/storm-pars
```