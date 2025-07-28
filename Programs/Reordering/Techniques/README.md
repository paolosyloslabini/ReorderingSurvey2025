# Reordering Techniques

This directory contains wrapper scripts and installation notes for each
reordering algorithm listed in `TOOLS.md`.

## Rabbit Order (`ro`)

The Rabbit Order sources are retrieved during the bootstrap stage. Ensure `gcc`,
`boost`, `libnuma`, and `google-perftools` are installed on your system.

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
