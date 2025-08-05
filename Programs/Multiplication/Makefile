# Makefile for cuSPARSE multiplication implementation
# Requires CUDA toolkit and cuSPARSE library

NVCC = nvcc
CUDA_ARCH = -arch=sm_60 -arch=sm_70 -arch=sm_80
CXXFLAGS = -O3 -std=c++14 -Xcompiler -fPIC
LIBS = -lcusparse -lcudart

# Try to find CUDA installation
CUDA_PATH ?= /usr/local/cuda
ifneq ($(wildcard $(CUDA_PATH)/include/cuda_runtime.h),)
    INCLUDES = -I$(CUDA_PATH)/include
    LIBDIRS = -L$(CUDA_PATH)/lib64
else
    # Fallback for system installation
    INCLUDES = 
    LIBDIRS = 
endif

TARGET = cusparse_spmm
SOURCE = cusparse_spmm.cu

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(NVCC) $(CUDA_ARCH) $(CXXFLAGS) $(INCLUDES) $(LIBDIRS) -o $@ $< $(LIBS)

clean:
	rm -f $(TARGET)

# Test target to verify compilation environment
test-env:
	@echo "Testing CUDA environment..."
	@which nvcc || echo "NVCC not found - please load CUDA module"
	@nvcc --version || echo "NVCC not working"
	@echo "CUDA_PATH: $(CUDA_PATH)"