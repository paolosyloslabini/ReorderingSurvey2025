# TODO

## Completed
- Established initial folder hierarchy as outlined in `AGENTS.md`.
- Added README files describing the purpose of each directory.
- Created placeholders for `exp_config.sh`, helper scripts, and YAML configuration files.

## Next Steps
1. Implement wrapper scripts for each reordering technique and multiplication kernel listed in `TOOLS.md`.
2. Flesh out `exp_config.sh` with module loads and environment setup.
3. Populate `config/reorder.yml` and `config/multiply.yml` with real parameter sets.
4. Develop the Slurm driver scripts for both pipeline phases.
5. Write code in `scripts/csv_helper.py` to merge structural metrics into the results CSVs.
6. Add documentation on how to run the bootstrap process and execute the pipeline.
7. Add an `reordering_identity.sh` wrapper that outputs the identity permutation and writes a minimal `results.csv` for local tests.
8. Create an `operation_mock.sh` multiplication wrapper that emits fake timing metrics while matching the results CSV schema.
9. Register these mock techniques in the YAML config files and mention them in the documentation for local runs.

