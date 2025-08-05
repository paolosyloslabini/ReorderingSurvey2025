# Reordering Techniques

This directory contains wrapper scripts for matrix reordering algorithms. Each script follows the contract:

```bash
reordering_<technique>.sh <matrix.mtx> <output_permutation.g> [key=value ...]
```

## Available Techniques

- `identity` - Identity permutation (no reordering) for testing
- `rcm` - Reverse Cuthill-McKee bandwidth reduction  
- `ro` - Rabbit Order block-oriented reordering (requires external build)

## Wrapper Contract

Each reordering wrapper must:
1. Read a Matrix Market (.mtx) file
2. Apply the reordering algorithm 
3. Output a permutation file with 1-based indices
4. Accept optional key=value parameters
5. Exit with status 0 on success

## Installation Notes

### Rabbit Order (`ro`)

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

## Adding New Techniques

1. Create `reordering_<name>.sh` following the contract above
2. Make the script executable: `chmod +x reordering_<name>.sh`
3. Add the technique to `config/reorder.yml`
4. Update `TOOLS.md` with technique details
