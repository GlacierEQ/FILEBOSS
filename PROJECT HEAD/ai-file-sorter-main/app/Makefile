# Detect platform
UNAME := $(shell uname | cut -d'-' -f1)

BIN_DIR := ./bin
OBJ_DIR := ./obj
SRC_DIR := ./lib
RESOURCES = resources/resources.c

ifeq ($(UNAME), Linux)
    PLATFORM := Linux
    CXXFLAGS += -DLINUX
    TARGET := $(BIN_DIR)/aifilesorter
    INSTALL_DIR := /usr/local/bin
    RESOURCE_DIR := /usr/local/share/aifilesorter
    LDFLAGS += -lcurl -ljsoncpp -lsqlite3 -lcrypto -lfmt -lspdlog -lssl
else ifeq ($(UNAME), Darwin)
    PLATFORM := MacOS
    CXXFLAGS += -DMACOS
    TARGET := $(BIN_DIR)/aifilesorter
    INSTALL_DIR := /usr/local/bin
    RESOURCE_DIR := /usr/local/share/aifilesorter
    LDFLAGS += -lcurl -ljsoncpp -lsqlite3 -lcrypto -lfmt -lspdlog -lssl
else ifeq ($(UNAME), MINGW32_NT)
    PLATFORM := Windows (32-bit)
    CXXFLAGS += -DWINDOWS
    TARGET := $(BIN_DIR)/AI\ File\ Sorter.exe
    INSTALL_DIR := C:/Program\ Files\ (x86)/AiFileSorter
    RESOURCE_DIR := C:/Program\ Files\ (x86)/AiFileSorter/resources
    WINDRES = windres
    RC_FILE = resources/exe_icon.rc
    RC_OBJ = resources/exe_icon.o
    LDFLAGS += -mwindows
else ifeq ($(UNAME), MINGW64_NT)
    PLATFORM := Windows (64-bit)
    CXXFLAGS += -DWINDOWS
    TARGET := $(BIN_DIR)/AiFileSorter.exe
    INSTALL_DIR := C:/Program\ Files/AiFileSorter
    RESOURCE_DIR := C:/Program\ Files/AiFileSorter/resources
    WINDRES = windres
    RC_FILE = resources/exe_icon.rc
    RC_OBJ = resources/exe_icon.o
    LDFLAGS += -mwindows -ljsoncpp -lcrypto -lcurl -lspdlog -lsqlite3 -lssl -lfmt
endif

# Compiler and flags
CXX = g++
CXXFLAGS += -std=c++20 -Wall $(shell pkg-config --cflags gtkmm-3.0)
LDFLAGS += $(shell pkg-config --libs gtkmm-3.0)
INCLUDE_DIRS = -I./include

# Source files
SRCS = main.cpp $(wildcard $(SRC_DIR)/*.cpp)
OBJS = $(patsubst %.cpp, $(OBJ_DIR)/%.o, $(notdir $(SRCS)))

.PHONY: all clean install uninstall

# Main rules
all: $(TARGET)
	@printf "\nFinished building AI File Sorter for %s\n" "$(PLATFORM)"

$(TARGET): $(OBJS) $(RC_OBJ)
	mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(RESOURCES) $(LDFLAGS)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	mkdir -p $(OBJ_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDE_DIRS) -c $< -o $@

$(OBJ_DIR)/main.o: main.cpp
	mkdir -p $(OBJ_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDE_DIRS) -c $< -o $@

# Windows resource compilation
ifeq ($(PLATFORM), Windows (32-bit))
$(RC_OBJ): $(RC_FILE)
	$(WINDRES) -i $< -o $@
endif

ifeq ($(PLATFORM), Windows (64-bit))
$(RC_OBJ): $(RC_FILE)
	$(WINDRES) -i $< -o $@
endif

clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR) $(RC_OBJ)

install: $(TARGET)
ifeq ($(PLATFORM), Linux)
	mkdir -p $(INSTALL_DIR)
	mkdir -p $(RESOURCE_DIR)
	cp $(TARGET) $(INSTALL_DIR)/aifilesorter
	cp -r resources/* $(RESOURCE_DIR)
else ifeq ($(PLATFORM), MacOS)
	mkdir -p $(INSTALL_DIR)
	mkdir -p $(RESOURCE_DIR)
	cp $(TARGET) $(INSTALL_DIR)/aifilesorter
	cp -r resources/* $(RESOURCE_DIR)
else ifeq ($(PLATFORM), Windows (32-bit))
	mkdir -p $(INSTALL_DIR)
	mkdir -p $(RESOURCE_DIR)
	cp $(TARGET) $(INSTALL_DIR)/aifilesorter.exe
	cp -r resources/* $(RESOURCE_DIR)
else ifeq ($(PLATFORM), Windows (64-bit))
	mkdir -p $(INSTALL_DIR)
	mkdir -p $(RESOURCE_DIR)
	cp $(TARGET) $(INSTALL_DIR)/aifilesorter.exe
	cp -r resources/* $(RESOURCE_DIR)
endif

uninstall:
	ifeq ($(PLATFORM), Linux)
		rm -f $(INSTALL_DIR)/aifilesorter
		rm -rf $(RESOURCE_DIR)
	else ifeq ($(PLATFORM), MacOS)
		rm -f $(INSTALL_DIR)/aifilesorter
		rm -rf $(RESOURCE_DIR)
	else ifeq ($(PLATFORM), Windows (32-bit))
		rm -rf $(INSTALL_DIR)
	else ifeq ($(PLATFORM), Windows (64-bit))
		rm -rf $(INSTALL_DIR)
	endif