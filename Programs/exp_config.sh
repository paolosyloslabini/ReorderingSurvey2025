# Cluster-wide environment and path definitions
# Define where raw matrices and results are stored. These can point
# outside the repository if the datasets or outputs are large.

# Absolute path to the repository root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROJECT_ROOT

# Location of original matrix files (may reside on shared storage)
export RAW_MATRIX_DIR="${RAW_MATRIX_DIR:-$PROJECT_ROOT/Raw_Matrices}"

# Location where experiment outputs are written
export RESULTS_DIR="${RESULTS_DIR:-$PROJECT_ROOT/Results}"

# TODO: add module load commands and other environment variables

