/**
 * cuSPARSE CSR SpMM implementation for the ReorderingSurvey2025 framework
 * Performs sparse matrix-matrix multiplication A * B = C where A is sparse CSR
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <string>
#include <cmath>
#include <stdexcept>
#include <sstream>
#include <algorithm>

#include <cuda_runtime.h>
#include <cusparse.h>

// Error checking macros
#define CHECK_CUDA(call) \
    do { \
        cudaError_t err = call; \
        if (err != cudaSuccess) { \
            std::cerr << "CUDA error at " << __FILE__ << ":" << __LINE__ << " - " << cudaGetErrorString(err) << std::endl; \
            exit(1); \
        } \
    } while(0)

#define CHECK_CUSPARSE(call) \
    do { \
        cusparseStatus_t err = call; \
        if (err != CUSPARSE_STATUS_SUCCESS) { \
            std::cerr << "cuSPARSE error at " << __FILE__ << ":" << __LINE__ << " - " << err << std::endl; \
            exit(1); \
        } \
    } while(0)

struct MatrixMarketHeader {
    int rows, cols, nnz;
    bool is_symmetric;
};

// Parse Matrix Market header
MatrixMarketHeader parseMatrixMarketHeader(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open matrix file: " + filename);
    }

    std::string line;
    MatrixMarketHeader header;
    header.is_symmetric = false;

    // Read header line
    std::getline(file, line);
    if (line.find("%%MatrixMarket") != 0) {
        throw std::runtime_error("Invalid Matrix Market format");
    }
    if (line.find("symmetric") != std::string::npos) {
        header.is_symmetric = true;
    }

    // Skip comments
    while (std::getline(file, line) && line[0] == '%');

    // Read dimensions
    std::istringstream iss(line);
    iss >> header.rows >> header.cols >> header.nnz;

    return header;
}

// Load CSR matrix from Matrix Market format
void loadMatrixMarket(const std::string& filename, 
                     std::vector<int>& rowPtr, 
                     std::vector<int>& colIdx, 
                     std::vector<double>& values) {
    
    MatrixMarketHeader header = parseMatrixMarketHeader(filename);
    
    std::ifstream file(filename);
    std::string line;
    
    // Skip to data
    while (std::getline(file, line) && line[0] == '%');
    std::getline(file, line); // Skip dimension line
    
    // Read coordinate format
    std::vector<std::vector<std::pair<int, double>>> rows(header.rows);
    
    int row, col;
    double val;
    for (int i = 0; i < header.nnz; ++i) {
        file >> row >> col >> val;
        rows[row-1].push_back({col-1, val}); // Convert to 0-based indexing
        
        // Handle symmetric matrices
        if (header.is_symmetric && row != col) {
            rows[col-1].push_back({row-1, val});
        }
    }
    
    // Convert to CSR format
    rowPtr.resize(header.rows + 1);
    rowPtr[0] = 0;
    
    for (int i = 0; i < header.rows; ++i) {
        // Sort columns in each row
        std::sort(rows[i].begin(), rows[i].end());
        
        for (const auto& entry : rows[i]) {
            colIdx.push_back(entry.first);
            values.push_back(entry.second);
        }
        rowPtr[i + 1] = colIdx.size();
    }
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <matrix.mtx> <output_file> [alpha] [beta] [num_cols_B]" << std::endl;
        return 1;
    }

    std::string matrix_file = argv[1];
    std::string output_file = argv[2];
    double alpha = (argc > 3) ? std::stod(argv[3]) : 1.0;
    double beta = (argc > 4) ? std::stod(argv[4]) : 0.0;
    int num_cols_B = (argc > 5) ? std::stoi(argv[5]) : 64; // Default dense matrix B with 64 columns

    try {
        // Load matrix A from file
        std::vector<int> h_rowPtr, h_colIdx;
        std::vector<double> h_values;
        loadMatrixMarket(matrix_file, h_rowPtr, h_colIdx, h_values);

        int num_rows_A = h_rowPtr.size() - 1;
        int num_cols_A = *std::max_element(h_colIdx.begin(), h_colIdx.end()) + 1;
        int nnz_A = h_values.size();

        std::cout << "Matrix A: " << num_rows_A << "x" << num_cols_A << " with " << nnz_A << " non-zeros" << std::endl;

        // Initialize cuSPARSE
        cusparseHandle_t handle;
        CHECK_CUSPARSE(cusparseCreate(&handle));

        // Allocate device memory for matrix A (CSR)
        int *d_rowPtr, *d_colIdx;
        double *d_values;
        CHECK_CUDA(cudaMalloc(&d_rowPtr, (num_rows_A + 1) * sizeof(int)));
        CHECK_CUDA(cudaMalloc(&d_colIdx, nnz_A * sizeof(int)));
        CHECK_CUDA(cudaMalloc(&d_values, nnz_A * sizeof(double)));

        CHECK_CUDA(cudaMemcpy(d_rowPtr, h_rowPtr.data(), (num_rows_A + 1) * sizeof(int), cudaMemcpyHostToDevice));
        CHECK_CUDA(cudaMemcpy(d_colIdx, h_colIdx.data(), nnz_A * sizeof(int), cudaMemcpyHostToDevice));
        CHECK_CUDA(cudaMemcpy(d_values, h_values.data(), nnz_A * sizeof(double), cudaMemcpyHostToDevice));

        // Create sparse matrix A
        cusparseSpMatDescr_t matA;
        CHECK_CUSPARSE(cusparseCreateCsr(&matA, num_rows_A, num_cols_A, nnz_A,
                                        d_rowPtr, d_colIdx, d_values,
                                        CUSPARSE_INDEX_32I, CUSPARSE_INDEX_32I,
                                        CUSPARSE_INDEX_BASE_ZERO, CUDA_R_64F));

        // Create dense matrix B (random values)
        double *d_B, *d_C;
        CHECK_CUDA(cudaMalloc(&d_B, num_cols_A * num_cols_B * sizeof(double)));
        CHECK_CUDA(cudaMalloc(&d_C, num_rows_A * num_cols_B * sizeof(double)));

        // Initialize B with random values on GPU - using simple constant for reproducibility
        std::vector<double> h_B(num_cols_A * num_cols_B, 1.0);
        CHECK_CUDA(cudaMemcpy(d_B, h_B.data(), num_cols_A * num_cols_B * sizeof(double), cudaMemcpyHostToDevice));

        // Create dense matrices B and C
        cusparseDnMatDescr_t matB, matC;
        CHECK_CUSPARSE(cusparseCreateDnMat(&matB, num_cols_A, num_cols_B, num_cols_A, d_B, CUDA_R_64F, CUSPARSE_ORDER_COL));
        CHECK_CUSPARSE(cusparseCreateDnMat(&matC, num_rows_A, num_cols_B, num_rows_A, d_C, CUDA_R_64F, CUSPARSE_ORDER_COL));

        // Allocate workspace
        size_t bufferSize;
        CHECK_CUSPARSE(cusparseSpMM_bufferSize(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, CUSPARSE_OPERATION_NON_TRANSPOSE,
                                              &alpha, matA, matB, &beta, matC, CUDA_R_64F, CUSPARSE_SPMM_ALG_DEFAULT, &bufferSize));

        void *d_buffer;
        CHECK_CUDA(cudaMalloc(&d_buffer, bufferSize));

        // Warm-up run
        CHECK_CUSPARSE(cusparseSpMM(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, CUSPARSE_OPERATION_NON_TRANSPOSE,
                                   &alpha, matA, matB, &beta, matC, CUDA_R_64F, CUSPARSE_SPMM_ALG_DEFAULT, d_buffer));
        CHECK_CUDA(cudaDeviceSynchronize());

        // Timing runs
        const int num_trials = 10;
        auto start = std::chrono::high_resolution_clock::now();

        for (int trial = 0; trial < num_trials; ++trial) {
            CHECK_CUSPARSE(cusparseSpMM(handle, CUSPARSE_OPERATION_NON_TRANSPOSE, CUSPARSE_OPERATION_NON_TRANSPOSE,
                                       &alpha, matA, matB, &beta, matC, CUDA_R_64F, CUSPARSE_SPMM_ALG_DEFAULT, d_buffer));
        }
        CHECK_CUDA(cudaDeviceSynchronize());

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double avg_time_ms = duration.count() / (1000.0 * num_trials);

        // Calculate GFLOPS (2 * nnz * num_cols_B for SpMM)
        double gflops = (2.0 * nnz_A * num_cols_B) / (avg_time_ms * 1e6);

        // Write results
        std::ofstream outfile(output_file);
        outfile << "avg_time_ms," << avg_time_ms << std::endl;
        outfile << "gflops," << gflops << std::endl;
        outfile << "nnz," << nnz_A << std::endl;
        outfile << "num_rows," << num_rows_A << std::endl;
        outfile << "num_cols," << num_cols_A << std::endl;
        outfile << "num_cols_B," << num_cols_B << std::endl;
        outfile.close();

        std::cout << "Average time: " << avg_time_ms << " ms" << std::endl;
        std::cout << "Performance: " << gflops << " GFLOPS" << std::endl;

        // Cleanup
        cusparseDestroySpMat(matA);
        cusparseDestroyDnMat(matB);
        cusparseDestroyDnMat(matC);
        cusparseDestroy(handle);

        cudaFree(d_rowPtr);
        cudaFree(d_colIdx);
        cudaFree(d_values);
        cudaFree(d_B);
        cudaFree(d_C);
        cudaFree(d_buffer);

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}