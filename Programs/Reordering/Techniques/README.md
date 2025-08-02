# Reordering Techniques

This directory contains wrapper scripts and installation notes for each
reordering algorithm listed in `TOOLS.md`.

## Rabbit Order (`ro`)

Rabbit Order depends on the following libraries (minimum versions taken from
the upstream project):

- g++ ≥ 4.9.2
- Boost ≥ 1.58.0
- libnuma ≥ 2.0.9
- libtcmalloc_minimal from gperftools ≥ 2.1

On clusters, load these via modules or install them in a local prefix you
control. For example:

```bash
module load gcc/9.3.0 boost/1.74 numactl/2.0.12 gperftools/2.7
```

### Build steps

1. Clone the repository into `build/rabbit_order`:

   ```bash
   git clone --depth 1 https://github.com/araij/rabbit_order.git \
       "$PROJECT_ROOT/build/rabbit_order"
   git -C "$PROJECT_ROOT/build/rabbit_order" checkout f67a79e427e2a06e72f6b528fd5464dfe8a43174
   ```
2. Compile the demo program which outputs the permutation:

   ```bash
   make -C "$PROJECT_ROOT/build/rabbit_order/demo"
   ```

The wrapper `reordering_ro.sh` expects the resulting binary at
`$PROJECT_ROOT/build/rabbit_order/demo/reorder`.
