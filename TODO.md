# TODO

## Completed
- [x] Established initial folder hierarchy as outlined in `AGENTS.md`.
- [x] Added README files describing the purpose of each directory.
- [x] Created placeholders for `exp_config.sh`, helper scripts, and YAML configuration files.
- [x] Developed the Slurm driver scripts for both pipeline phases.
- [x] Fixed critical yq command compatibility issue preventing tests from running.
- [x] Fixed shellcheck warnings in bash scripts.
- [x] Added `reordering_identity.sh` wrapper that outputs the identity permutation.
- [x] Created mock `operation_mock.sh` and `operation_cucsrspmm.sh` multiplication wrappers.
- [x] Enhanced YAML config files with realistic parameter sets.
- [x] Fixed filename typo: Job_sumbmit_sample.txt → Job_submit_sample.txt.
- [x] Added proper .gitignore for Python cache files and build artifacts.

## Next Steps
1. **Implement remaining reordering techniques**: Add wrappers for `rcm`, `amd`, `nd`, `mgp`, etc. listed in `TOOLS.md`.
2. **Complete multiplication kernel implementations**: Add real cuSPARSE, MKL, and other kernel wrappers.
3. **Enhance `scripts/csv_helper.py`**: Verify and improve structural metrics calculation.
4. **Add comprehensive documentation**: 
   - Update README.md with installation and usage instructions
   - Complete individual README files in subdirectories
   - Add examples of running the pipeline
5. **Create additional tests**: Add tests for reordering techniques and end-to-end pipeline.
6. **Implement bootstrap process**: Complete `scripts/bootstrap.sh` to fetch and build external dependencies.
7. **Add error handling**: Improve robustness of pipeline scripts with better error messages.
8. **Performance optimization**: Profile and optimize for large-scale matrix processing.

