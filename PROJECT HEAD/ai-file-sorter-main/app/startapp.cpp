#include <iostream>
#include <cstdlib>
#include <shlobj.h>
#include <string>
#include <windows.h>


std::string getExecutableDirectory() {
    WCHAR buffer[MAX_PATH];
    GetModuleFileNameW(NULL, buffer, MAX_PATH);
    std::wstring wpath(buffer);
    size_t pos = wpath.find_last_of(L"\\/");
    std::wstring dir = wpath.substr(0, pos);
    return std::string(dir.begin(), dir.end());
}


void addToPath(const std::string& directory) {
    char* pathEnv = nullptr;
    size_t requiredSize = 0;

    getenv_s(&requiredSize, nullptr, 0, "PATH");
    if (requiredSize == 0) {
        std::cerr << "Failed to retrieve PATH environment variable." << std::endl;
        return;
    }

    pathEnv = new char[requiredSize];
    getenv_s(&requiredSize, pathEnv, requiredSize, "PATH");

    std::string newPath = std::string(pathEnv) + ";" + directory;
    delete[] pathEnv;

    // Update PATH in the current process
    if (_putenv_s("PATH", newPath.c_str()) != 0) {
        std::cerr << "Failed to set PATH environment variable." << std::endl;
    } else {
        std::cout << "Updated PATH: " << newPath << std::endl;
    }
}


void launchMainApp() {
    std::string exePath = "bin\\AI File Sorter.exe";
    if (WinExec(exePath.c_str(), SW_SHOW) < 32) {
        std::cerr << "Failed to launch the application." << std::endl;
    }
}


int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
                   LPSTR lpCmdLine, int nCmdShow) {
    std::string exeDir = getExecutableDirectory();

    if (!SetCurrentDirectoryA(exeDir.c_str())) {
        std::cerr << "Failed to set current directory: " << exeDir << std::endl;
        return EXIT_FAILURE;
    }

    std::string dllPath = exeDir + "\\lib";
    addToPath(dllPath);
    launchMainApp();
    return EXIT_SUCCESS;
}